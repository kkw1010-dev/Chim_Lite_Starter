Scriptname TKLChimChatController extends Quest
{CHIM Lite dialogue chat. An NPC dialogue option opens CHIM's text entry for
that NPC, first making the NPC a temporary AI agent when it is not one
already. Temporary agents are released by their own dialogue option and,
automatically, when the player changes location or loads a game while they
are no longer nearby. Also removes the Numpad 0 text-chat key that CHIM binds
at game start, so CHIM has no hotkeys at all.}

AIAgentPapyrusFunctions Property ChimControl Auto
{CHIM's key-handling quest script, AIAgent.esp 0093FC.}
Faction Property TempAgentFaction Auto
{Marks NPCs this mod made agents; the release option is conditioned on it.}
Actor Property PlayerRef Auto

string Property TempListKey = "TKLChimChat.TempAgents" AutoReadOnly
int Property ChimDefaultTextKey = 82 AutoReadOnly ; 0x52, Numpad 0, bound in AIAgentPapyrusFunctions.OnInit
float Property NearbyDistance = 4096.0 AutoReadOnly

Actor pendingChat = None
bool textKeyCleared = false

Event OnInit()
	; One line per failure mode, so a single Papyrus log answers "did it load".
	Debug.Trace("[TKLChimChat] quest started; CHIM control=" + ChimControl + " faction=" + TempAgentFaction)
	if !ChimControl || !TempAgentFaction
		Debug.Trace("[TKLChimChat] ERROR: a property is unbound; the dialogue option cannot work", 2)
	endif
	; CHIM binds Numpad 0 in its own OnInit; wait until that has surely run.
	RegisterForSingleUpdate(5.0)
EndEvent

Event OnUpdate()
	if !textKeyCleared
		textKeyCleared = true
		ChimControl.removeBinding(ChimDefaultTextKey)
		Debug.Trace("[TKLChimChat] removed CHIM's default text-chat key (Numpad 0)")
	endif
	if pendingChat
		; The dialogue menu does not pause the game, so this can fire while it is
		; still closing. The text entry must open after it, with the NPC in view.
		if UI.IsMenuOpen("Dialogue Menu")
			RegisterForSingleUpdate(0.3)
			return
		endif
		Actor target = pendingChat
		pendingChat = None
		OpenChat(target)
	endif
EndEvent

; Called by the "talk" dialogue option.
Function RequestChat(Actor akTarget)
	if !akTarget || akTarget == PlayerRef
		return
	endif
	if !IsAgent(akTarget)
		AIAgentFunctions.setDrivenByAIA(akTarget, false)
		if !IsAgent(akTarget)
			; CHIM may register the agent a moment later; say so rather than fail silently.
			Debug.Trace("[TKLChimChat] WARNING: " + akTarget.GetDisplayName() + " is not listed as a CHIM agent right after setDrivenByAIA", 1)
		endif
		akTarget.AddToFaction(TempAgentFaction)
		StorageUtil.FormListAdd(None, TempListKey, akTarget, false)
		Debug.Trace("[TKLChimChat] temporary agent added: " + akTarget.GetDisplayName() + " " + akTarget)
	endif
	pendingChat = akTarget
	RegisterForSingleUpdate(0.3)
EndFunction

Function OpenChat(Actor akTarget)
	UIExtensions.OpenMenu("UITextEntryMenu")
	string text = UIExtensions.GetMenuResultString("UITextEntryMenu")
	if text != ""
		; CHIM addresses typed input to the NPC under the crosshair, which is the
		; NPC the player was just talking to.
		AIAgentFunctions.sendMessage(text, "")
		Debug.Trace("[TKLChimChat] sent chat to " + akTarget.GetDisplayName())
	endif
EndFunction

; Called by the "end" dialogue option, which only temporary agents offer.
Function ReleaseAgent(Actor akTarget)
	if !akTarget
		return
	endif
	if IsAgent(akTarget)
		; setDrivenByAIA toggles: on an agent it removes the agent.
		AIAgentFunctions.setDrivenByAIA(akTarget, false)
	endif
	akTarget.RemoveFromFaction(TempAgentFaction)
	StorageUtil.FormListRemove(None, TempListKey, akTarget, true)
	Debug.Trace("[TKLChimChat] temporary agent released: " + akTarget.GetDisplayName() + " " + akTarget)
EndFunction

; Releases every temporary agent that is gone, dead or far away. Runs on
; location change and game load (player alias), never on a timer.
Function ReleaseAbsentAgents()
	int i = StorageUtil.FormListCount(None, TempListKey)
	int released = 0
	while i > 0
		i -= 1
		Actor a = StorageUtil.FormListGet(None, TempListKey, i) as Actor
		if !a
			StorageUtil.FormListRemoveAt(None, TempListKey, i)
		elseif a.IsDead() || !a.Is3DLoaded() || a.GetDistance(PlayerRef) > NearbyDistance
			ReleaseAgent(a)
			released += 1
		endif
	endwhile
	if released > 0
		Debug.Trace("[TKLChimChat] released " + released + " absent temporary agent(s); " + StorageUtil.FormListCount(None, TempListKey) + " remain")
	endif
EndFunction

bool Function IsAgent(Actor akTarget)
	Actor[] agents = AIAgentFunctions.findAllAgents()
	int i = agents.Length
	while i > 0
		i -= 1
		if agents[i] == akTarget
			return true
		endif
	endwhile
	return false
EndFunction
