# coding=utf-8
"""Voice choice for CHIM Lite NPC profiles. No MO2 dependency (testable alone).

CHIM Lite never fills an NPC profile's voice ID; the service then answers that NPC
in text only ("NPC profile has blank voice ID"). This module picks one:

1. The NPC's Skyrim voice type: from voice_table.json when the profile's refid is a
   vanilla placed reference (Skyrim.esm and the four official masters load at
   indices 00-04 in every load order, so these runtime FormIDs are the same for
   everyone), otherwise a generic voice type for the profile's race and gender.
2. The provider voice for that voice type, from provider_voices.json. A voice
   whose declared gender differs from the NPC's is replaced by that gender's
   default; when the gender has no default (null), the result is "" = text only.
   A voice type mapped to null (e.g. children, for whom no fitting voice exists)
   is text only. "npcs" overrides the result for one reference ID.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
UNKNOWN_RACE = {"male": "maleeventoned", "female": "femaleeventoned"}


def load_json(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


class VoiceChooser:
    def __init__(self, table=None, provider=None):
        self.table = table or load_json("voice_table.json")
        self.provider = provider or load_json("provider_voices.json")
        self._validate()

    def _validate(self):
        p = self.provider
        names = set(p["voices"])
        used = [*p["map"].values(), *p["keywords"].values(), *p["default"].values(),
                *(n["voice"] for n in p.get("npcs", {}).values())]
        bad = sorted({v for v in used if v and v not in names})
        if bad:
            raise ValueError(f"provider_voices.json maps to unlisted voices: {bad}")
        missing = sorted(v for v in names if p["genders"].get(v) not in ("male", "female"))
        if missing:
            raise ValueError(f"provider_voices.json gives no gender for: {missing}")

    @staticmethod
    def gender_of(profile):
        return "female" if (profile.get("gender") or "").lower() == "female" else "male"

    def race_key(self, race):
        text = (race or "").strip().lower()
        for name, editor_id in self.table["race_names"].items():
            if text == name.lower():
                return editor_id
        for editor_id in set(self.table["race_names"].values()):
            if text.startswith(editor_id.lower()):  # e.g. "NordRace_CF"
                return editor_id
        return None

    def voice_type_of(self, profile):
        refid = (profile.get("refid") or "").upper()
        vt = self.table["refs"].get(refid)
        if vt:
            return vt, f"voice type of {refid}"
        key = self.race_key(profile.get("race"))
        gender = self.gender_of(profile)
        if key:
            return self.table["fallback"][f"{key}|{gender}"], f"generic {key}"
        return UNKNOWN_RACE[gender], f"generic, unknown race {profile.get('race')!r}"

    def choose(self, profile):
        """(voice, reason). voice == "" means leave the NPC text-only."""
        p = self.provider
        voice_type, why = self.voice_type_of(profile)
        gender = self.gender_of(profile)
        override = p.get("npcs", {}).get((profile.get("refid") or "").upper())
        if override:
            return override["voice"] or "", f"{voice_type}; per-NPC choice ({override.get('note', '')})"
        voice = next((v for k, v in p["keywords"].items() if k in voice_type), None)
        if voice is None and voice_type in p["map"]:
            voice = p["map"][voice_type]
            if not voice:
                return "", f"{voice_type}; {why}; mapped to text only"
        voice = voice or p["default"][gender] or ""
        if voice and p["genders"].get(voice) != gender:
            voice = p["default"][gender] or ""
        if not voice:
            return "", f"{voice_type}; {why}; no {gender} voice offered, text only"
        return voice, f"{voice_type}; {why}"
