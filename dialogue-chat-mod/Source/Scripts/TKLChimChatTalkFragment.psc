ScriptName TKLChimChatTalkFragment Extends TopicInfo Hidden

; BEGIN FRAGMENT Fragment_0
Function Fragment_0(ObjectReference akSpeakerRef)
    Actor akSpeaker = akSpeakerRef as Actor
    Debug.Trace("[TKLChimChat] talk option picked, speaker=" + akSpeaker)
    TKLChimChatQuest.RequestChat(akSpeaker)
EndFunction
; END FRAGMENT

TKLChimChatController Property TKLChimChatQuest Auto
