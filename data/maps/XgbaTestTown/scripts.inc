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
	msgbox XgbaTestTown_Text_ToHoenn2, MSGBOX_DEFAULT
	closemessage
	warp MAP_XGBA2_LITTLEROOT_TOWN, 13, 12
	waitstate
	release
	end

Xgba2Littleroot_EventScript_Return::
	lock
	faceplayer
	msgbox Xgba2Littleroot_Text_Return, MSGBOX_DEFAULT
	closemessage
	warp MAP_XGBA_TEST_TOWN, 15, 12
	waitstate
	release
	end

XgbaTestTown_Text_ToHoenn2:
	.string "Hoenn has a second address!\n"
	.string "Welcome to WORLD TWO!$"

Xgba2Littleroot_Text_Return:
	.string "This Hoenn is an independent\n"
	.string "map network. Back to the lab!$"
