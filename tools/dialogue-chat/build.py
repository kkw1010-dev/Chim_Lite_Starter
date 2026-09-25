"""Build "CHIM Lite - Dialogue Chat": compile the Papyrus scripts, generate the ESP
and SEQ, and optionally copy everything into an MO2 mod folder.

Every step fails loudly: a compile error, a generator read-back mismatch, or an
installed file that differs from the build output stops the build.

Usage:
  python build.py --compiler "<...>/PapyrusCompiler.exe" \
                  --import "<vanilla + TESV_Papyrus_Flags.flg folder>" \
                  --import "<SKSE Scripts/Source>" --import "<PapyrusUtil Scripts/Source>" \
                  [--install "<MO2>/mods/CHIM Lite - Dialogue Chat"]

The vanilla source folder must be last and must contain TESV_Papyrus_Flags.flg.
CHIM Lite's own .psc sources are NOT needed: Scripts/Stubs declares the few CHIM
functions these scripts call (compile-only, never shipped).
"""

import argparse
import filecmp
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = "CHIM Lite - Dialogue Chat.esp"
SCRIPTS = ["TKLChimChatController", "TKLChimChatPlayerAlias",
           "TKLChimChatTalkFragment", "TKLChimChatEndFragment"]


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        sys.exit(f"FAILED: {' '.join(map(str, cmd))}\n{r.stdout}\n{r.stderr}")
    return r.stdout


def scrub_pex_identity(path):
    """Replace the Windows user and computer name PapyrusCompiler writes into a PEX header.

    Header (big-endian): magic u32, major u8, minor u8, game id u16, compile time u64,
    then source, user and machine names as u16-length strings. Nothing later in the
    file holds offsets, so the lengths may change.
    """
    data = Path(path).read_bytes()
    o = 16
    o += 2 + int.from_bytes(data[o:o + 2], "big")  # keep the source file name
    head, rest = data[:o], data[o:]
    for _ in range(2):
        rest = rest[2 + int.from_bytes(rest[:2], "big"):]
    field = len(b"CHIM Lite Starter").to_bytes(2, "big") + b"CHIM Lite Starter"
    Path(path).write_bytes(head + field + field + rest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--compiler", required=True, type=Path)
    ap.add_argument("--import", dest="imports", action="append", default=[], type=Path)
    ap.add_argument("--install", type=Path, help="MO2 mod folder to copy the result into")
    args = ap.parse_args()

    out = HERE / "build"
    compiled = out / "Scripts"
    compiled.mkdir(parents=True, exist_ok=True)
    imports = [HERE / "Scripts" / "Source", HERE / "Scripts" / "Stubs", *args.imports]
    for s in SCRIPTS:
        text = run([args.compiler, f"{s}.psc", "-f=TESV_Papyrus_Flags.flg",
                    "-i=" + ";".join(map(str, imports)), f"-o={compiled}"])
        if "0 error(s)" not in text:
            sys.exit(f"FAILED compiling {s}:\n{text}")
        scrub_pex_identity(compiled / f"{s}.pex")
    print(f"compiled {len(SCRIPTS)} scripts")

    gen = HERE / "Generator"
    run(["dotnet", "build", "-c", "Release", "-nodeReuse:false", gen])
    subprocess.run(["dotnet", "build-server", "shutdown"], capture_output=True)
    print(run([gen / "bin" / "Release" / "net10.0" / "Generator.exe", out / PLUGIN]).strip())

    if args.install:
        seq = Path(PLUGIN).stem + ".seq"
        pairs = [(out / PLUGIN, args.install / PLUGIN), (out / "SEQ" / seq, args.install / "SEQ" / seq)]
        pairs += [(compiled / f"{s}.pex", args.install / "Scripts" / f"{s}.pex") for s in SCRIPTS]
        pairs += [(HERE / "Scripts" / "Source" / f"{s}.psc", args.install / "Source" / "Scripts" / f"{s}.psc")
                  for s in SCRIPTS]
        for src, dst in pairs:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            if not filecmp.cmp(src, dst, shallow=False):
                sys.exit(f"FAILED: installed copy differs: {dst}")
        if list((args.install / "Scripts").glob("AIAgent*.pex")):
            sys.exit("FAILED: a CHIM stub was installed and would override the real script")
        print(f"installed {len(pairs)} files into {args.install}")


if __name__ == "__main__":
    main()
