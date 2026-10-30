XgbaTestTown_MapScripts::
	.byte 0

XgbaTestTown_EventScript_Return::
	lock
	faceplayer
	msgbox XgbaTestTown_Text_Return, MSGBOX_DEFAULT
	closemessage
	warp MAP_LITTLEROOT_TOWN, 13, 12
	waitstate
	release
	end

XgbaTestTown_EventScript_Witness::
	msgbox XgbaTestTown_Text_Witness, MSGBOX_NPC
	end

XgbaTestTown_Text_Return:
	.string "The original LITTLEROOT TOWN is\n"
	.string "one experiment away. Going back!$"

XgbaTestTown_Text_Witness:
	.string "You're in XGBA TEST TOWN!\n"
	.string "This map lives beyond 32 MB!$"


Xgba2Neutral_MapScripts::
	.byte 0

XgbaTestTown_EventScript_ToHoenn2::
	lock
	faceplayer
	compare VAR_XGBA_WORLD_ID, 2
	goto_if_ge XgbaTestTown_EventScript_EnterSelectedWorld
	setvar VAR_XGBA_WORLD_ID, 2
XgbaTestTown_EventScript_EnterSelectedWorld:
	buffernumberstring STR_VAR_1, VAR_XGBA_WORLD_ID
	msgbox XgbaTestTown_Text_ToHoenn2, MSGBOX_DEFAULT
	closemessage
	warp MAP_XGBA2_LITTLEROOT_TOWN, 13, 12
	waitstate
	release
	end

Xgba2Littleroot_EventScript_Return::
	lock
	faceplayer
	buffernumberstring STR_VAR_1, VAR_XGBA_WORLD_ID
	msgbox Xgba2Littleroot_Text_Return, MSGBOX_DEFAULT
	closemessage
	warp MAP_XGBA_TEST_TOWN, 15, 12
	waitstate
	release
	end

XgbaTestTown_Text_ToHoenn2:
	.string "Hoenn has a second address!\n"
	.string "Destination: WORLD {STR_VAR_1}!$"

Xgba2Littleroot_Text_Return:
	.string "World {STR_VAR_1} reporting in!\n"
	.string "Back to the lab!$"


XgbaTestTown_EventScript_NextWorld::
	lock
	faceplayer
	compare VAR_XGBA_WORLD_ID, 2
	goto_if_lt XgbaTestTown_EventScript_ResetWorld
	compare VAR_XGBA_WORLD_ID, 20
	goto_if_ge XgbaTestTown_EventScript_ResetWorld
	addvar VAR_XGBA_WORLD_ID, 1
	goto XgbaTestTown_EventScript_ShowSelectedWorld

XgbaTestTown_EventScript_ResetWorld:
	setvar VAR_XGBA_WORLD_ID, 2

XgbaTestTown_EventScript_ShowSelectedWorld:
	buffernumberstring STR_VAR_1, VAR_XGBA_WORLD_ID
	msgbox XgbaTestTown_Text_NextWorld, MSGBOX_DEFAULT
	release
	end

XgbaTestTown_Text_NextWorld:
	.string "Destination set: WORLD {STR_VAR_1}!\n"
	.string "Talk to my colleague to warp.$"
