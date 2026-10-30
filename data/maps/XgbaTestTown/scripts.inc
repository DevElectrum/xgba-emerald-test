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
	.string "The original LITTLEROOT TOWN is\\n"
	.string "one experiment away. Going back!$"

XgbaTestTown_Text_Witness:
	.string "You're in XGBA TEST TOWN!\\n"
	.string "This map lives beyond 32 MB!$"
