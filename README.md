# CHIM Lite Starter

CHIM Lite 2.3.3 + SeranaCHANnel 환경에서 쓰는 비공식 확장 두 가지.

| 구성 | 하는 일 |
| --- | --- |
| **CHIM Lite - Dialogue Chat** (ESL 플래그 ESP) | 단축키 없이 **NPC 대화 선택지**로 CHIM 채팅을 연다. 대화 대상이 AI 에이전트가 아니면 **임시 에이전트**로 만들고, 필요 없어지면 해제한다. CHIM이 기본으로 거는 텍스트 채팅 키(숫자패드 0)도 해제한다. |
| **CHIM Lite Starter** (MO2 플러그인) | MO2에서 스카이림을 실행하면 **chim-lite.exe를 자동 실행**한다. 게임 중에는 **빈 NPC Voice ID를 자동으로 채운다**. 별도 Python 설치가 필요 없다(MO2 내장 Python 사용). |

> **원 제작자 퍼미션**: CHIM Lite 제작자에게 개조 및 업로드 허락을 받았다. 제작자는 이 기능들을 CHIM Lite 본체로 **흡수할 계획**을 밝혔다. 그래서 이 저장소는 흡수 작업에 필요한 동작 원리, 레코드 구성, 검증 결과를 최대한 자세히 적는다. 흡수가 끝나면 이 저장소의 역할도 끝난다.

---

## 1. 왜 만들었나

### 1-1. 단축키

단축키를 없애는 모드를 만드는 입장에서, CHIM이 단축키를 여러 개 추가하는 것은 받아들이기 어려웠다(Text Chat, Master Wheel, Roleplay/Settings/Mode Wheel, Manual AI Activate, Halt 등). 게다가 MCM에 모든 키가 "미지정(-1)"으로 보여도, `AIAgentPapyrusFunctions.OnInit()`이 새 게임마다 `doBinding(0x52)`를 호출한다. 그래서 텍스트 채팅이 **숫자패드 0에 몰래 걸린다**.

### 1-2. NPC가 말을 하지 않음 (텍스트만 나옴)

CHIM Lite 서비스 로그에는 NPC가 대답할 때마다 다음 줄이 남았다.

```
WARN chim_lite_server::tts_response: TTS response degraded to text only line_index=0
     error=Configuration error: NPC profile has blank voice ID: <NPC 이름>
```

- 게임의 `addnpc` 신호에는 race, gender, refid만 있다(서비스 로그: `[ADDNPC] received for '…' race='…' gender='…' refid='…'`). **Voice ID는 오지 않는다.**
- 서비스는 `npc_master.voiceid`를 빈 값으로 만든다. 빈 값이면 TTS를 건너뛴다. 풀버전 CHIM에 있는 "Fallback Voices" 기능은 Lite에 없다.
- 그래서 Lite에서는 원래 **웹 UI(NPC → Voice ID)에서 NPC마다 손으로 입력**해야 한다. 제작자 정보글에도 그렇게 안내되어 있다. NPC가 늘어날 때마다 사람이 입력하는 것은 현실적이지 않아서 자동화했다.

---

## 2. 설치

### 2-1. Dialogue Chat (ESP)

1. `dialogue-chat-mod/` 폴더 전체를 MO2 모드로 설치한다. 파일은 `CHIM Lite - Dialogue Chat.esp`, `SEQ/`, `Scripts/`, `Source/`이다.
2. 플러그인 순서는 `AIAgent.esp` **뒤**여야 한다(마스터가 `Skyrim.esm`, `AIAgent.esp`).
3. **새 게임 필요.** 시작 시 활성화되는 퀘스트와 스크립트 속성을 추가하기 때문이다.
4. 선행 모드는 CHIM Lite 2.3.3과 CHIM Lite가 이미 요구하는 것(SKSE, PapyrusUtil, UIExtensions)뿐이다.

### 2-2. Starter (MO2 플러그인)

1. `mo2-plugin/CHIM_Lite_Starter/` 폴더를 **`<MO2 설치 폴더>/plugins/`** 안에 그대로 복사한다. 결과는 `plugins/CHIM_Lite_Starter/__init__.py`가 된다.
2. MO2를 재시작한다.
3. MO2 → 설정(Settings) → 플러그인(Plugins) → **CHIM Lite Starter**에서 `chim_lite_exe`에 `chim-lite.exe`의 전체 경로를 입력한다. 비워 두면 서비스를 자동 실행하지 않고, 음성 채우기만 한다(이미 서비스를 켜 둔 경우).
4. 게임 전에 **SeranaCHANnel에 로그인**한다. API 호출이 30분 동안 없으면 자동 로그아웃되고, 그러면 LLM과 TTS가 모두 `HTTP 404 endpoint_inactive`를 돌려준다.
5. MO2에서 SKSE(`skse64_loader.exe`) 또는 `SkyrimSE.exe`를 실행한다.

로그는 `<MO2>/plugins/data/CHIM_Lite_Starter/starter.log`에 남는다. 서비스 시작, 음성 스레드 시작, NPC별 `SET`/`REMAP`, 오류가 기록된다.

| 설정 | 기본값 | 의미 |
| --- | --- | --- |
| `enabled` | true | 스카이림 실행 시 동작 |
| `chim_lite_exe` | "" | chim-lite.exe 경로. 비우면 자동 실행 안 함 |
| `auto_voice` | true | 빈 Voice ID 자동 채우기 |
| `port` | 8081 | CHIM Lite 서비스 포트 |

---

## 3. Dialogue Chat 기술 상세 (흡수용)

### 3-1. 레코드

ESL 플래그가 붙은 ESP이다. FormID는 모두 0x800~0xFFF 범위이다. 원본 `AIAgent.esp`의 레코드는 **하나도 수정하거나 덮어쓰지 않는다**(override 0건).

| FormID | 종류 | EditorID | 내용 |
| --- | --- | --- | --- |
| 800 | QUST | `TKLChimChatQuest` | 플래그 `0x011`(StartGameEnabled + 바닐라 대화 퀘스트가 모두 가진 0x010 비트), Priority 50, Type None. 스크립트 `TKLChimChatController`. Alias 0 = 플레이어(ForcedRef 000014), 별칭 스크립트 `TKLChimChatPlayerAlias` |
| 801 | FACT | `TKLChimChatTempAgentFaction` | 이 모드가 임시로 에이전트로 만든 NPC 표시용 |
| 810/811/812 | DIAL/DLBR/INFO | `TKLChimChatTalk*` | 플레이어 선택지 `[AI] 이야기 좀 하자.` → NPC `무슨 이야기지?`. 조건: Subject `HasKeyword ActorTypeNPC(013794) == 1`. Goodbye 플래그. End 프래그먼트 `TKLChimChatTalkFragment` |
| 820/821/822 | DIAL/DLBR/INFO | `TKLChimChatEnd*` | 플레이어 선택지 `[AI] 이야기는 여기까지 하지.` → NPC `그러지.`. 조건: `GetInFaction TKLChimChatTempAgentFaction == 1`. Goodbye. End 프래그먼트 `TKLChimChatEndFragment` |

- DLBR은 **Top-Level, Category Player**이다. DIAL은 Category Topic, Subtype Custom(`CUST`)이다. 최상위 브랜치에 속하지 않은 플레이어 토픽은 대화 메뉴에 나오지 않는다.
- `SEQ/CHIM Lite - Dialogue Chat.seq`(`02000800`)가 반드시 있어야 한다. 대화를 가진 StartGameEnabled 퀘스트는 SEQ에 없으면 새 게임에서 잠든 상태로 남고, 선택지가 **아예 나오지 않는다**. 값은 `(마스터 수 << 24) | 로컬ID`이다.
- 한국어 문자열은 UTF-8이다(Mutagen `EncodingBundle(_utf8, _utf8)`).
- CK 호환 하위 레코드: INFO CNAM(FavorLevel None), 별칭 FNAM(0)과 VTCK(null 링크). 없으면 CK 대화 편집기가 튕긴다. 게임은 괜찮다.

### 3-2. 스크립트 동작

`TKLChimChatController`(퀘스트 스크립트)의 속성은 다음과 같다.

- `ChimControl` → `AIAgent.esp` 0093FC 퀘스트의 `AIAgentPapyrusFunctions`
- `TempAgentFaction` → 801
- `PlayerRef` → 000014

**대화하기** (`RequestChat(akTarget)`, Talk 선택지의 End 프래그먼트에서 호출)

1. `AIAgentFunctions.findAllAgents()`에 대상이 없으면 `AIAgentFunctions.setDrivenByAIA(akTarget, false)`로 에이전트화한다(인사말 없이). 그 NPC를 `TempAgentFaction`에 넣고, PapyrusUtil `StorageUtil.FormList "TKLChimChat.TempAgents"`에도 기록한다.
2. 대화 메뉴는 게임을 멈추지 않는다. 그래서 `RegisterForSingleUpdate`로 대기하다가, `UI.IsMenuOpen("Dialogue Menu")`가 false가 된 뒤에 `UIExtensions.OpenMenu("UITextEntryMenu")`를 연다. CHIM 텍스트 채팅 단축키가 쓰는 것과 같은 입력창이다.
3. 입력 문자열을 `AIAgentFunctions.sendMessage(text, "")`로 보낸다. DLL은 입력을 **조준선 아래 NPC**에게 보낸다(DLL 문자열 `Ref under crosshair`, `(Talking to {})`). 대화 직후에는 방금 대화한 NPC가 조준선 아래에 있다.

**해제**

- End 선택지는 `ReleaseAgent(akTarget)`를 호출한다. `setDrivenByAIA`는 **토글**이라서, 이미 에이전트인 NPC에 호출하면 해제된다. 그 뒤 faction과 목록에서도 뺀다.
- 자동 해제는 `ReleaseAbsentAgents()`가 맡는다. 플레이어 별칭의 `OnLocationChange`와 `OnPlayerLoadGame`에서만 실행하고, 타이머는 쓰지 않는다. 목록을 돌면서 죽었거나, 3D가 로드되지 않았거나, 4096 유닛보다 멀리 있는 임시 에이전트를 해제한다.
- 원래부터 에이전트였던 NPC(수동 추가, 자동 추가)는 임시로 표시하지 않으므로, 이 모드가 절대 해제하지 않는다.

**숫자패드 0 해제**: 퀘스트 `OnInit` 5초 뒤 `ChimControl.removeBinding(82)`를 한 번 호출한다. 이후 MCM에서 키를 지정하면 그 키는 정상적으로 동작한다.

**진단 로그**: 모든 단계가 Papyrus 로그에 `[TKLChimChat]` 줄을 남긴다. 퀘스트 시작과 속성 바인딩, 속성이 비었을 때의 ERROR, 숫자패드 0 해제, 선택지 선택과 화자, 임시 에이전트 추가와 해제, 에이전트 등록 지연 WARNING, 채팅 전송이 기록된다.

**MCM Memory 사용자 주의**: MCM Memory가 CHIM 키를 기록해 두었으면 새 게임마다 다시 걸린다. 프로필에서 `AIAgentMCMConfigScript::CHIM` 항목을 지워야 한다.

### 3-3. 본체 흡수 시 제안

- 선택지와 퀘스트는 `AIAgent.esp`에 그대로 옮기면 된다. 프래그먼트는 두 개이고, 컨트롤러 함수는 세 개(`RequestChat`, `ReleaseAgent`, `ReleaseAbsentAgents`)이다.
- 숫자패드 0 기본 바인딩은 `AIAgentPapyrusFunctions.OnInit()`의 `doBinding(_currentKey)`를 없애고, MCM 값(-1)과 맞추면 끝난다.
- Voice ID 문제는 서비스 쪽에서 해결하는 것이 가장 깔끔하다. `addnpc` 신호에 VoiceType EditorID를 추가하거나(DLL은 이미 `[VOICE] Voice name for` 경로로 음성 타입을 안다), `voiceid`가 비었을 때 종족·성별 기본 음성으로 대체하면 된다(풀버전의 Fallback Voices).

---

## 4. Starter(자동 Voice ID) 기술 상세

### 4-1. 동작

- **실행 감지**: MO2 `IOrganizer.onAboutToRun(path, wd, args)`에서 실행 파일 이름이 `skse64_loader.exe`나 `SkyrimSE.exe`일 때만 동작한다. 어떤 예외가 나도 `True`를 돌려주므로, **게임 실행을 막지 않는다**.
- **서비스 실행**: `127.0.0.1:<port>`에 접속되지 않을 때만 `chim_lite_exe`를 창 없이(`CREATE_NO_WINDOW | DETACHED_PROCESS`) 실행한다. 작업 폴더는 exe 폴더이다.
- **음성 스레드**: MO2 프로세스 안의 데몬 스레드로, 3초마다 다음을 반복한다.
  1. `GET /api/npc/profiles?page=N&limit=100`(한 번에 최대 100개)으로 전체 목록을 읽는다.
  2. Voice ID가 비었거나 이 플러그인이 이전에 넣은 값인 NPC에 대해 음성을 고른다.
  3. `GET /api/npc/{이름}/biography` → `voiceid`만 바꿔 `PUT` → 다시 `GET`으로 확인한다.
- **사용자가 직접 넣은 Voice ID는 절대 바꾸지 않는다.** 플러그인이 넣은 값은 `plugins/data/CHIM_Lite_Starter/assigned.json`에 기록하고, 이 파일에 있는 값만 다시 계산한다.
- 통신 대상은 **로컬 CHIM Lite API(127.0.0.1)뿐**이다. 계정, 엔드포인트, 비밀번호는 읽지도 저장하지도 않는다. TTS 테스트 호출도 하지 않는다. 연속 테스트 호출 뒤 제공자가 한동안 `MeloTTS returned empty audio`를 돌려주는 것이 두 번 관찰되었다.

### 4-2. 음성 고르기

1. **Skyrim VoiceType 찾기** (`voice_table.json`)
   - 프로필의 `refid`(배치 참조 런타임 FormID)로 VoiceType EditorID를 찾는다.
   - 표에는 `Skyrim.esm`, `Update.esm`, `Dawnguard.esm`, `HearthFires.esm`, `Dragonborn.esm`이 정의한 배치 NPC 12,595개만 들어 있다. 이 다섯 파일은 어느 load order에서나 00~04번에 로드되므로, 런타임 FormID가 누구에게나 같다.
   - 템플릿은 실제 게임과 같게 따라간다. `Traits` 템플릿 플래그가 있으면 NPC 템플릿을 따라가고, Leveled NPC 템플릿이면 첫 항목을 따른다.
   - 표에 없는 참조(모드 NPC, 스크립트로 생성된 NPC)는 프로필의 종족과 성별로 고른 기본 VoiceType을 쓴다. 종족 이름은 한국어와 영어 표시명, `NordRace_CF` 같은 EditorID를 모두 인식한다.
2. **제공 음성으로 변환** (`provider_voices.json`)
   - SeranaCHANnel TTS는 ElevenLabs 매핑이다. 목록에 없는 이름은 `HTTP 422 unknown_speaker`로 거부된다. Skyrim VoiceType 이름(`malenord`, `femalenord` 등)도 그대로는 거부된다.
   - 2026-09-25 기준 제공 음성: `Ashe, FemaleCommander, FemaleEvenToned, FemaleYoungEager, Frea, Serana, TS_Gelebor, TS_Miraak, Valerica`.
   - **청취 확인 결과 9개 모두 여성 음성**이다. `TS_Miraak`(256Hz), `TS_Gelebor`(208Hz)는 성별을 바꾼 버전으로 보이고, `Valerica`(134Hz)는 낮은 여성 음성이다. 그래서 `default.male = null`로 두어 **남성 NPC는 Voice ID를 비운다(텍스트만)**. 여성 음성으로 남성 NPC를 말하게 하지 않으려는 선택이다.
   - 여성 VoiceType은 성격에 맞춰 연결한다. 예: `femalecommander → FemaleCommander`, `femalenord → Frea`, `femalesultry → FemaleYoungEager`. 나머지는 `FemaleEvenToned`이다.
3. **남성 음성이 추가되면**: `provider_voices.json`의 `voices`에 이름을 넣고, `genders`에 `"male"`, `default.male`에 그 이름을 넣은 뒤 MO2를 재시작한다. 이전에 비워 둔 남성 NPC도 자동으로 채워진다.

### 4-3. 검증 결과 (2026-09-25, 개발자 환경)

- **게임 내 테스트 통과**: 대화 선택지, 임시 에이전트 추가와 해제, 장소 이동 시 자동 해제, 단축키 없음, 여성 NPC 음성, 남성 NPC 텍스트만. Papyrus 로그로 각 단계를 확인했다.
- 같은 음성 선택 로직을 실제 서비스의 NPC 23명에 적용했다. 21명은 게임에서 확인된 배정과 같았다. 나머지 2명은 모드 NPC라서, 배포 표(공식 마스터 전용) 대신 종족 기본 여성 음성을 받는다.
- MO2 플러그인은 가짜 `mobase`로 다음을 확인했다.
  - 게임이 아닌 실행에는 반응하지 않는다.
  - 서비스가 켜져 있으면 다시 실행하지 않는다.
  - 음성 스레드는 중복으로 생기지 않는다.
  - 빈 Voice ID를 채우고 다시 읽어 확인한다.
  - 서비스가 꺼져 있으면 exe를 실행하고, 경로가 틀리면 로그로 안내한다.
- **실제 MO2 안에서의 로드는 개발자 환경에서 아직 확인하지 않았다.** 이 패키지 형태로 설치해 게임을 켠 기록이 없다.

---

## 5. 다시 빌드하기

### Dialogue Chat ESP와 스크립트

필요한 것: .NET SDK 10, PapyrusCompiler, 바닐라·SKSE·PapyrusUtil 스크립트 소스.

```
python tools/dialogue-chat/build.py --compiler "<...>/PapyrusCompiler.exe" ^
  --import "<PapyrusUtil>/Scripts/Source" --import "<SKSE>/Scripts/Source" ^
  --import "<바닐라 소스 + TESV_Papyrus_Flags.flg 폴더>" ^
  --install "<MO2>/mods/CHIM Lite - Dialogue Chat"
```

- CHIM Lite의 `.psc`는 RaceMenu와 po3 소스까지 요구하므로 쓰지 않는다. 대신 `Scripts/Stubs`에 필요한 함수 선언만 둔 스텁을 쓴다(컴파일 전용, 배포하지 않음).
- 생성기(`Generator/Program.cs`, Mutagen 0.54.4)는 ESP를 다시 읽어 검사한다. 마스터, ESL 플래그, 퀘스트 플래그, 스크립트 부착, 최상위 브랜치, UTF-8 한국어, Goodbye 플래그, End 프래그먼트, 조건 수, SEQ 값, CNAM, FNAM 중 하나라도 틀리면 빌드가 실패한다.
- 컴파일러가 PEX 헤더에 넣는 Windows 사용자명과 PC 이름은 빌드 과정에서 `CHIM Lite Starter`로 바꾼다.

### voice_table.json

houseCARL(MO2 데이터 계층 MCP 서버)의 `housecarl_records`로 다음 네 가지를 `format="dense"`, `to_file`로 내보낸 뒤 실행한다.

1. `types=["ACHR"]`, `project={"form":"fields","fields":["Base"]}` → `achr.jsonl`
2. `types=["NPC_"]`, `project={"form":"fields","fields":["EditorID","Voice","Template","Configuration.TemplateFlags","Configuration.Flags","Race"]}` → `npc.jsonl`
3. `types=["LVLN"]`, `project={"form":"fields","fields":["Entries[*].Data.Reference"]}` → `lvln.jsonl`
4. `types=["VTYP","RACE"]`, `project={"form":"fields","fields":["EditorID"]}` → `vtyp_race.jsonl`

```
python tools/voice-table/build_voice_table.py <내보낸 폴더> mo2-plugin/CHIM_Lite_Starter/voice_table.json
```

---

## 6. 알려진 한계

- SeranaCHANnel에 남성 음성이 없는 동안 남성 NPC는 텍스트만 나온다.
- NPC가 처음 등록된 직후의 첫 대답은, Voice ID가 채워지기 전(최대 약 3초)이면 무음일 수 있다.
- SeranaCHANnel 세션은 API 호출이 30분 동안 없으면 끊긴다. 게임 전에 로그인해야 한다.
- 대사 문구와 선택지 문구는 개발자가 정한 것이다. 바꾸려면 `Generator/Program.cs`의 `AddTopic` 인자를 고치면 된다.
