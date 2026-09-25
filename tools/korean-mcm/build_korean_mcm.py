"""Build the Korean CHIM Lite 2.3.3 MCM source from the installed upstream PSC.

Only user-facing literals are changed. Internal keys, voice identifiers and NPC
matching strings stay as shipped. Compile the generated PSC with PapyrusCompiler.
"""

from pathlib import Path

# Optional: python build_korean_mcm.py <CHIM Lite Source/Scripts/AIAgentMCMConfigScript.psc> [output.psc]
# writes a Korean .psc for source-based maintenance. The shipped translation is the
# string-table patch made by patch_pex_strings.py, which imports LABELS from here.
import sys
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else None
OUTPUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "AIAgentMCMConfigScript.psc"

LABELS = {
    "Main": "기본",
    "Behavior": "행동",
    "Sound": "소리",
    "AI Agents": "AI 에이전트",
    "Tools": "도구",
    "Text Chat": "텍스트 대화",
    "Master Wheel": "마스터 휠",
    "Roleplay Wheel": "롤플레이 휠",
    "Settings Wheel": "설정 휠",
    "Mode Wheel": "모드 휠",
    "Manual AI Activate": "AI 수동 활성화",
    "Halt AI Actions": "AI 행동 중단",
    "Connection Timeout (seconds)": "연결 시간 제한 (초)",
    "Bored Event Timer (seconds)": "심심함 이벤트 간격 (초)",
    "Dynamic Profile Timer (minutes)": "동적 프로필 갱신 간격 (분)",
    "Smart Rechat": "스마트 재대화",
    "Interior Auto Activate Distance": "실내 자동 활성화 거리",
    "Exterior Auto Activate Distance": "실외 자동 활성화 거리",
    "NPCs Sandbox Near Player": "NPC가 플레이어 근처에서 배회",
    "Seat Conversation Camera": "앉아서 대화할 때 카메라 회전",
    "NPC Scene Safety": "기존 대화 장면 보호",
    "Auto Activate Options": "자동 활성화 설정",
    "Add Hostile NPCs": "적대 NPC도 추가",
    "Add All races": "모든 종족 추가",
    "Allow combat dialogue": "전투 중 대화 허용",
    "Clear dialogue entering combat": "전투 시작 시 대화 취소",
    "Enable Combat Barks": "전투 외침 사용",
    "Combat Bark Timer (seconds)": "전투 외침 간격 (초)",
    "AI Voice Volume": "AI 음성 음량",
    "AI Voice Distance Scale": "AI 음성 거리 배율",
    "Skip milliseconds at begining": "음성 시작 부분 건너뛰기 (밀리초)",
    "Skip milliseconds at end": "음성 끝부분 건너뛰기 (밀리초)",
    "3D Sound Invert Heading": "3D 음향 방향 반전",
    "Resolution of Lip Animations": "입 모양 애니메이션 해상도",
    "Intensity of Lip Animations ": "입 모양 애니메이션 강도",
    "Pause Dialogue on Game Pause": "게임 일시 정지 시 대화 멈춤",
    "Open Mic Settings": "상시 마이크 설정",
    "Enable Open Mic": "상시 마이크 사용",
    "Voice Detection Sensitivity": "음성 감지 민감도",
    "End of Sentence Delay (seconds)": "문장 종료 대기 시간 (초)",
    "Mute Open Mic": "상시 마이크 음소거",
    "Agent Management": "에이전트 관리",
    "Add all current AI Agents": "현재 AI 에이전트 모두 추가",
    "Remove All AI Agents": "모든 AI 에이전트 제거",
    "Remove: ": "제거: ",
    "Active AI Agents": "활성 AI 에이전트",
    "No AI agents active": "활성 AI 에이전트 없음",
    "Total Active Agents: ": "활성 에이전트 수: ",
    "Nearby Available NPCs": "근처에서 추가할 수 있는 NPC",
    "Refresh Nearby NPCs List": "근처 NPC 목록 새로고침",
    "Add: ": "추가: ",
    "No nearby available NPCs": "추가할 수 있는 근처 NPC 없음",
    "Available NPCs: ": "추가 가능한 NPC 수: ",
    "Close menu": "메뉴를 닫아 주세요",
    "AI agents added successfully": "AI 에이전트를 추가했습니다",
    "Are you sure you want to remove ALL AI agents? Won't do anything if Auto Activate is enabled.": "모든 AI 에이전트를 제거할까요? 자동 활성화가 켜져 있으면 다시 추가될 수 있습니다.",
    "All AI agents removed": "모든 AI 에이전트를 제거했습니다",
    "Removed AI agent: ": "제거한 AI 에이전트: ",
    "Nearby NPCs list refreshed": "근처 NPC 목록을 새로고침했습니다",
    "Added AI agent: ": "추가한 AI 에이전트: ",
    "Could not find NPC: ": "NPC를 찾을 수 없습니다: ",
    "Open a text box to communicate with AI NPCs via typed messages.": "입력창을 열어 AI NPC와 글로 대화합니다.",
    "Enables Text-to-Speech for AI NPCs.": "AI NPC의 음성 합성을 켭니다.",
    "If using mods like RDO, check this to force default voice, so dialog Follow me should appear. Note that checking this will disable custom voiced sounds. As of version 0.9.x, this shouldn't be needed.": "RDO 같은 모드에서 '따라와' 대화가 보이지 않으면 기본 음성을 강제합니다. 사용자 지정 음성은 꺼집니다. 0.9.x 이후에는 대개 필요하지 않습니다.",
    "Settings Wheel - Looking at NPC: Assign profiles (1-4). Not looking: Switch LLM models, toggle focus chat.": "설정 휠: NPC를 바라보면 프로필(1~4)을 지정합니다. 다른 곳을 보면 LLM 모델이나 집중 대화 설정을 바꿉니다.",
    "Roleplay Wheel - Write Diary, Gather NPCs, Follow NPC, Update NPC, Wait/Follow, Stop All AI, Add to BgL. Hold it for nearby NPCs to write diary entries.": "롤플레이 휠: 일지 작성, NPC 모으기·따라가기·갱신, 대기/동행, 모든 AI 중단, BgL 추가. 길게 누르면 근처 NPC의 일지를 작성합니다.",
    "Change AI/LLM Connector.": "AI/LLM 연결 설정을 바꿉니다.",
    "Manually activate/deactivate AI control for the targeted NPC or all nearby NPCs if none targeted.": "대상 NPC의 AI 제어를 수동으로 켜거나 끕니다. 대상이 없으면 근처 NPC 전체에 적용합니다.",
    "Set AI NPC speech volume.": "AI NPC 음성의 음량을 정합니다.",
    "Skips specified millisecods at begining of a sentence. Some TTS services add some silence at the begining of audio clips.": "문장 시작 부분을 지정한 밀리초만큼 건너뜁니다. 일부 TTS 서비스가 앞에 붙이는 무음을 줄일 수 있습니다.",
    "Skips specified millisecods at end of a sentence. Some TTS services add some silence at the end of audio clips.": "문장 끝 부분을 지정한 밀리초만큼 건너뜁니다. 일부 TTS 서비스가 뒤에 붙이는 무음을 줄일 수 있습니다.",
    "Adjust AI NPC volume at distance.": "거리에 따른 AI NPC 음량을 조정합니다.",
    "Lip modifier intensity. Set it lower if mouth opens too much ": "입 모양 움직임의 강도입니다. 입을 지나치게 크게 벌리면 낮추세요.",
    "Lip modifier resolution. Set it lower if movement is too laggy. Lower uses more CPU. Find your sweet spot.": "입 모양 움직임의 해상도입니다. 반응이 늦으면 낮추세요. 낮은 값은 CPU를 더 사용합니다.",
    "Connection timeout when requesting data from CHIM Server. Recommended: 60 seconds.": "CHIM 서버 응답을 기다리는 시간입니다. 권장값: 60초.",
    "Mod name has changed. This will reset MCM to show new name. May affect other mods. Will call setstage SKI_ConfigManagerInstance 1": "모드 이름 변경 후 MCM을 새로 고칩니다. 다른 모드에 영향을 줄 수 있습니다. SKI_ConfigManagerInstance의 단계를 1로 설정합니다.",
    "When using 3D sound, it will try inverting the heading. This may resolve issues where NPCs in the front are heard at a lower volume.": "3D 음향 방향을 반전합니다. 앞에 있는 NPC의 목소리가 작게 들리는 문제에 도움이 될 수 있습니다.",
    "Enable to pause dialogue during game pauses. Disable to allow dialogue to continue during game pauses.": "게임이 일시 정지될 때 대화를 멈춥니다. 끄면 대화가 계속됩니다.",
    "AI within this distance in interiors are Auto Activated.": "실내에서 이 거리 안의 NPC를 자동으로 활성화합니다.",
    "AI within this distance outside are Auto Activated.": "실외에서 이 거리 안의 NPC를 자동으로 활성화합니다.",
    "How many seconds (with some exceptions) a Bored event can potenitally be triggered.": "심심함 이벤트가 발생할 수 있는 간격입니다. 일부 예외가 있습니다.",
    "Timer for automatic dynamic profile updates. Updates NPC personalities based on recent events.": "최근 사건을 반영해 NPC 성격 프로필을 자동 갱신하는 간격입니다.",
    "When enabled, will send more context to a responding NPC during a Rechat event.": "재대화 이벤트에서 응답하는 NPC에게 더 많은 맥락을 보냅니다.",
    "Only works when player is seated. When enabled NPC's will subtly move around the player to make listening to conversations easier.": "플레이어가 앉아 있을 때 NPC가 주변에서 조금씩 움직여 대화를 듣기 쉽게 합니다.",
    "Only works when player is seated and 1st person. Automatically rotate the camrea to a talking NPC. It's like Netflix!": "플레이어가 앉아 있고 1인칭일 때 대화하는 NPC 쪽으로 카메라를 자동 회전합니다.",
    "Prevent AI NPCs in a traditional dialogue scene from responding automatically.": "기존 대화 장면에 참여 중인 AI NPC의 자동 응답을 막습니다.",
    "Mode Wheel - Switch between chat modes: Standard, Whisper, Director, Spawn NPC, Cheat Mode, Auto Chat, Inject. Hold to cycle modes.": "모드 휠: 일반, 속삭임, 감독, NPC 소환, 치트, 자동 대화, 주입 모드를 전환합니다. 길게 누르면 모드를 순환합니다.",
    "Immediately stop all CHIM AI actions for targeted NPC or all nearby NPCs.": "대상 NPC 또는 근처 모든 NPC의 CHIM AI 행동을 즉시 중단합니다.",
    "Master Wheel - Quick access menu to open any of the 4 wheels: Roleplay, Settings, Mode, or Soulgaze.": "마스터 휠에서 롤플레이, 설정, 모드, 영혼 응시 휠을 빠르게 엽니다.",
    "Auto Activate policy. By default, it applies to non-hostile NPCs whose race allows player dialogue (PC Dialogue = 1). Check this to allow Auto Activate hostile NPCs": "자동 활성화는 기본적으로 플레이어와 대화할 수 있는 비적대 NPC에 적용됩니다. 이 옵션을 켜면 적대 NPC에도 적용합니다.",
    "Auto Activate policy. By default, it applies to non-hostile NPCs whose race allows player dialogue (PC Dialogue = 1). Check this option to allow Auto Activate for all races - including animals like rabbits, deer, foxes, etc. Note: Enabling this may cause instability.": "모든 종족을 자동 활성화 대상으로 포함합니다. 토끼·사슴·여우 같은 동물도 포함되며 불안정해질 수 있습니다.",
    "Enable open microphone mode. Will automatically start recording when it detects voice input above the sensitivity threshold.": "상시 마이크를 켜고 감지 민감도보다 큰 소리가 들어오면 자동으로 녹음합니다.",
    "Voice detection sensitivity for open mic. Higher values require louder voice to trigger recording.": "상시 마이크의 음성 감지 민감도입니다. 값이 높을수록 큰 소리가 필요합니다.",
    "How long to wait (in seconds) after voice stops before ending the recording and processing the speech.": "말이 멈춘 뒤 녹음을 끝내고 처리하기까지 기다리는 시간입니다.",
    "Key to temporarily mute open microphone.": "상시 마이크를 잠시 음소거하는 키입니다.",
    "Enable combat dialogue.": "전투 중 대화를 허용합니다.",
    "When enabled, all AI dialogue will be immediately cancelled when you enter combat (prevents NPCs talking during fights)": "전투가 시작되면 모든 AI 대화를 즉시 취소합니다.",
    "When enabled AI agents in combat will periodically shout taunts/battle cries. Is controlled via Rechat. ": "전투 중 AI 에이전트가 주기적으로 도발이나 함성을 외칩니다. 재대화 기능을 사용합니다.",
    "How often (in seconds) combat barks trigger during active combat. Will automatically trigger an event when combat starts. Default: 30 seconds": "전투 중 외침의 발생 간격입니다. 전투 시작 시 이벤트가 자동으로 발생합니다. 기본값: 30초.",
    "Will Auto Activate (almost) all nearby NPCs.": "근처 NPC 대부분을 자동 활성화합니다.",
    "Remove all active AI agents from the system.": "활성 AI 에이전트를 모두 제거합니다.",
    "Refresh the list of nearby NPCs that can be added to the AI system.": "AI 시스템에 추가할 수 있는 근처 NPC 목록을 새로고침합니다.",
}


def main() -> None:
    if SOURCE is None:
        raise SystemExit("usage: python build_korean_mcm.py <AIAgentMCMConfigScript.psc> [output.psc]")
    text = SOURCE.read_text(encoding="utf-8-sig")
    # Quoted literals only: preserve identifiers, Papyrus API names and comments.
    for english, korean in LABELS.items():
        old = '"' + english + '"'
        if old not in text:
            raise ValueError(f"Upstream changed or missing: {english}")
        text = text.replace(old, '"' + korean + '"')

    # Dynamic prompts are split across Papyrus concatenations.
    dynamic = {
        '"Remove AI agent \'" + _currentAgentNames[i] + "\'?"': '"선택한 NPC \'" + _currentAgentNames[i] + "\'의 설정을 변경할까요?"',
        '"Add AI agent \'" + _nearbyNpcNames[k] + "\'?"': '"선택한 NPC \'" + _nearbyNpcNames[k] + "\'의 설정을 변경할까요?"',
        '"Remove the AI agent \'"': '"AI 에이전트 \'"',
        '"Add the nearby NPC \'"': '"근처 NPC \'"',
        '"\' from the active AI system."': '"\'을(를) 활성 AI 시스템에서 제거합니다."',
        '"\' to the AI system."': '"\'을(를) AI 시스템에 추가합니다."',
    }
    for english, korean in dynamic.items():
        if english not in text:
            raise ValueError(f"Upstream changed or missing dynamic prompt: {english}")
        text = text.replace(english, korean)

    # Key conflict message contains explicit Papyrus newline escapes.
    text = text.replace("This key is already mapped to:\\n'", "이 키는 이미 다음 기능에 지정되어 있습니다:\\n'")
    text = text.replace("Are you sure you want to continue?", "계속할까요?")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8-sig", newline="\r\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
