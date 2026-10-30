# XGBA Emerald experiment: living Astra handoff

Updated: 2026-10-30
Status: **E0 static checks PASSED**, and user confirms **expanded Emerald runs in XGBA**. Working SDL Tab fast-forward and the Qt/menu-driven XGBA launch were separately confirmed by user. The full scripted warp/event/save/reload matrix is not explicitly confirmed. **Next milestone E1: a second independently selectable map with its own extended-ROM layout.**

## Read this first

- Canonical ROM test repo: `DevElectrum/xgba-emerald-test`; https://github.com/DevElectrum/xgba-emerald-test
- The upstream fork source is `pret/pokeemerald`, default branch `master`. Preserve upstream licensing, history and attribution.
- Experimental working branch: `xgba/e0-expanded-layout`; keep fork's `master` unmodified during experimentation.
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

## E1 implementation progress (2026-10-30)

- New experimental branch `xgba/e1-independent-map`, based on E0; [draft E1 PR #2](https://github.com/DevElectrum/xgba-emerald-test/pull/2) targets `xgba/e0-expanded-layout`. Leave the fork's master and `DevElectrum/grand-anthology` untouched.
- E1 **source compilation was already confirmed** by GitHub Actions #41024607901, but that run's packer phase **failed** due an overly strict assumption about adjacent ground tiles. Fixed in commit `e99c2536c4dc44623748e359767931f347954257`; inspect the latest E1 workflow before claiming full pass.
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
