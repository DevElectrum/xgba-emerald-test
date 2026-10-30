# XGBA Emerald experiment: living Astra handoff

Updated: 2026-10-30
Status: E0 implementation in progress. **Do not claim a playable expanded Emerald ROM until CI and an interactive XGBA test confirm it.**

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
