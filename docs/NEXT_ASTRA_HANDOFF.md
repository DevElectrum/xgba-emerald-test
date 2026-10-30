# XGBA Emerald experiment: living Astra handoff

Updated: 2026-10-30
Status: E1 and E2 core tests accepted by user. **E3 20-world ROM construction PASSED** on [GitHub Actions #41029580141](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41029580141). Gameplay in Worlds 3-20, selector, and save/reload are NOT yet confirmed.

## Read this first

- Canonical ROM test repo: `DevElectrum/xgba-emerald-test`; https://github.com/DevElectrum/xgba-emerald-test
- The upstream fork source is `pret/pokeemerald`, default branch `master`. Preserve upstream licensing, history and attribution.
- Current experimental working branch: `xgba/e3-20-worlds` (derived from user-tested E2 branch xgba/e2-hoenn-network, draft PR #3). Preserve E1/E2 baselines and original master.
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

## E3 marker fix validated in CI (2026-10-30)

- Initial post-failure marker correction `b8611d...` was also too restrictive: CI #41031616416 failed with `Could not locate five unchanged matching-ground tiles for world marker`.
- **Working fix** `633d5e4d0578035804e6b65491ba9c57e256fca7` chooses five positions whose source tile shares the same high six bits (elevation/collision mask `0xFC00`) as the safe metatile variants, rather than requiring any specific exact tile value. Each set bit changes only a source tile's low metatile index; unset bits preserve the original. The variants are sampled from the existing Littleroot layout.
- **Full E3 CI #41032096903 PASSED** this marker code: normal Emerald compilation, full 64 MiB E3 pack and verification, 16,760 expanded-ROM tile/border payloads and 20 world entries, with the final World 20 data ending at `0x0359F668`. https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41032096903 .
- Added `tools/xgba_test_e3_marker.py` in `ab5b8e4766f203bbcdc37e64ccf3b3d392f28430`, and inserted an automatic marker preflight before full compilation in Makefile commit `c0181a5ea1138ce7c40fb4d7f9f674ce0514138f`. The preflight itself needs green CI confirmation; check https://github.com/DevElectrum/xgba-emerald-test/actions/workflows/xgba-e3.yml .
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
