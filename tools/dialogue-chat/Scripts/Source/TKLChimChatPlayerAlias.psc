Scriptname TKLChimChatPlayerAlias extends ReferenceAlias
{Releases temporary CHIM agents left behind when the player moves on.}

TKLChimChatController Property Controller Auto

Event OnPlayerLoadGame()
	Controller.ReleaseAbsentAgents()
EndEvent

Event OnLocationChange(Location akOldLoc, Location akNewLoc)
	Controller.ReleaseAbsentAgents()
EndEvent
