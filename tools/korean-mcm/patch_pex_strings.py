"""Replace only string-table entries in the upstream CHIM Lite 2.3.3 MCM PEX.

The installed Papyrus compiler source set is incomplete/incompatible with this
MCM, so preserve the shipped bytecode and its string indices exactly.
"""

import argparse
from hashlib import sha256
from pathlib import Path
from build_korean_mcm import LABELS

EXPECTED_SHA256 = "18fa4432e23038190f0bfbd38b47f0006aed407734a516132ac20d41e63994df"

EXTRA = {
    "Remove AI agent '": "선택한 NPC '",
    "Add AI agent '": "선택한 NPC '",
    "'?": "'의 설정을 변경할까요?",
    "Remove the AI agent '": "AI 에이전트 '",
    "' from the active AI system.": "'을(를) 활성 AI 시스템에서 제거합니다.",
    "Add the nearby NPC '": "근처 NPC '",
    "' to the AI system.": "'을(를) AI 시스템에 추가합니다.",
    "This key is already mapped to:\n'": "이 키는 이미 다음 기능에 지정되어 있습니다:\n'",
    ")\n\nAre you sure you want to continue?": ")\n\n계속할까요?",
    "'\n\nAre you sure you want to continue?": "'\n\n계속할까요?",
}


def read_u16(data: bytes, offset: int) -> tuple[int, int]:
    if offset + 2 > len(data):
        raise ValueError("Truncated PEX")
    return int.from_bytes(data[offset : offset + 2], "big"), offset + 2


def parse_table(data: bytes) -> tuple[int, int, list[str]]:
    if data[:4] != bytes.fromhex("fa57c0de"):
        raise ValueError("Unexpected PEX magic")
    offset = 16
    for _ in range(3):  # source filename, compiler user, compiler machine
        length, offset = read_u16(data, offset)
        offset += length
    table_start = offset
    count, offset = read_u16(data, offset)
    strings = []
    for _ in range(count):
        length, offset = read_u16(data, offset)
        strings.append(data[offset : offset + length].decode("utf-8"))
        offset += length
    return table_start, offset, strings


def main() -> None:
    ap = argparse.ArgumentParser(description="Usage: python patch_pex_strings.py <CHIM Lite 2.3.3 Scripts/AIAgentMCMConfigScript.pex> <output.pex>")
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    SOURCE, OUTPUT = args.source, args.output
    original = SOURCE.read_bytes()
    if sha256(original).hexdigest() != EXPECTED_SHA256:
        raise ValueError("Upstream PEX changed; review strings and indices before patching")
    start, end, strings = parse_table(original)
    changes = LABELS | EXTRA
    unknown = set(changes) - set(strings)
    if unknown:
        raise ValueError(f"Translations absent from upstream PEX: {sorted(unknown)}")
    translated = [changes.get(s, s) for s in strings]
    if len(translated) != len(strings):
        raise ValueError("PEX string count changed")
    table = bytearray(len(strings).to_bytes(2, "big"))
    for s in translated:
        encoded = s.encode("utf-8")
        if len(encoded) > 65535:
            raise ValueError("PEX string too long")
        table.extend(len(encoded).to_bytes(2, "big"))
        table.extend(encoded)
    result = original[:start] + table + original[end:]
    _, tail_start, check = parse_table(result)
    if check != translated or result[tail_start:] != original[end:]:
        raise ValueError("PEX verification failed")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(result)
    print(f"Patched {sum(a != b for a, b in zip(strings, translated))} string-table entries: {OUTPUT}")


if __name__ == "__main__":
    main()
