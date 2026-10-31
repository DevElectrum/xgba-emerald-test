# XGBA Emerald experiment: living Astra handoff

## 2026-10-31: USER FOUND E6 HOENN 20 STORY NPC BUG; PATCH COMMITTED

- Screenshot of Route 101 World 20 shows Professor Birch and Zigzagoon visible, bag nearby, but Birch does not talk; user also reports child in May's house walking outside right-hand wall. This is **NOT** intended gameplay. Root cause from source: E6 bulk restoration `f09e785c` only copied normal `object_events` and background interactions while intentionally zeroing `coord_events` and assigning `shared_scripts_map = Xgba2Neutral`. Birch's rescue actor has `script: "0x0"` in the original and normally depends on `Route101_OnTransition` plus coordinate trigger `Route101_EventScript_StartBirchRescue`; it cannot be started by talking directly to Birch.
- **Patch 1** `077c6aae`: `tools/xgba_generate_e2.py` now restores native map scripts + coordinate events specifically for `Route101`, `LittlerootTown_MaysHouse_1F`, and `LittlerootTown_BrendansHouse_1F`. The May rival sibling's wandering movement was changed to fixed face-down to avoid clipping near east wall. This does NOT globally restore story scripts throughout Hoenn.
- **Patch 2** `102a0e87`: `src/overworld.c:SetWarpDestination` now redirects original Hoenn story-script destinations to clone map groups (+34) only when the *current map* is a cloned group and world selector is 2–20. It excludes `MAP_XGBA_TEST_TOWN` to allow exiting to the lab. Original groups number 0..33, cloned groups 34..67. Scripted warps must not accidentally send users to original World 1.
- **Latest CI** [run 41184903637](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41184903637) for `102a0e87`: pending at this checkpoint. Earlier source `f09e785c` passed game build [41183201138](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41183201138). **No human verification of this bug fix yet.** Do not state Birch rescue/house movement is fixed in gameplay until user confirms.
- Screenshot window title identified XGBA as `0.11-xgba/e5-save-expansion-...` even though the user launched E6. The user previously ran a `cmake --build` without `cmake -S ... -B ...` reconfiguration after switching branches. Likely stale CMake project-version metadata; verify binary and branch before claiming E6 emulator build is active. The user's E6 auditor appears to function, so version title alone does not definitively prove binary core is old.
- Next: check CI for both patches. Give user **at most two commands** for ROM-only update/rebuild and Qt launch, or one command to reconfigure/rebuild emulator and Emerald and one to launch. Preserve original E5/E6 save! User should test Route 101 by approaching scene trigger and interacting with Birch's bag, not expecting conversation from the scriptless Birch actor. Observe rival house clipping, and report issues. If trigger remains wrong, investigate initial `VAR_ROUTE101_STATE` and World 20 E6 snapshot initialization, before altering unrelated maps.
- E6's core goal still includes full 20-world story/party isolation and 112-box streaming, neither globally verified. Keep updating handoffs periodically; user wants speedy progress and modest testing.


## 2026-10-31: EXTRA E6 NPC RESTORATION + CI update
**LATEST VERIFIED CI PASS:** [41183201138](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41183201138) completed SUCCESS for `f09e785c`: both native 64 MiB E6 ROM build (including cloned NPC restoration) and Python E6 format tests. Paired emulator E6 CI [41182582688](https://github.com/DevElectrum/xgba/actions/runs/41182582688) also SUCCESS. Next user action is copy-only E5→E6 migration and a first integrated World3/20 smoke test; no E6 gameplay has yet passed. 


- E6 world-switch engine (`src/xgba_e6.c`, `src/save.c`, `data/maps/XgbaTestTown/scripts.inc`) **COMPILED** with `make e6` and Python format tests passed: https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41183020017 . Still **NO USER GAMEPLAY PASS**.
- Commit `f09e785ccf630f83b4778b29f798ce1a17875331`: `tools/xgba_generate_e2.py` now retains normal object events/trainers and BG interactables in cloned maps, while suppressing hazardous coordinate/script callbacks; cloned Littleroot keeps the five E4/E6/return lab NPCs. Caveat: `shared_events_map` indirection unresolved and NPCs may have original-world script warp destinations. New ROM CI: https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41183201138 (last checked IN PROGRESS). Do not call full stories playable.
- The ambitious **112-box ×20 worlds / 2240-box** page-streaming follow-up architecture was drafted in `docs/XGBA_E6_PLAN.md` at commit `3c3508eb`. This is design only; native PC currently remains 14 boxes and no page-bank code exists.
- Next: inspect NPC CI, address failures; then perform one E6 integrated gameplay smoke test with a **new 16 MiB E6 save copy**, preserving E5. If test shows breakage, patch on E6 feature branches and update handoffs. User wants 3 commands and speed, not 100 tests.


## 2026-10-31: E6 EXECUTION checkpoint; feature branches and real code

**The earlier E6 "not yet implemented" statements in this file are historical. E6 IS NOW IN PROGRESS.** Read `docs/XGBA_E6_PLAN.md` first. User wants **Regieleki speed**, no exhaustive QA, but explicit copies of accepted E5 save and frequent handoff commits.

- **Branches created:** game `DevElectrum/xgba-emerald-test@xgba/e6-world-virtualization` from accepted E5; emulator `DevElectrum/xgba@xgba/e6-large-save` from accepted E5. No edits to masters or `DevElectrum/grand-anthology`.
- **Emulator done + verified:** versioned 16 MiB save extension (0x0F) with v2 magic, dual CRC32 headers, E5 compatibility retained. CI **success** https://github.com/DevElectrum/xgba/actions/runs/41182582688.
- **Game source created:** `tools/xgba_pack_e3.py` supports `--e6-save`, `Makefile` adds `make e6` for `xgba-emerald-e6.gba` (64 MiB revision E6). `tools/xgba_e6_save.py` safe `init` from native E4 or E5 to a distinct 16 MiB E6 save, preserving native flash / legacy E5 world records / RTC trailer. Unit tests `tests/test_xgba_e6_save.py` (53,380-byte record, dual-copy fallback, old record preservation) are GREEN on current game E6 workflow; game ROM native CI was running during this checkpoint. `docs/XGBA_E6_PLAN.md` gives full format and implementation details.
- **Game C implemented but NOT user tested:** `src/xgba_e6.c` / `include/xgba_e6.h` byte-stream the 15,752-byte SaveBlock1, 3,884-byte SaveBlock2, and 33,744-byte PokemonStorage = 53,380 bytes per world into independent two-slot 64 KiB E6 records from file offset 0x100000. CRC verified. `data/specials.inc` and `data/maps/XgbaTestTown/scripts.inc` change known accessible E5 snapshot/audit NPCs to report E6 full records and automate checkpoint on exit/restore on entry. `src/save.c` refreshes E6 record on normal native saves inside a cloned world. Field transition restore skips SaveBlock1 navigation offset 0..0x233 and retains the chosen world ID, then refreshes party/bag. First visit seeded from preserved baseline World1 record. This is high-risk and may require rapid gameplay bug fixes.
- **Important remaining:** Game ROM CI success and joint XGBA runtime NOT YET established for latest C changes. There are still only 14 native boxes, no 100-box GUI, cloned maps still have suppressed story NPCs/events. An E6 bank can hold full existing PokémonStorage; that is *not* a massive box system. Preserve good E5 saves and don't ask the user to repeat previously accepted E5 tests.
- **User test UX:** nearly always three commands: update/build local emulator and game E6 branches; safe copy-only save migration `python3 tools/xgba_e6_save.py init xgba-emerald-e5.sav xgba-emerald-e6.sav`; launch `~/Projects/xgba/build-xgba-gui/qt/mgba-qt ~/Projects/xgba-emerald-test/xgba-emerald-e6.gba`. Save copies never overwrite.
- **Next action:** review `.github/workflows/xgba-e6.yml` run results for latest runtime C changes and fix compiler errors. Then request one World20/World3 switching smoke test and record actual results, not assumptions. Update both living handoffs and agent guidance again at the next substantial milestone.


## CURRENT NEXT ASTRA CHECKPOINT: 2026-10-31 (E6 planned, no E6 code started)

**Immediate instruction:** Read [`docs/XGBA_E6_PLAN.md`](XGBA_E6_PLAN.md) and [`AGENTS.md`](../AGENTS.md), plus companion emulator handoff and AGENTS. User explicitly rejected conservative flags-only E6 in favor of an ambitious, fast-moving E6. **Regieleki: speed is god.** This is a passion project: take large steps, run minimal CI and selected gameplay smoke tests, use backups, and accept temporary breakage rather than designing a huge QA bureaucracy.

**Current verified work:** accepted E3 geography (20 selectable Hoenn layouts), accepted E4 per-world 16-byte event state, and **user-tested E5 1 MiB extended-save snapshot persistence for World 3 and 20 across normal save, full XGBA shutdown and reload**. They should NOT have to repeat those tests. E5 selection-menu QoL change implemented in game branch: Test Town (18,12) opens a scrolling list Worlds 2..20; neighboring (16,12) warps. No explicit user confirmation of that newer menu's runtime behavior yet.

**E6 planned scope (NOT IMPLEMENTED):** increase emulator file-backed E5 save to a **versioned ~16 MiB E6** format, independent world-local `SaveBlock1`, `SaveBlock2`, PC storage, parties, inventory, story flags, trainer state and safe world transitions; restore actual events/NPCs/story in cloned Hoenn; attempt **100 PC boxes per world** as aggressive stretch. Avoid claiming mere disk growth automatically fixes box UI or 95%-full EWRAM. Need deliberate shared/global metadata, migration from E5, streamed records and safe warp boundary. E6 is a combined large milestone, not flags-only E6 followed by later storage milestones.

**Next steps:** (1) inspect current HEAD, code and CI; (2) when starting implementation, branch the **game** `xgba/e6-world-virtualization` from `xgba/e5-expanded-save` and the **emulator** `xgba/e6-large-save` from `xgba/e5-save-expansion` (names proposed, branches do not yet exist); (3) implement expanded file-backed save + migration first or in parallel with world-state serialization, then restored maps and big boxes, iterating rapidly. Protect E4/E5 savenames and `master`; never touch `DevElectrum/grand-anthology`.

**Repository changes made during this handoff update:** E6 strategy doc added `8099a85a`; game `AGENTS.md` updated `060bee38`; emulator `AGENTS.md` created on E5 branch `1a66d9a0`. These are **documentation-only** changes; no new emulator/game runtime E6 code was written, and no new E6 gameplay tests run in this checkpoint.

**Mandatory continuity rule:** at every meaningful coding milestone/CI result/architecture change/blocker, *commit an updated handoff before ending or exhausting chat context*. Update both repos' `AGENTS.md` and handoffs when instructions/interfaces change. Record exact branch and commit, changed files, tests with links and observed status, outstanding bugs, and concrete next action. The user wants ~three terminal commands only (update/build, optional save copy, launch Qt GUI). GitHub updates are not yet present in the user's local Nyx repos until `git pull`.


## 2026-10-31: Test Town world selector replaced with a native scrolling menu

User asked to replace the repetitive (18,12) world-ID cycling NPC (World 2 through World 20) with a Pokémart-style selection list. Implemented on `xgba/e5-expanded-save` in `include/constants/field_specials.h` (new `SCROLL_MULTI_XGBA_WORLD_SELECT = 13`, capacity increased from 16 to 20), `src/field_specials.c` (19 static WORLD 2–20 labels plus Exit; six visible rows, scroll arrows, current destination preselected), and `data/maps/XgbaTestTown/scripts.inc` (cancel/B leaves `VAR_XGBA_WORLD_ID` unchanged; selecting index 0–18 copies index+2 into the existing world ID; existing (16,12) warp scientist unchanged). No emulator or save-format modifications; existing E5 `.sav` should be reused. User has not yet verified this new menu in gameplay. The goal is one scrolling menu rather than up to 19 separate dialogs. Updated instructions and notes in `docs/XGBA_E5_README.md`.

## 2026-10-31: E5 LIVE GAMEPLAY PERSISTENCE ACCEPTED

**USER CONFIRMED BOTH PHASES PASSED.** With the E5 Qt XGBA build and the separately initialized `xgba-emerald-e5.sav`, the user visited World 20 and World 3. In each world, the E5 writer successfully recorded the existing 16-byte E4 prototype event state and the E5 auditor reported a match. Returning between worlds preserved each independent E5 snapshot. After a normal in-game save, complete emulator shutdown, and reload, both world's E5 auditors again reported matches. This is direct user verification of guest 0x0F writes surviving the emulator's save-file cycle.

The final reachable E5 NPC locations in cloned Littleroot are **writer (14,15)** and **auditor (16,15)**. The original (20,12)/(22,12) placements were obstructed by trees and have been fixed in the generator. The user confirmed the replacement NPCs are reachable.

**Accepted scope:** E5 opt-in 1 MiB save bridge and independent 16-byte snapshot read/write/restart proof for Worlds 3/20. **Not accepted:** full world-local trainer/story data, Pokémon PC box expansion, maximal 20,448-byte record stress tests, game-level torn-write recovery, all-world coverage, and end-to-end RTC compatibility. The original E4 save must remain backed up. Do not ask the user to repeat this already successful acceptance test.

User workflow preference: **three commands whenever practical**: (1) update repositories/build, (2) create or copy save only if applicable, (3) run the Qt `mgba-qt` with the new ROM. For ROM-only patches, give two commands: update/rebuild, launch.

Next: choose the next design milestone. The 20 KiB E5 per-world payload cannot accommodate a vanilla 33,744-byte `PokemonStorage` wholesale; do not claim full Pokémon boxes are supported. Plan larger or differently packed world/PC storage separately. Keep `DevElectrum/grand-anthology` and both `master` branches untouched.

- **2026-10-31 E5 integration gate update:** E5 game native build succeeded: https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41172674059 . E5 64 MiB ROM, header/checksum validation and host-format tests succeeded: https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41172674073 . E5 emulator CTest persistence success: https://github.com/DevElectrum/xgba/actions/runs/41172551382 . All are code/format proof, not in-game acceptance. Next action: build emulator + E5 ROM locally, use host `init` to convert a COPY of the E4 save, verify NPCs at World 20/3 (20,12 writer; 22,12 auditor), save/close/reopen, and check `xgba_e5_save.py inspect`. Protect originals.

## 2026-10-31: E5 game-side runtime integration started

- Active `xgba/e5-expanded-save` now contains `include/xgba_e5.h` and `src/xgba_e5.c`: strict cart+superblock probe, bytewise `0x0F` read/write, 20-world dual-slot format compatible with `tools/xgba_e5_save.py`, header/payload CRC32 validation, newest-valid-copy selection, and inactive-slot writes with magic last.
- E5 snapshot/audit specials are appended to `data/specials.inc`; event scripts live in `data/maps/XgbaTestTown/scripts.inc`; `tools/xgba_generate_e2.py` generates new NPCs at cloned Littleroot (14,15) writer and (16,15) auditor. They snapshot/check the existing 16-byte E4 world-event prototype, **not** complete world progression or PC boxes.
- The first native agbcc link job found that libc `memcmp` is unavailable in this build. Fixed in `83c63f99ffd750c9825e8b845e3d4d2274065d0c` with explicit byte comparison. The latest ROM build/check must pass before asking the user to test; earlier green host-format-only Python jobs do not verify the new game C code.
- Emulator E5 unit test is green: https://github.com/DevElectrum/xgba/actions/runs/41172551382, including save-file unload/reload persistence, redundant superblock recovery, and fail-closed behavior.
- Preserve accepted E4 save/ROM, create E5 **copies** with `tools/xgba_e5_save.py init`, and keep all changes on E5 branches. Details and proposed gameplay acceptance procedure in `docs/XGBA_E5_README.md`. Nothing merged to master or Grand Anthology.

Updated: 2026-10-30
Status: E1/E2/E3 accepted, E4 **fully accepted in real gameplay with independent World 3 and World 20 records surviving save/restart**. E5 experimental storage expansion STARTED on `xgba/e5-expanded-save` (game) and `xgba/e5-save-expansion` (emulator). Offline 1 MiB save format / CRC fallback tests and emulator baseline CI pass; E5 game runtime snapshot I/O and user testing NOT done.

## Read this first

- Canonical ROM test repo: `DevElectrum/xgba-emerald-test`; https://github.com/DevElectrum/xgba-emerald-test
- The upstream fork source is `pret/pokeemerald`, default branch `master`. Preserve upstream licensing, history and attribution.
- Accepted E4 prototype branch: `xgba/e4-world-state`, derived from accepted E3 branch `xgba/e3-20-worlds`. [Draft PR #5](https://github.com/DevElectrum/xgba-emerald-test/pull/5). Preserve E1/E2/E3 baselines and original master.
- Emulator repo: `DevElectrum/xgba`. The verified P0 core branch is `xgba/p0-validation-20261030`; initial emulator validation draft PR #2: https://github.com/DevElectrum/xgba/pull/2
- Emulator validation details: https://github.com/DevElectrum/xgba/blob/xgba/p0-validation-20261030/docs/XGBA_P0_VALIDATION_2026-10-30.md
- **NEVER edit `DevElectrum/grand-anthology`** in this experiment.
- User requests periodic updates to this handoff after every meaningful successful milestone or change of plan, so later Astras can continue without repeated questions.

## Why

XGBA forks mGBA with an opt-in `XGBA256` cartridge tag in the GBA header bytes `0xB5..0xBB`. It maps up to 256 MiB ROM data to CPU address `0x10000000..0x1FFFFFFF`. File offset `0x02000000` (32 MiB) maps to `0x12000000`. The original cartridge `0x08000000` window remains accessible. Tagged ROMs over 32 MiB need an updated GBA header complement checksum.

XGBA's validated core tests passed, but actual Emerald gameplay, audio/video/input, expanded-ROM cheat/patch alias behavior, frontend runtime, and Android are **not** yet tested. The first ROM work must use normal game-side pointers, not emulator-side patching or cheats.

## E0 acceptance gates

1. Build plain `pokeemerald.gba` and `pokeemerald.elf` reproducibly from this fork.
2. Build a 64 MiB tagged `xgba-emerald-e0.gba` from those outputs, without checking ROM binaries into Git.
3. Copy Littleroot Town's actual map layout bytes to an address beyond 32 MiB, patch the corresponding `LittlerootTown_Layout` map-pointer field in the original ROM, preserve other descriptor fields, tag header, recalculate header checksum.
4. Verify from the output bytes that the new map pointer equals `0x12000000` (or configured aligned address), the expanded payload exactly matches `data/layouts/LittlerootTown/map.bin`, and the original input ROM was not modified.
5. Boot and navigate the game interactively **in the validated XGBA emulator**, enter Littleroot Town, move/warp/trigger an event and save/reload. These interactive actions must be explicitly reported as human/manual until performed.
6. Compare conventional Emerald boot against patched Emerald. Neither a synthetic test nor a successful compiler alone proves real map compatibility.

The first E0 is **relocation** of the existing Littleroot map layout, not yet a second separately addressable map. A separate cloned map and later twenty-Hoenn experiments come next.

## Design

- Keep pret's unmodified default linker output under 32 MiB. Use a Python stdlib postprocessor to emit an expanded ROM, so no mass linker rewrite is required for this gate.
- Locate linker symbols `LittlerootTown_Layout` and `LittlerootTown_Layout_Blockdata` from `arm-none-eabi-nm --defined-only pokeemerald.elf`.
- In `struct MapLayout` (see `include/global.fieldmap.h`), the `const u16 *map` field is byte offset **12** of the layout descriptor. Confirm its existing word points at `LittlerootTown_Layout_Blockdata` before patching. Abort if any invariant mismatches.
- Read the `data/layouts/LittlerootTown/map.bin` file, confirm its contents match the ROM bytes at the old pointer, then copy it into the expanded region and patch descriptor to its XGBA CPU address.
- Use `XGBA256` marker and refresh GBA header complement at `0xBD`; verify a 64 MiB exact output.
- Note: `pret/pokeemerald` has 518 map definitions, 441 layouts, and 34 groups. 20 copies of raw tile-layout data would consume ~12.4 MiB; asset stress and true 256 MiB access are separate goals.
- Map group/number are byte-sized; for twenty complete worlds, likely add a separate world ID and dynamic map resolution instead of multiplying 34 groups by 20.

## Verified on 2026-10-30

- Working branch `xgba/e0-expanded-layout`; initial tooling commit `b38f7bd45226f95b8b47423dda47c8c72ffb476e`.
- [Actions run #1](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41017521459): **SUCCESS**; toolchain installation, original Emerald compilation, Python syntax check, 64 MiB XGBA packer, static ROM-integrity re-verification, and size checks all passed.
- Build logged ordinary Emerald ROM usage `14,929,764` bytes before expansion, within the 32 MiB conventional address space.
- Generated XGBA test ROM: `67,108,864` bytes (64 MiB); Littleroot tile-layout pointer `0x12000000`; payload `800` bytes; original file untouched. This ROM was generated on CI runner and deliberately **not** uploaded as an artifact or committed.
- Build is a static mapping proof, **not** proof that the emulator can boot Emerald or render the map on screen.
- A dedicated `.github/workflows/xgba-e0.yml` builds and validates E0; docs-only pushes should skip unnecessary CI once path-filter change applies.
- Read `docs/XGBA_E0_README.md` for exact local build/verify commands.

## Local Nyx/P​​op!_OS validation reported by user (2026-10-30)

- User locally executed a normal `pokeemerald` build and `tools/xgba_pack_emerald.py pack` / `verify` in `~/Projects/xgba-emerald-test`.
- The pasted console output shows successfully generated `pokeemerald.gba`, `pokeemerald.elf` and `xgba-emerald-e0.gba`. The packer wrote exactly **67,108,864** bytes and printed `Verified XGBA Emerald` twice, confirming Littleroot map data relocated to `0x12000000`.
- Conventional Emerald ROM linker footprint was **14,929,764 bytes**, as also seen in CI. This confirms build/ROM integrity on the user's machine, **not** gameplay.
- The remaining E0 gate is launch of **the XGBA validation branch's SDL frontend**, not regular mGBA, and verifying the game from intro through Littleroot, warps, events, save and reload.

## User-confirmed gameplay and mandatory turbo requirement (2026-10-30)

- User built `xgba-emerald-e0.gba` locally and then reported that it **works fine** in their XGBA emulator. The 64 MiB ROM and relocated Littleroot layout have therefore passed a user-reported *initial interactive smoke test*. Do **not** infer that every listed warp/event/save/reload test has been explicitly completed.
- User explicitly requires fast-forward in XGBA. The prior SDL build was unsatisfactory because turbo was ineffective. This is a **mandatory acceptance gate for any future emulator build/recommendation**.
- Emulator fix in progress on `DevElectrum/xgba` branch `xgba/p1-fast-forward`: removes software and OpenGL renderer VSync and prioritizes the hold-Tab turbo key; verify CI and actual measured speed on Nyx before saying fixed.
- Primary emulator handoff: https://github.com/DevElectrum/xgba/blob/xgba/p1-fast-forward/docs/NEXT_ASTRA_HANDOFF.md

## E5 start: audited save sectors and separate 1 MiB save backend (2026-10-30)

**User told us to start E5 while they sleep. No user action/commands are needed yet. Do NOT promise background progress beyond what has actually been committed.**

- **Important audit**: `src/save.c`, `include/save.h` show all 32 standard Emerald 4KiB flash sectors occupied: 0-13 main slot A, 14-27 main slot B, 28-29 Hall of Fame, 30 Trainer Hill, 31 Recorded Battle. None are spare. Do NOT repurpose native sectors or enlarge SaveBlock1 beyond the old `0x3D88` footprint.
- **E5 game branch**: `DevElectrum/xgba-emerald-test` / `xgba/e5-expanded-save`, based on accepted E4. Draft [PR #6](https://github.com/DevElectrum/xgba-emerald-test/pull/6). `tools/xgba_e5_save.py` creates a separate E5 save from unchanged 128KiB native flash and optional 16-byte mGBA RTC trailer. It refuses to overwrite existing files and provides inspect/get/put/extract-native commands for offline experiments. `tests/test_xgba_e5_save.py` covers 20 worlds, 2-copy CRC fallback, both-copy corruption detection, native bytes/RTC preservation and maximum payload.
- **Storage plan**: physical save size exactly 1MiB (optionally +16 bytes RTC at end): 0x00000..0x1FFFF untouched native save, 0x20000..0x20FFF primary header, 0x21000..0xE8FFF 20 worlds x two 20KiB slots, 0xE9000..0xFEFFF 88KiB reserved, 0xFF000..0xFFFFF backup header. Each record has 32-byte self-validating header and max 20,448-byte payload. Signatures `XGBAE5S\0` / `XGBAE5W\0`; CRC32 and monotonic sequence. Any corrupt active snapshot falls back to the older valid copy; both invalid report an error.
- **ROM opt-in**: E5 branch adds `make e5`, invoking established E3 64MiB packer with `--e5-save`. ROM has same `XGBA256` extended-ROM header bytes `0xB5..0xBB`, revision byte `0xBC=0xE5` and recomputed GBA checksum `0xBD`. Output `xgba-emerald-e5.gba`, independent of old E4 and E3 ROMs. The E5 game currently retains E4 script/counter behavior; it does NOT yet access expanded history.
- **E5 emulator branch**: `DevElectrum/xgba` / `xgba/e5-save-expansion`, based on accepted fast-forward branch `xgba/p1-fast-forward`. Draft [PR #4](https://github.com/DevElectrum/xgba/pull/4). For explicit E5-tagged ROMs **with initialized E5 save magic**, prototype maps 1MiB `.sav` (normal first128KiB flash + 896KiB appended) and exposes extension via CPU reads/writes to **0x0F000000..0x0F0DFFFF**. Original flash commands remain in 0x0E; out-of-range extension addresses ignored/return FF. Writes mark savedata dirty for normal mGBA sync. Legacy ROM and old E4 saves are never converted or overwritten implicitly.
- **RTC gotcha discovered**: mGBA appends 16B clock metadata *after* normal flash bytes. Offline E5 migration handles native `0x20010` saves and generates `0x100010` files preserving RTC trailer at the end. Emulator `GBASavedataRTCRead/Write` offsets follow `GBASavedataSize`. Never naively copy old trailer into extension at 0x20000.
- **CI passed across both repos**: [E5 offline format Actions #41041353375](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41041353375) including optional RTC migration, [E5 emulator build/test Actions #41041284439](https://github.com/DevElectrum/xgba/actions/runs/41041284439), and [E5 game ROM Actions #41041353411](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41041353411) compiling 64 MiB E5-tagged Emerald, checking GBA revision/checksum and verifying all expanded-ROM payloads. **No running game has yet used the E5 0x0F save extension**, so do not call E5 complete.
- **Next**: Finish E5 ROM CI; implement a strictly guarded game-side E5 GBA-memory API and a simple read/write world-history test that cannot write to normal 0x0E Flash when emulator E5 extension is absent. Validate emulator direct persistence on a newly copied E5 save and ROM. Then design broader world state serialization, world transition lifecycle and recovery/rollback policy. Do not claim complete independent stories or accept E5 based on CI alone.
- Full technical guide: `docs/XGBA_E5_README.md`. Preserve `DevElectrum/grand-anthology`, accepted E4 branch, existing E4 savestates and `.sav` files unchanged.

## E4 formal acceptance: two independent worlds survived save/restart (2026-10-30)

- User's final post-restart World 3 audit: **`1, set`**; earlier in the same cold-reloaded E4 session World 20 audit: **`3, set`**. This closes the last outstanding E4 test and demonstrates world-specific event variable and first-visit flag persistence for two distinct world records in one regular Emerald `.sav`.
- E4 prototype status: **ACCEPTED**, with a bounded scope of 4 variables and 48 flags for each of 20 worlds, in the original 384-byte unused portion of SaveBlock1. It is not yet independent full story, trainers, encounters, inventories, or PC boxes.
- Next architecture milestone should investigate expanding persistent storage substantially beyond SaveBlock1's unused bytes, while protecting E4 migration and accepted E3 geography. Do not quietly enlarge `struct SaveBlock1` inside the existing save-sector allocation.

## E4 user-confirmed live independent world state (2026-10-30)

- User successfully built `xgba-emerald-e4.gba` on Nyx with `make e4`: exact 64 MiB ROM, 20 geography instances and 16,760 verified expanded-ROM payloads. E4 save copied separately from E3 (`xgba-emerald-e4.sav`).
- **User confirmed in real XGBA gameplay**: in World 20 auditor initially showed progress **0**, flag **CLEAR**; after talking to writer three times, auditor showed progress **3**, flag **SET**.
- After switching to World 3, auditor showed **0 / CLEAR**. Writer once, then auditor showed **1 / SET**. After switching *back* to World 20, auditor still reported **progress 3**. Hence world-local variable+flag writes/readback and different counters survive round-trip world switching. World 20 flag after this last return has not been separately reconfirmed in the user's newest message.
- **E4 COMPLETE COLD-RESTART ISOLATION CONFIRMED by user**: Following normal in-game save, complete emulator exit and relaunch, the World 20 auditor reported **3 / SET**, then the user traveled to World 3, whose auditor reported **1 / SET** after that same restart. Both independently selected world-bank records survived a normal save/restart/load and remained distinct. **E4 prototype is accepted.** This does not demonstrate complete story, trainer, encounter or box isolation.
- No terminal commands needed for this phase. The user requested step-by-step gameplay instructions rather than multiple technical commands at once.

## E4 clean CI build passed (2026-10-30)

- [Dedicated E4 Actions #41036086285](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41036086285) **SUCCEEDED**: generator, modified Emerald compiler/linker, 64 MiB E4 ROM pack/verify, exact original SaveBlock1 compile guard, and static event-bank presence check.
- Linker memory report **SaveBlock1 = 15,752 bytes / 15,872 capacity (99.24%)**, identical to E3 and fully compatible with the existing save-sector footprint. SaveBlock2 = 3,884 and PokemonStorage = 33,744 unchanged. The 384-byte E4 bank occupies bytes previously labeled unused, not an added region. E4 uses no additional sectors.
- The `xgba-emerald-e4.gba` output in CI was exactly **67,108,864 bytes**. Existing E3 packer verified all **16,760 relocated border/map assets** covering original, World Two, and 18 extra physical world payloads. No copyrighted ROM is committed or uploaded.
- The inherited `.github/workflows/build.yml` CI also **PASSED** in [Actions #41036331293](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41036331293), including both original and MODERN Emerald compiler stages with E4 bank and NPC scripts.
- E4 **runtime test PASSED and accepted**: writer NPC at World 20 cloned Littleroot x16,y12, auditor x18,y12, return scientist x14,y12. User confirmed World 20 count3/SET, switched to World 3 0/CLEAR then 1/SET, returned to World 20 count3, saved/reloaded World 20 count3/SET and revisited World 3 count1/SET after reload. The E3 save was copied to an E4 save file.
- Dedicated draft E4 PR #5: https://github.com/DevElectrum/xgba-emerald-test/pull/5. Detailed user test steps: `docs/XGBA_E4_README.md`. Stay on experimental E4 branch, leave `DevElectrum/grand-anthology` untouched.
## E3 final visual acceptance and E4 start (2026-10-30)

- User explicitly confirmed 'Kool fixed' after rebuilding the roof-preserving E3. The previous World 20 selector, save/quit/restart/reload and scientist number readback were also confirmed by user screenshots. Treat the E3 core geographic instance experiment and roof repair as accepted, while never claiming all 518 maps were visited.
- New E4 experimental branch: `xgba/e4-world-state`, based only on accepted E3, not modifying E3 baseline or Grand Anthology.
- Inspected actual `struct SaveBlock1`: 15,752 bytes exactly (`0x3D88`) and it contains a truly labeled unused 384-byte region at offset `0x3598` (`unused_3598[0x180]`), separate from live flags/vars. `struct SaveBlock1` and `struct XgbaWorldStateBank` have compile-time exact-size guards. E4 replaces only the unused region, preserving the save-block's size and all existing field offsets.
- E4 bank layout: 4-byte magic `0x34454758`, 20 × 16-byte per-world records, and 60 reserved bytes, total 384 bytes. Each world record contains **four world-scoped u16 variables** and **48 world-scoped flags** (6 bytes) plus 2 reserved bytes. Unlike a wholesale full-story replacement, this fits inside existing flash sectors and works with E3 save format.
- `src/event_data.c` routes `GetVarPointer` for `0x40F7..0x40FA` and `GetFlagPointer` for reserved `0x020..0x04F` through indexed records. Since normal VarGet/VarSet/FlagGet/FlagSet call those pointer methods, event scripts automatically observe independent per-world values. The existing `VAR_XGBA_WORLD_ID` (0x40FF) is read directly from old global SaveBlock1 vars; World 2 maps to index1, World 20 to index19, 0/1 to original World 1 index0.
- E3 save migration: On first E4 bank access, if magic doesn't match, zero the entire bank and write magic. On normal save, bank is included in vanilla SaveBlock1 sectors without changing sector allocation. This is an experimental extension; users should **copy** their E3 .sav to an E4 filename, not overwrite original.
- Updated E2 map generator adds two new test NPCs in cloned Littleroot in **all worlds 2..20**: state writer at (16,12) increments world-specific progress and sets first-visit flag; state auditor at (18,12) reports current world's counter and flag. Existing return scientist at (14,12) remains. Assembly scripts in `data/maps/XgbaTestTown/scripts.inc` use ordinary `addvar`, `setflag`, `goto_if_set`, `buffernumberstring` macros and should exercise the C bank through real gameplay.
- `make e4` generates E2 maps and E3 offset header, recompiles Emerald, and invokes unchanged E3 64 MiB packer with E4-specific output `xgba-emerald-e4.gba`; dedicated `.github/workflows/xgba-e4.yml` validates the compiler save-block assertions and expanded ROM. Docs: `docs/XGBA_E4_README.md`.
- Intended E4 user test **fully passed**: E3 save copy; World 20 auditor 0/CLEAR, then 3/SET; World 3 initially 0/CLEAR, then 1/SET; World 20 still 3; save/restart -> World 20 3/SET and World 3 1/SET. Prototype completion confirmed by user.
- E4 LIMITATION: this is 4 variables/48 flags per world, **not** isolation of all normal story flags, encounters or trainers. Full 20-world story history exceeds the current spare save space and requires expanded persistent backing storage with migration/checksums.
- Dedicated E4 CI **passed**: https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41036086285 . **E4 gameplay acceptance is also complete**, including cold-restart persistence of both world records.
## E3 user-confirmed World 20 persistence and rooftop repair (2026-10-30)

- **E3 core runtime milestone confirmed by user:** screenshot 1 shows the XGBA Test Town selector saying "Destination: WORLD 20!"; screenshot 2, taken after saving, exiting and relaunching XGBA, shows the cloned Littleroot return scientist saying "World 20 reporting in! Back to the lab!" User explicitly states everything else appears to work. This proves the world ID in SaveBlock1 persisted across a cold emulator restart and the duplicated Hoenn geometry loaded.
- **Visual regression reported:** screenshot 2 has a missing tile on the roof of the house on the left. E3's cosmetic 5-bit world marker was overwriting full metatile indices near central Littleroot and previously only checked the high collision/elevation bits (`0xFC00`); preserving those attributes does NOT ensure a roof tile remains a roof. World 20 exposes the corruption.
- **Root-cause fix on E3 branch:** commit `3990b93bdca256dc52ec79df9f6fea66cba3d818` removed the entire `marker_cells/world_marker` helper and the call mutating cloned Littleroot tiles in `tools/xgba_pack_e3.py`. Thus every one of Worlds 3-20 gets original border/map bytes unchanged, with distinct CPU pointers and physical ROM copies. `tools/xgba_pack_e3.py verify` checks exact bytes for all payloads.
- Removed unused marker preflight from `Makefile` (`6a3a8c31`) and deleted `tools/xgba_test_e3_marker.py` (`88ad5d0a`). The active world remains observable through NPC dialogue in cloned Littleroot and the Test Town selector, without modifying map geometry.
- IMPORTANT for user rebuilding: an E3 ROM is already present locally. **Do not delete `xgba-emerald-e3.sav`**. Close XGBA, execute `cd ~/Projects/xgba-emerald-test && git pull --ff-only origin xgba/e3-20-worlds && mv xgba-emerald-e3.gba xgba-emerald-e3-with-marker.gba && make e3`; the packer deliberately opens outputs in exclusive mode and will otherwise fail if ROM already exists. The save remains compatible because map IDs/world variable/save layout were not changed.
- **Fresh ROM-integrity validation PASSED**: [E3 Actions #41034692808](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41034692808) confirms generated 64 MiB ROM, 20 worlds, 16,760 exact expanded-layout/border payloads and relocated World 20 end offset `0x0359F668`. This run includes the tile-preserving packer, removal of obsolete preflight, and unchanged E3 runtime. User roof appearance after rebuilding remains to be checked. No evidence that all 518 maps in all 20 instances have been individually traversed.
- Branch `xgba/e3-20-worlds`, draft PR #4, derived from accepted E2. Keep `DevElectrum/grand-anthology` untouched.

## E3 marker fix validated in CI (2026-10-30)

- Initial post-failure marker correction `b8611d...` was also too restrictive: CI #41031616416 failed with `Could not locate five unchanged matching-ground tiles for world marker`.
- **Working fix** `633d5e4d0578035804e6b65491ba9c57e256fca7` chooses five positions whose source tile shares the same high six bits (elevation/collision mask `0xFC00`) as the safe metatile variants, rather than requiring any specific exact tile value. Each set bit changes only a source tile's low metatile index; unset bits preserve the original. The variants are sampled from the existing Littleroot layout.
- **Full E3 CI #41032096903 PASSED** this marker code: normal Emerald compilation, full 64 MiB E3 pack and verification, 16,760 expanded-ROM tile/border payloads and 20 world entries, with the final World 20 data ending at `0x0359F668`. https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41032096903 .
- Added `tools/xgba_test_e3_marker.py` in `ab5b8e4766f203bbcdc37e64ccf3b3d392f28430`, and inserted an automatic marker preflight before full compilation in Makefile commit `c0181a5ea1138ce7c40fb4d7f9f674ce0514138f`. **Both the marker preflight and full ROM build PASSED in [Actions #41032163852](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41032163852)**; logs report `E3 marker preflight PASS: all 18 world IDs, five safe tile slots`, then the full 16,760-payload 64 MiB E3 ROM verification.
- Local recovery for user: `cd ~/Projects/xgba-emerald-test && git pull --ff-only origin xgba/e3-20-worlds && make e3`. The previous failed packer created no E3 ROM, so there is normally nothing to delete. Expected ROM: `xgba-emerald-e3.gba` 67,108,864 bytes.
- Still need user to confirm Worlds 3/20 selection, route transitions, building exits, and save/restart/reload. Do not claim 20-world runtime gameplay accepted from CI alone.
## E3 marker failure on Nyx, corrective fix (2026-10-30)

- User ran `make e3` on `xgba/e3-20-worlds`. **Emerald compilation/linking passed** (EWRAM 249,776 bytes, IWRAM 30,892 bytes). `tools/xgba_pack_e3.py pack` then raised `ValueError: World marker would overwrite a non-ground tile` inside `world_marker()` after assuming five fixed positions in cloned Littleroot had identical ground tiles.
- Confirmed this is a **ROM packer marker assumption**, not XGBA emulator, linker, map tables or 64 MiB addressability. Earlier E3 pre-marker build passed CI #41029580141; subsequent marker-added CI runs failed.
- **Corrective fix committed** to packer in `b8611d6472a3cb387937d1016e602f047ac5c675`: select five existing equal ground tiles near the center of Littleroot by scanning rows 12, 11, 10, 9, 8 (columns 6-12), then encode binary `world - 2` using matching upper 6-bit metatile attributes; no longer require a fixed five-tile strip to be uniform. README corrected in `f75425bf6dd9447c40d023b8f6e1724f2436fac2`.
- The post-fix CI status must be checked before claiming successful 20-world marker build. See the latest runs of `.github/workflows/xgba-e3.yml`, including #41031616416 (fix) and #41031653299 (docs update). If further packer errors occur, inspect the exact line from logs and correct without compromising safety checks.
- User should run `git pull --ff-only origin xgba/e3-20-worlds`, then `make e3` (if no output ROM from failed packer, no deletion needed). Use the user-reported emulator Qt frontend to test Worlds 3 and 20, separate geometry and save/reload.
## E3 successful CI evidence (2026-10-30)

- Clean [GitHub Actions run #41029580141](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41029580141) **PASSED every step**: tools syntax, generator, Emerald compile, full 64 MiB pack, independent verify and 20-instance manifest assertions.
- Manifest confirms World 1 original Hoenn + World 2 E2 shared network + **18 additional physical world payload sets**. Each of Worlds 3-20 has 441 distinct layout entries, 882 tile/border assets, **652,904 bytes of physical geometry**, fixed 1 MiB block stride.
- Verified generated cartridge size **67,108,864 bytes**. Last World 20 payload ends at ROM file offset **0x0359F668** (56,227,432), leaving room inside the 64 MiB cartridge. Total E3 check covered **16,760 tile/border payloads**, including E1/E2.
- The CI build proves the generated and relocated bytes, not that the C runtime pointer selector and in-game world switch work under real XGBA graphics/saving. User's XGBA interactive tests are still needed. Explicitly test selector IDs World 3 and World 20, route borders/interior doors, leave and reenter world, and save/restart/reload.
- Draft PR #4 is https://github.com/DevElectrum/xgba-emerald-test/pull/4, targeting the E2 experimental branch. Keep draft until user acceptance.
- GitHub's inherited `.github/workflows/build.yml` originally started normal/modern compilation without generating E3 map JSON/headers. Updated it in commit `d793be4da5fc37a8a63118eaa07a18c1983270b2` to run E2 and E3 generators before the original standard + modern compiler jobs. This CI-specific addition has not itself been confirmed green yet; check the latest `CI` workflow on draft PR #4.
## E3 implementation: 20 Hoenn geography instances (2026-10-30)

- New branch: `xgba/e3-20-worlds` based on user-tested E2. Previous E2 map network generation remains intact; no writes to Grand Anthology or master.
- Architecture: original Hoenn is World 1; E2's tested cloned map group network is World 2. Worlds 3..20 reuse E2's 518 map header/warp/connection definitions and switch **separate physical copies** of 441 tile maps plus 441 borders by a persistent `VAR_XGBA_WORLD_ID=0x40FF` (previously unused SaveBlock1 event var). This avoids 680 map groups, whose group indexes exceed eight bits.
- `src/overworld.c` uses `XgbaGetWorldLayout()` for the active map; `src/fieldmap.c` applies it to neighboring maps when copying route border tiles. Temporary active/connection layout structs are separate so neighbor rendering does not overwrite the active pointer. `include/xgba_world_e3.h` declares the API.
- `tools/xgba_generate_e3.py` generates ignored `include/xgba_world_e3_data.h` with 441 per-layout map/border offsets. `tools/xgba_pack_e3.py` preserves verified E2 payloads and adds 18 physical world chunks from file offset `0x02400000`, 1 MiB per chunk, all within a 64 MiB tagged ROM. All source/offset/payload bytes are verified.
- Later E3 **visual verification upgrade**: commit `173dc589b2a6d8b2b5682d3ea585df98aa3ffc17` adds a five-ground-tile marker to cloned Littleroot only in Worlds 3-20, encoding `world_id - 2` in binary; the other 440 map layouts are copied unchanged. The return scientist now buffers and displays the active world ID (commit `eb013c91ad1a0071ddc8fc00e620a25eaa305b92`). These upgrades require their own CI pass and gameplay confirmation.
- In XGBA Test Town, a new scientist NPC at `(18,12)` cycles destination IDs **2 through 20**. Existing destination scientist `(16,12)` now warps into the chosen world and reports number. The E2 return NPC at cloned Littleroot `(14,12)` remains unchanged. Worlds 2..20 share warp graph and story suppression.
- `make e3` runs E2 map generator, E3 offset generator, Emerald compilation, E3 pack, E3 verify. Dedicated `.github/workflows/xgba-e3.yml` tests on branch pushes; docs/XGBA_E3_README.md describes local commands and portal checks.
- Important E3 LIMITS: geometry copies, not 20 independent stories or save slots; same encounter/trainer/global flags across worlds, and script/dynamic Fly/Teleport routing isn't redirected. World ID saved in the existing event var; no enlargement of persistent save RAM.
- E3 **static clean CI PASSED**: https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41029580141 . Game acceptance is still pending.
- Immediate next steps: (1) inspect E3 clean CI logs and fix compile/packer failures, (2) produce xgba-emerald-e3.gba locally with `make e3`, (3) user visits Worlds 3 and 20, tests interior/route transitions, save-restart-reload and Tab/Qt.
## E2 World Two door routing CONFIRMED by user (2026-10-30)

- User explicitly states they tested **multiple times** that houses, **Pokémon Centers** and **Poké Marts** entered in Hoenn World Two return to **Hoenn World Two**, never original Hoenn.
- Combined with prior screenshot and user report of save/quit/restart/reload still in World Two, this closes the **core E2 proof**: an independently indexed map network, native interior warp isolation, and persistent map location work in real XGBA gameplay.
- Static verification passed in [Actions #41027163879](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41027163879) for 518 clones, 441 cloned layouts, 1,313 processed warp entries, 148 route connections, and exact 64 MiB ROM output.
- **Not yet individually reported**: crossing outdoor route boundaries, visiting every one of the 518 maps, scripted teleport behavior, world-isolated story flags, trainer progression, or encounters. Do not equate core E2 proof with 100% second-world gameplay compatibility.
- Next architecture milestone E3: use a separate world/instance identifier and dynamic map resolution for a prospective 20 Hoenn worlds. Native map group IDs are byte-sized; 20 × 34 groups exceeds that representation. Maintain all user-verified E1/E2 branches and never touch Grand Anthology.

## E2 real-game save persistence proof (2026-10-30)

- User posted an mGBA/XGBA screenshot showing a rendered outdoor World Two Hoenn town after saving, closing, restarting, and reloading, explicitly reporting **'spawned in hoenn 2 after save and restart'**.
- **Confirmed by user**: World Two save-location identity persists across an emulator restart and the loaded town renders successfully. This is a crucial persistence milestone beyond E1's isolated test town. Screenshot is conversation evidence, not copied into the public repository.
- **Previously confirmed by CI**: 518 cloned map definitions / 34 new map groups / 441 cloned layouts, 1,313 static warp entries / 148 route connections remapped, no unresolved destinations, 64 MiB packed image with relocated layout/border bytes (Actions run #41027163879).
- **Subsequently verified by user**: World Two house, Pokémon Center, and Poké Mart doorways return to World Two, tested repeatedly. **Still to verify explicitly:** crossing outdoor route boundaries and the return portal from World Two Littleroot.
- E2 **core geography, interior routing and location-persistence proof is accepted**. Outdoor route-boundary checks remain an optional follow-up for broader network acceptance. Do not claim separate per-world plot flags, encounter tables or trainer state: the current E2 maps intentionally share game-wide progress and suppress story events.
## E2 verified CI milestone (2026-10-30)

- [GitHub Actions run 41027163879](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41027163879): SUCCESS, every workflow step passed. Generator produced **518 cloned maps, 34 new groups, 441 cloned layouts, 1,313 processed warp entries, 148 route connections and zero unresolved links**.
- The ROM packer built exact **67,108,864 bytes (64 MiB)**, preserved E1 two map layouts and relocated **882 separate border/map payloads** beyond the 32 MiB boundary. World Two payloads begin at file offset 0x02002000 / XGBA CPU 0x12002000, with asset payload end offset 0x020A1668. ELF symbols for Xgba2_LittlerootTown_Layout and Xgba2_Route101_Layout were confirmed in CI.
- Initial CI run #41026760064 failed *after successful Emerald compilation* because unused contest-room layout placeholders don't have tile bytes matching their declared 1x1 dimensions. Fixed in commit 52e1ef85496dd06ee936282080bf186514b6e340: accept even-byte source tile arrays but continue checking ELF symbols, linked source bytes and relocated bytes exactly. The rerun passed.
- E2 draft PR #3: https://github.com/DevElectrum/xgba-emerald-test/pull/3 (targets accepted E1 branch). Keep draft until user gameplay confirms traversable World Two, door exits and save/load.
- **User has not yet performed E2 gameplay test**, so avoid claims that World Two route navigation/save reload work. Existing E1 evidence is only for test town.
- Local: checkout xgba/e2-hoenn-network; run make e2 (generator -> Emerald compiler -> E2 pack -> verify); then launch xgba-emerald-e2.gba in Qt XGBA. Portal at E1 Test Town second scientist (16,12) goes to E2 Littleroot. Detailed sequence: docs/XGBA_E2_README.md.
## E2 second-Hoenn implementation underway (2026-10-30)

- Branch: xgba/e2-hoenn-network based on accepted E1 branch xgba/e1-independent-map. Never modify Grand Anthology or master for this work.
- tools/xgba_generate_e2.py derives a second map network from original source JSON, appending 34 map groups and 441 layout descriptors and generating map JSON under ignored data/maps/Xgba2_*/ directories. All ordinary connection and warp destinations within original Hoenn are rewritten to cloned IDs. Unexpected unmapped links fail fast; special MAP_UNDEFINED/MAP_DYNAMIC are preserved as exceptions.
- World Two maps use a shared neutral map script, no NPC story objects/coordinate scripts, preserving geometry and standard door/route transitions only. User should not assume script-triggered transitions, wild encounters, story or independent progression are implemented.
- Portal chain: Original Littleroot scientist (14,12) -> E1 Test Town, second Test Town scientist (16,12) -> E2 Littleroot (13,12), E2 return scientist (14,12) -> E1 Test Town (15,12).
- tools/xgba_pack_e2.py builds 64 MiB tagged XGBA ROM, relocates E1 pair plus 441 cloned map and border asset pairs to 0x12002000 onwards, verifies ELF pointers and byte payloads. Intended target: xgba-emerald-e2.gba.
- Makefile adds make e2 (generate -> compile -> pack -> verify). CI workflow .github/workflows/xgba-e2.yml and user guide docs/XGBA_E2_README.md added.
- Generation deliberately modifies tracked data/maps/map_groups.json and data/layouts/layouts.json in **local** working tree. Do not commit generated groups/layouts/map files; README explains restoring tracked files after building. Ignore generated map folders; output ROM must never be uploaded or committed.
- Important architecture: groups 34 original +34 E2 =68 (<256). Native group ID is 8-bit; twenty Hoenn copies will not fit 680 groups. Later add explicit world ID and map router.
- Status at creation of this handoff entry: E2 fresh CI compile still running; **do not claim E2 build or gameplay passed** without CI result and user's manual portal/warp/save tests.
- Build CI: https://github.com/DevElectrum/xgba-emerald-test/actions/workflows/xgba-e2.yml . User run instructions: https://github.com/DevElectrum/xgba-emerald-test/blob/xgba/e2-hoenn-network/docs/XGBA_E2_README.md

### Current E2 acceptance checklist

1. Generate all E2 maps without any unresolved map links; compile a normal Emerald executable under 32 MiB, link cloned maps and pointers.
2. Build and statically verify exactly 64 MiB E2 ROM with 441 relocated map layouts and borders, plus E1 payloads.
3. User navigates Test Town portal to World Two Littleroot, north to World Two Route101 and Oldale, enters/exits a house, returns through portal and saves/reloads in World Two.
4. If any step fails, fix E2 branch only, rerun CI and update this handoff, keeping accepted E1 intact.
## E1 final acceptance: user confirmed (2026-10-30)

**All critical E1 gates are confirmed complete.** After the screenshot established new map rendering and custom witness NPC dialogue, user explicitly confirmed:
1. The return scientist takes the player from `XgbaTestTown` back to original Littleroot.
2. The player can return to `XgbaTestTown`, use in-game save, close XGBA, relaunch the 64 MiB E1 ROM and load into the cloned town successfully.

This validates independently defined Emerald map IDs, distinct layouts at XGBA CPU addresses `0x12000000` and `0x12001000` (already statically verified in CI), bidirectional map navigation, and location persistence on save/load. **It does not yet establish independent per-world flags/trainer progress, 20 Hoenn copies or expanded PC save capacity.**

- Completed experiment: `xgba/e1-independent-map`, [draft PR #2](https://github.com/DevElectrum/xgba-emerald-test/pull/2).
- CI: [E1 ROM-integrity pass](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41024989544) and [source-build pass](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41024989681).
- Next E2: **do not modify Grand Anthology**; create a new isolated `xgba/e2-hoenn-network` branch based on accepted E1. Avoid naively duplicating all maps in the first group if it would push individual map indices past 255. Investigate generator, map groups and warp/connection routing; preserve original story/route network. Define instance identity separately from map group and map number for eventual 20-world scaling.
- Preserve E1 as working baseline, and maintain this living handoff at every major implementation/test milestone.

## E1 user gameplay evidence (2026-10-30)

- User uploaded an XGBA gameplay screenshot of the newly defined **XGBA TEST TOWN**, showing successfully rendered town tiles/buildings, a character by a house, and active custom NPC dialogue: **"You're in XGBA TEST TOWN! This map lives beyond 32 MB!"**
- **Confirmed by screenshot**: gameplay reached the independently defined test map, visual rendering succeeded, and the new test-town witness NPC event/script/text executes.
- **Corroborating static evidence**: [E1 build and integrity CI #41024989544](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41024989544) passed, showing the test town's tile layout is independently located at XGBA CPU `0x12001000` while Littleroot is at `0x12000000`.
- **Subsequently user-confirmed**: return scientist works and in-game save/relaunch/load while in the cloned town works. E1 acceptance is complete; exact collision coverage is not exhaustive.
- Screenshot is conversation evidence, not a file committed to the public repository.

## E1 implementation progress (2026-10-30)

- New experimental branch `xgba/e1-independent-map`, based on E0; [draft E1 PR #2](https://github.com/DevElectrum/xgba-emerald-test/pull/2) targets `xgba/e0-expanded-layout`. Leave the fork's master and `DevElectrum/grand-anthology` untouched.
- E1 **full static build and ROM-integrity verification PASSED** in [GitHub Actions run #41024989544](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41024989544), commit `e99c2536c4dc44623748e359767931f347954257`. All stages succeeded: Emerald compile, Python syntax, E1 pack, independent verification, exact 64 MiB output and two ELF layout descriptors. The additional [upstream-compatible source CI #41024989681](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41024989681) also **PASSED**, including its modified Emerald and modern-compiler builds. The prior failed run #41024607901 assumed three adjacent original tiles matched; this was corrected in `e99c2536`. **Actual bidirectional portal gameplay and saving in the test town remain unverified.**
- Added `data/maps/XgbaTestTown/map.json`, `scripts.inc`, and separate copies of source `data/layouts/XgbaTestTown/map.bin` and `border.bin`. Updated map group list and layout table, preserving all original IDs by appending at the end of their existing group and table.
- New Littleroot scientist at map `(14,12)` warps to `MAP_XGBA_TEST_TOWN` at `(13,12)`. The test town has return scientist at `(14,12)`, witness NPC at `(3,12)`, no house-story warps or Route101 connection, and a minimal mapscript.
- `tools/xgba_pack_e1.py` builds `xgba-emerald-e1.gba` at exactly 64 MiB; first map layout is relocated to `0x12000000` and the clone layout to `0x12001000`. The clone's **output tile layout** gets a small three-tile variant so the contents are different while source binaries remain separately managed.
- `.github/workflows/xgba-e1.yml` compiles and runs static pack/verify steps. The inherited upstream workflow on E1 uses `COMPARE=0` intentionally because an edited game is **not** bit-for-bit vanilla. Generated ROMs remain ignored.
- Local build and manual test instructions: [docs/XGBA_E1_README.md](https://github.com/DevElectrum/xgba-emerald-test/blob/xgba/e1-independent-map/docs/XGBA_E1_README.md).
- **Unverified until user performs E1 manual test**: bidirectional portals, distinct tile marker, save/reload while standing in clone, collision and NPC events. Preserve an existing save backup; never overwrite the user's important project ROM.

## User-verified UI milestone and E1 design (2026-10-30)

- The user confirmed **Tab fast-forward works** on the SDL XGBA P1 branch and then confirmed that the **Qt GUI build launches** after fixing the empty Git-tag CMake error. They wish to resume the ROM work. This is user-reported evidence of the GUI launch; do not assume every Qt menu or game feature has been exhaustively checked.
- Emulator branch is `DevElectrum/xgba:xgba/p1-fast-forward`; see its own `docs/NEXT_ASTRA_HANDOFF.md`. The Qt CMake fix quotes an empty `RELEASE_TAGS` expansion.
- In `data/maps/map_groups.json`, `gMapGroup_TownsAndRoutes` is first in `group_order`. In `data/layouts/layouts.json`, layout entries include source `map.bin` and `border.bin` and tileset pointers. To preserve map constants, append a new test map at the end of an existing group; append a separate layout at the end of the layout table.
- **E1 goal:** preserve original Littleroot, introduce `XgbaTestTown` (or similar) with separate map ID/header/layout, and have an explicit reversible portal between the two. Simplest robust approach: add a dedicated map event/NPC script to enter the test map and an exit script to return. Do not repurpose a story-critical original warp. Avoid duplicating Littleroot story scripts/triggers into the test clone.
- Place the clone's `map.bin` in an independently owned source path, and distinguish it visibly from the original using a safe tile or sign; adjust the packer to relocate **only the clone's** `MapLayout.map` pointer into an aligned expanded region (E0's relocation can stay or be retained as a regression check). Use ELF symbols and validate the pointer and relocated byte payload.
- Critical acceptance: warp into the second map, verify distinct map identity, expected visual/layout difference, collision and NPC/script behavior; warp back to original, preserve normal story; test save/reload while standing in the clone. If the save file cannot restore the clone, investigate before scale-up.
- Distinguish this from full **20 Hoenn worlds**: a 20-world implementation will eventually require a world/instance ID and instance-scoped flags/scripts/saves. E1 proves unique map IDs and navigation, not world isolation or expanded save RAM.
- Keep large ROM files out of Git history, and run CI for every source/packer change. Keep `master` and Grand Anthology untouched.

## Immediate next three steps

1. Create `xgba/e1-independent-map` based on E0 branch and implement a separately indexed test map plus a non-story-critical portal/return route. Keep E0 draft PR open.
2. Extend `tools/xgba_pack_emerald.py` and CI to relocate and verify **both** original Littleroot and the test clone's independent map payload(s), including a visibly distinct marker, precise address alignment, checksum and byte-range assertions.
3. Build a local expanded E1 ROM on Nyx, interactively walk through portal, validate collision/scripts, return, save/reload, and check normal Qt/Tab turbo. Record exact results in this handoff. Only after this gate, plan mass cloning, per-world identity, and separate Pokémon storage engineering.

## E0 work and tests

- The working branch should contain `tools/xgba_pack_emerald.py` and a dedicated `.github/workflows/xgba-e0.yml` CI pipeline. Inspect current files and latest CI before claiming success.
- The upstream `.github/workflows/build.yml` on `master` is unmodified; the dedicated E0 workflow should run on PRs and on work branch pushes only as configured.
- Use GitHub connector actions and GitHub Actions logs for validated claims. Avoid generated ROMs or copyrighted binary outputs in commits.
- For emulator manual testing: XGBA is the experimental mGBA fork; ordinary mGBA cannot handle XGBA's `0x12000000` ROM mapping.

## After E0

- Build a **distinct** duplicated test map accessible alongside original Littleroot, with independently addressable map header and warp, while retaining original.
- Stress actual maps/assets, not 20 synthetic probe records.
- Only then explore enlarging save/PC boxes. Enlarging PC storage is separately limited by Emerald's reserved save area (upstream recently reported PokemonStorage 33744 / 35712 bytes); a 256 MiB ROM does not increase save RAM automatically.
- Never claim Android support without an Android build and manual test.

## How to update this handoff

Append/replace with: new branch + exact commit SHA; changes made; tests and exact CI run URLs; reproducible commands; blocking errors; next three concrete steps. Keep it compact and factual. Do not mark planned work as done.
