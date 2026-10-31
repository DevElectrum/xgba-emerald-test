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


XgbaE4_EventScript_AdvanceProgress::
	lock
	faceplayer
	addvar VAR_XGBA_E4_PROGRESS, 1
	goto_if_set FLAG_XGBA_E4_FIRST_VISIT, XgbaE4_EventScript_ProgressAlreadyVisited
	setflag FLAG_XGBA_E4_FIRST_VISIT
	buffernumberstring STR_VAR_1, VAR_XGBA_WORLD_ID
	buffernumberstring STR_VAR_2, VAR_XGBA_E4_PROGRESS
	msgbox XgbaE4_Text_FirstProgress, MSGBOX_DEFAULT
	release
	end

XgbaE4_EventScript_ProgressAlreadyVisited:
	buffernumberstring STR_VAR_1, VAR_XGBA_WORLD_ID
	buffernumberstring STR_VAR_2, VAR_XGBA_E4_PROGRESS
	msgbox XgbaE4_Text_AdvancedProgress, MSGBOX_DEFAULT
	release
	end

XgbaE4_EventScript_ReadProgress::
	lock
	faceplayer
	buffernumberstring STR_VAR_1, VAR_XGBA_WORLD_ID
	buffernumberstring STR_VAR_2, VAR_XGBA_E4_PROGRESS
	goto_if_set FLAG_XGBA_E4_FIRST_VISIT, XgbaE4_EventScript_ProgressReadVisited
	msgbox XgbaE4_Text_UnvisitedProgress, MSGBOX_DEFAULT
	release
	end

XgbaE4_EventScript_ProgressReadVisited:
	msgbox XgbaE4_Text_VisitedProgress, MSGBOX_DEFAULT
	release
	end

XgbaE4_Text_FirstProgress:
	.string "World {STR_VAR_1}: progress {STR_VAR_2}!\n"
	.string "This world's flag is now set.$"

XgbaE4_Text_AdvancedProgress:
	.string "World {STR_VAR_1}: progress {STR_VAR_2}!\n"
	.string "Your flag was already set.$"

XgbaE4_Text_UnvisitedProgress:
	.string "World {STR_VAR_1}: progress {STR_VAR_2}.\n"
	.string "Local event flag: CLEAR.$"

XgbaE4_Text_VisitedProgress:
	.string "World {STR_VAR_1}: progress {STR_VAR_2}.\n"
	.string "Local event flag: SET.$"

XgbaE5_EventScript_Snapshot::
	lock
	faceplayer
	special XgbaE5SpecialSnapshot
	compare VAR_RESULT, 1
	goto_if_eq XgbaE5_EventScript_SnapshotSuccess
	compare VAR_RESULT, 0
	goto_if_eq XgbaE5_EventScript_Unsupported
	msgbox XgbaE5_Text_WriteFailed, MSGBOX_DEFAULT
	release
	end

XgbaE5_EventScript_SnapshotSuccess:
	msgbox XgbaE5_Text_SnapshotSuccess, MSGBOX_DEFAULT
	release
	end

XgbaE5_EventScript_Audit::
	lock
	faceplayer
	special XgbaE5SpecialAudit
	compare VAR_RESULT, 1
	goto_if_eq XgbaE5_EventScript_AuditSuccess
	compare VAR_RESULT, 0
	goto_if_eq XgbaE5_EventScript_Unsupported
	compare VAR_RESULT, 2
	goto_if_eq XgbaE5_EventScript_AuditEmpty
	compare VAR_RESULT, 3
	goto_if_eq XgbaE5_EventScript_AuditMismatch
	msgbox XgbaE5_Text_AuditCorrupt, MSGBOX_DEFAULT
	release
	end

XgbaE5_EventScript_AuditSuccess:
	msgbox XgbaE5_Text_AuditSuccess, MSGBOX_DEFAULT
	release
	end

XgbaE5_EventScript_AuditEmpty:
	msgbox XgbaE5_Text_AuditEmpty, MSGBOX_DEFAULT
	release
	end

XgbaE5_EventScript_AuditMismatch:
	msgbox XgbaE5_Text_AuditMismatch, MSGBOX_DEFAULT
	release
	end

XgbaE5_EventScript_Unsupported:
	msgbox XgbaE5_Text_Unsupported, MSGBOX_DEFAULT
	release
	end

XgbaE5_Text_SnapshotSuccess:
	.string "E5: Wrote this world's event bank!\n"
	.string "Use the next auditor after saving.$"

XgbaE5_Text_AuditSuccess:
	.string "E5: Persistent event bank matches!\n"
	.string "Our new save window works.$"

XgbaE5_Text_AuditEmpty:
	.string "E5: No snapshot for this world.\n"
	.string "Talk to the writer first.$"

XgbaE5_Text_AuditMismatch:
	.string "E5: Snapshot differs from RAM.\n"
	.string "Did you change progress since then?$"

XgbaE5_Text_AuditCorrupt:
	.string "E5: Cannot verify saved record.\n"
	.string "No data was overwritten.$"

XgbaE5_Text_WriteFailed:
	.string "E5: Record write refused.\n"
	.string "Check the save-format integrity.$"

XgbaE5_Text_Unsupported:
	.string "E5 expanded save is unavailable!\n"
	.string "No extra-memory write occurred.$"
