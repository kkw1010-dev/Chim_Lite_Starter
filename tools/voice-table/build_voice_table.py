"""Build the reference-to-voice-type table used by fill_voice_ids.py.

CHIM Lite 2.3.3 never fills an NPC profile's voice ID on its own: the game's
addnpc signal carries only race, gender and reference ID, and the service
refuses to synthesize speech for a blank voice ID ("NPC profile has blank voice
ID", reply degraded to text only). MeloTTS voices are named after Skyrim voice
types, so the voice ID an NPC needs is its VoiceType EditorID.

Inputs are four houseCARL `housecarl_records` exports (format=dense, to_file)
taken from an MO2 profile (see the README for the exact calls). Output is the
plugin's voice_table.json: only references defined by the five official masters
(runtime indices 00-04, identical in every load order) are kept, each mapped to
its VoiceType EditorID (lowercase).

Usage: python build_voice_table.py <export_dir> <output.json>
"""

import json
import sys
from collections import Counter
from pathlib import Path

VANILLA_MASTERS = {
    "skyrim.esm", "update.esm", "dawnguard.esm", "hearthfires.esm", "dragonborn.esm",
}
MAX_TEMPLATE_DEPTH = 12

# The service stores the race as the game's localized display name. Korean
# names come from the user's localized strings; English names are included for
# NPCs whose race has no localized name.
RACE_NAME_TO_EDITOR_ID = {
    "노드": "NordRace", "노르드": "NordRace", "nord": "NordRace",
    "임페리얼": "ImperialRace", "imperial": "ImperialRace",
    "브레튼": "BretonRace", "breton": "BretonRace",
    "레드가드": "RedguardRace", "redguard": "RedguardRace",
    "오크": "OrcRace", "orc": "OrcRace", "orsimer": "OrcRace",
    "하이 엘프": "HighElfRace", "하이엘프": "HighElfRace", "알트머": "HighElfRace",
    "high elf": "HighElfRace", "altmer": "HighElfRace",
    "우드 엘프": "WoodElfRace", "우드엘프": "WoodElfRace", "보즈머": "WoodElfRace",
    "wood elf": "WoodElfRace", "bosmer": "WoodElfRace",
    "다크 엘프": "DarkElfRace", "다크엘프": "DarkElfRace", "던머": "DarkElfRace",
    "dark elf": "DarkElfRace", "dunmer": "DarkElfRace",
    "아르고니안": "ArgonianRace", "argonian": "ArgonianRace",
    "카짓": "KhajiitRace", "khajiit": "KhajiitRace",
}
PLAYABLE_RACES = sorted(set(RACE_NAME_TO_EDITOR_ID.values()))

# Generic vanilla voice per playable race and gender, used when the reference
# is not in the table (a load-order change, a runtime-spawned actor) or its
# voice type is a mod's own voice that MeloTTS does not carry.
FALLBACK = {
    "NordRace|male": "malenord", "NordRace|female": "femalenord",
    "ImperialRace|male": "maleeventoned", "ImperialRace|female": "femaleeventoned",
    "BretonRace|male": "maleeventoned", "BretonRace|female": "femaleeventoned",
    "RedguardRace|male": "maleeventoned", "RedguardRace|female": "femalesultry",
    "OrcRace|male": "maleorc", "OrcRace|female": "femaleorc",
    "HighElfRace|male": "maleelfhaughty", "HighElfRace|female": "femaleelfhaughty",
    "WoodElfRace|male": "maleeventoned", "WoodElfRace|female": "femaleeventoned",
    "DarkElfRace|male": "maledarkelf", "DarkElfRace|female": "femaledarkelf",
    "ArgonianRace|male": "maleargonian", "ArgonianRace|female": "femaleargonian",
    "KhajiitRace|male": "malekhajiit", "KhajiitRace|female": "femalekhajiit",
}


def rows(path):
    with open(path, encoding="utf-8") as f:
        manifest = json.loads(f.readline())
        if manifest.get("row_count") != manifest.get("total"):
            raise SystemExit(f"{path}: incomplete export ({manifest.get('row_count')} of {manifest.get('total')})")
        for line in f:
            yield json.loads(line)


def fields(row):
    out = {}
    for item in row["fields"]:
        if "value" in item:
            out[item["path"]] = item["value"]
    return out


def plugin_of(formid):
    return formid.split(":", 1)[1].lower()


def main(export_dir, output):
    d = Path(export_dir)
    voice_types = {}  # formid -> editorid
    race_ids = {}  # race EditorID -> formid
    for r in rows(d / "vtyp_race.jsonl"):
        if r["type"] == "VoiceType" and r["editorid"]:
            voice_types[r["formid"]] = r["editorid"]
        elif r["type"] == "Race" and r["editorid"]:
            race_ids[r["editorid"]] = r["formid"]

    npcs = {}
    for r in rows(d / "npc.jsonl"):
        f = fields(r)
        npcs[r["formid"]] = {
            "voice": f.get("Voice"),
            "template": f.get("Template"),
            "traits_from_template": "Traits" in (f.get("Configuration.TemplateFlags") or ""),
            "female": "Female" in (f.get("Configuration.Flags") or ""),
            "race": f.get("Race"),
        }

    leveled = {}
    for r in rows(d / "lvln.jsonl"):
        refs = [item["value"] for item in r["fields"] if "value" in item]
        leveled[r["formid"]] = refs

    def resolve(formid, depth=0):
        """Voice type FormID the game would use, following Traits templates."""
        if depth > MAX_TEMPLATE_DEPTH:
            return None
        if formid in leveled:
            # A leveled template picks an entry at spawn time; take the first
            # entry that resolves, which matches the common single-voice lists.
            for entry in leveled[formid]:
                v = resolve(entry, depth + 1)
                if v:
                    return v
            return None
        npc = npcs.get(formid)
        if not npc:
            return None
        if npc["traits_from_template"] and npc["template"]:
            return resolve(npc["template"], depth + 1)
        return npc["voice"]

    def is_vanilla_voice(vt_formid):
        return plugin_of(vt_formid) in VANILLA_MASTERS

    vanilla_names = {v.lower() for k, v in voice_types.items() if is_vanilla_voice(k)}
    bad = {k: v for k, v in FALLBACK.items() if v not in vanilla_names}
    if bad:
        raise SystemExit(f"FAIL: fallback voices are not vanilla VoiceType EditorIDs: {bad}")
    fallback = dict(FALLBACK)

    refs = {}
    stats = Counter()
    for r in rows(d / "achr.jsonl"):
        base = fields(r).get("Base")
        vt = resolve(base) if base else None
        if not vt or vt not in voice_types:
            stats["unresolved"] += 1
            continue
        entry = {"voice": voice_types[vt].lower(), "vanilla": is_vanilla_voice(vt)}
        refs[r["runtime_formid"].upper()] = entry
        stats["vanilla" if entry["vanilla"] else "modded"] += 1

    epochs = set()
    for name in ("achr.jsonl", "npc.jsonl", "lvln.jsonl", "vtyp_race.jsonl"):
        with open(d / name, encoding="utf-8") as f:
            epochs.add(json.loads(f.readline()).get("epoch"))

    table = {
        "format": 1,
        "source_epochs": sorted(e for e in epochs if e),
        "race_names": RACE_NAME_TO_EDITOR_ID,
        "fallback": fallback,
        # Portable subset: official-master references with vanilla voice types.
        "refs": dict(sorted((k, v["voice"]) for k, v in refs.items() if k[:2] in ("00", "01", "02", "03", "04") and v["vanilla"])),
    }
    Path(output).write_text(json.dumps(table, ensure_ascii=False, indent=0), encoding="utf-8")

    missing = [f"{r}|{g}" for r in PLAYABLE_RACES for g in ("male", "female") if f"{r}|{g}" not in fallback]
    unmapped = sorted({v for v in RACE_NAME_TO_EDITOR_ID.values() if v not in race_ids})
    if unmapped:
        raise SystemExit(f"FAIL: race EditorIDs not found in the load order: {unmapped}")
    print(f"refs: {len(refs)} ({stats['vanilla']} vanilla voice, {stats['modded']} modded voice, {stats['unresolved']} unresolved)")
    print(f"fallback race/gender pairs: {len(fallback)}; missing: {missing or 'none'}")
    print(f"source epochs: {table['source_epochs']}")
    if missing:
        raise SystemExit("FAIL: a playable race/gender pair has no fallback voice")
    if len(table["source_epochs"]) != 1:
        raise SystemExit("FAIL: exports come from different load-order epochs; re-export all four")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
