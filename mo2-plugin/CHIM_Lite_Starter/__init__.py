# coding=utf-8
"""CHIM Lite Starter - MO2 plugin.

When Skyrim (skse64_loader.exe or SkyrimSE.exe) is launched from MO2:
  1. starts chim-lite.exe, hidden, unless the service already answers on its port;
  2. starts a background thread inside MO2 that fills blank NPC voice IDs through
     the service's local API (127.0.0.1), so NPCs speak without manual voice setup.

It never blocks or cancels the game launch; every problem goes to the log file in
MO2's plugin data folder (plugins/data/CHIM_Lite_Starter/starter.log).
Only the local CHIM Lite API is contacted. No account data is read or stored.
"""

import json
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import List

import mobase

from .voice import VoiceChooser

NAME = "CHIM Lite Starter"
TRIGGERS = {"skse64_loader.exe", "skyrimse.exe"}
POLL_SECONDS = 3.0
IDLE_SECONDS = 15.0  # when the service does not answer


class Starter(mobase.IPlugin):
    def __init__(self):
        super().__init__()
        self._organizer = None
        self._thread = None
        self._stop = threading.Event()
        self._data_dir = None
        self._logged = set()

    # ---- MO2 plugin interface ------------------------------------------------
    def init(self, organizer: mobase.IOrganizer) -> bool:
        self._organizer = organizer
        base = Path(organizer.pluginDataPath()) if hasattr(organizer, "pluginDataPath") else Path(__file__).parent
        self._data_dir = base / "CHIM_Lite_Starter"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        organizer.onAboutToRun(self._on_about_to_run)
        try:
            self._remember_running_exe()
        except Exception as e:
            self._log(f"FAIL exe detection {type(e).__name__}: {e}")
        return True

    def name(self) -> str:
        return NAME

    def author(self) -> str:
        return "kkw1010-dev"

    def description(self) -> str:
        return ("Starts CHIM Lite with Skyrim and fills NPC voice IDs automatically "
                "(male NPCs stay text-only while the TTS service offers no male voice).")

    def version(self) -> mobase.VersionInfo:
        return mobase.VersionInfo(1, 0, 0)

    def settings(self) -> List[mobase.PluginSetting]:
        return [
            mobase.PluginSetting("enabled", "Run CHIM Lite Starter when Skyrim is launched", True),
            mobase.PluginSetting("chim_lite_exe", "Full path to chim-lite.exe (empty: remembered automatically "
                                                  "the first time chim-lite.exe is found running)", ""),
            mobase.PluginSetting("auto_voice", "Fill blank NPC voice IDs automatically", True),
            mobase.PluginSetting("port", "CHIM Lite service port", 8081),
        ]

    def _setting(self, key):
        return self._organizer.pluginSetting(NAME, key)

    # ---- logging -------------------------------------------------------------
    def _log(self, message, once_key=None):
        if once_key is not None:
            if once_key in self._logged:
                return
            self._logged.add(once_key)
        try:
            with open(self._data_dir / "starter.log", "a", encoding="utf-8") as f:
                f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {message}\n")
        except OSError:
            pass

    # ---- launch hook ---------------------------------------------------------
    def _on_about_to_run(self, app_path: str, wd=None, args: str = "") -> bool:
        try:
            if self._setting("enabled") is False or Path(app_path).name.lower() not in TRIGGERS:
                return True
            self._start_service()
            if self._setting("auto_voice") is not False:
                self._start_voice_thread()
        except Exception as e:  # never stop the game from launching
            self._log(f"FAIL {type(e).__name__}: {e}")
        return True

    def _port(self):
        try:
            return int(self._setting("port") or 8081)
        except (TypeError, ValueError):
            return 8081

    def _service_up(self):
        try:
            with socket.create_connection(("127.0.0.1", self._port()), timeout=0.5):
                return True
        except OSError:
            return False

    def _remember_running_exe(self):
        """If chim_lite_exe is empty and chim-lite.exe is running, store its path."""
        if str(self._setting("chim_lite_exe") or "").strip():
            return
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             "(Get-Process chim-lite -ErrorAction SilentlyContinue | Select-Object -First 1).Path"],
            capture_output=True, text=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
        path = r.stdout.strip()
        if path and Path(path).is_file():
            self._organizer.setPluginSetting(NAME, "chim_lite_exe", path)
            self._log(f"remembered running chim-lite.exe: {path}")

    def _start_service(self):
        self._remember_running_exe()
        if self._service_up():
            self._log("service already running")
            return
        exe = Path(str(self._setting("chim_lite_exe") or "").strip().strip('"'))
        if not str(exe) or str(exe) == "." or not exe.is_file():
            self._log(f"service not running and chim_lite_exe is not set to an existing file ({exe}); "
                      "set it in MO2 > Settings > Plugins > CHIM Lite Starter, or start chim-lite.exe once "
                      "and it is remembered")
            return
        subprocess.Popen([str(exe)], cwd=str(exe.parent),
                         creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                         close_fds=True)
        self._log(f"started {exe}")

    def _start_voice_thread(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._voice_loop, name="CHIMLiteStarterVoice", daemon=True)
        self._thread.start()
        self._log("voice thread started")

    # ---- voice filling -------------------------------------------------------
    def _api(self, method, path, body=None):
        url = f"http://127.0.0.1:{self._port()}/api/{path}"
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status, json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            return e.code, None

    def _profiles(self):
        page, out = 1, []
        while True:
            status, body = self._api("GET", f"npc/profiles?page={page}&limit=100")
            if status != 200 or not body:
                raise ConnectionError(f"npc/profiles returned HTTP {status}")
            out += body.get("items", [])
            if page * body.get("limit", 100) >= body.get("total", 0):
                return out
            page += 1

    def _assigned_path(self):
        return self._data_dir / "assigned.json"

    def _voice_loop(self):
        try:
            chooser = VoiceChooser()
        except Exception as e:
            self._log(f"FAIL voice data: {e}")
            return
        try:
            assigned = json.loads(self._assigned_path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            assigned = {}
        while not self._stop.is_set():
            try:
                for prof in self._profiles():
                    name, current = prof["npc_name"], (prof.get("voiceid") or "").strip()
                    if current and current != assigned.get(name):
                        continue  # set by the player or by the service: never touch
                    voice, why = chooser.choose(prof)
                    if voice == current:
                        continue
                    if self._write_voice(name, current, voice):
                        assigned[name] = voice
                        self._assigned_path().write_text(json.dumps(assigned, ensure_ascii=False, indent=1), encoding="utf-8")
                        self._log(f"{'REMAP' if current else 'SET'} {name}: {current or '-'} -> "
                                  f"{voice or '(text only)'} ({why})")
                self._stop.wait(POLL_SECONDS)
            except (OSError, ConnectionError, ValueError) as e:
                self._log(f"service not reachable: {e}", once_key=("down", type(e).__name__))
                self._stop.wait(IDLE_SECONDS)
            except Exception as e:
                self._log(f"FAIL voice loop {type(e).__name__}: {e}", once_key=("fail", str(e)))
                self._stop.wait(IDLE_SECONDS)

    def _write_voice(self, name, expected, voice):
        path = f"npc/{urllib.parse.quote(name, safe='')}/biography"
        status, bio = self._api("GET", path)
        if status != 200 or not bio or (bio.get("voiceid") or "").strip() != expected:
            return False
        status, _ = self._api("PUT", path, dict(bio, voiceid=voice))
        status2, back = self._api("GET", path)
        ok = status == 200 and status2 == 200 and back and back.get("voiceid") == voice
        if not ok:
            self._log(f"FAIL {name}: write not confirmed (PUT {status})", once_key=("write", name))
        return ok


def createPlugin() -> mobase.IPlugin:
    return Starter()
