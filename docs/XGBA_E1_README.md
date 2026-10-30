# E1: Two playable towns in XGBA's expanded ROM

## Why E1 exists

E0 proved that a real Emerald tile-layout pointer can reach file data stored beyond 32 MiB. E1 adds a **second native Emerald map**, `MAP_XGBA_TEST_TOWN`, with its own map header, layout descriptor, events and scripts. This is a map duplication milestone, **not** twenty complete worlds or independent story/save progression.

The original Littleroot remains playable. Both maps are backed by separate data in the expanded cartridge.

## Layout and portals

- `LittlerootTown_Layout`: tile-layout payload at ROM offset `0x02000000`, XGBA CPU address `0x12000000`.
- `XgbaTestTown_Layout`: independent tile-layout payload at ROM offset `0x02001000`, XGBA CPU address `0x12001000`.
- Test-town source binaries: `data/layouts/XgbaTestTown/map.bin` and `border.bin`, originally copied from Littleroot to preserve tile compatibility.
- E1 packer marks a 3-tile strip of the test map with another valid ground tile from the same source map. This ensures the final ROM holds **different** tile data for the two layouts.
- In Littleroot, interact with the scientist at map coordinates `(14, 12)` to enter Test Town at `(13, 12)`.
- In Test Town, interact with its scientist at `(14, 12)` to return to Littleroot at `(13, 12)`.
- A second test-town NPC near `(3, 12)` identifies the location. The clone deliberately has **no Littleroot story triggers, warps into story houses, or north Route 101 connection**.

## Build

Checkout the `xgba/e1-independent-map` branch and install the same `pret/agbcc` toolchain used for E0.

```bash
cd ~/Projects/xgba-emerald-test
git fetch origin
git switch -c xgba/e1-independent-map --track origin/xgba/e1-independent-map
make -j2 all
python3 tools/xgba_pack_e1.py pack
python3 tools/xgba_pack_e1.py verify
```

If the E1 branch already exists locally, use `git switch xgba/e1-independent-map` followed by `git pull --ff-only`. If an earlier E1 output exists, move it aside before rerunning `pack`; the packer deliberately refuses to overwrite it.

Launch using the Qt XGBA fork (built on `xgba/p1-fast-forward`):

```bash
~/Projects/xgba/build-xgba-gui/qt/mgba-qt ~/Projects/xgba-emerald-test/xgba-emerald-e1.gba
```

No copyrighted ROM binaries are committed or uploaded as CI artifacts.

## Manual acceptance test

1. Begin Emerald and reach original Littleroot with a test save.
2. Locate the new scientist NPC at `(14,12)` and interact. The message should mention visiting XGBA Test Town.
3. Confirm the new town renders, has an altered three-tile strip, and includes an identifying witness NPC near `(3,12)`.
4. Walk around, verify blocking tiles/buildings behave normally; speak to the witness; interact with the return scientist.
5. Confirm returning to **original** Littleroot, with original house/Route 101 events intact.
6. Enter the test town again, save using the normal in-game Save command, quit XGBA, reopen the E1 ROM and load the save. Verify player remains in the test town.
7. Check hold-Tab fast-forward in the Qt UI and regular-speed behavior after release.

The GitHub Actions `XGBA Emerald E1` workflow only proves **compilation and byte-level integrity**, not gameplay success. Report the observed manual results to the next Astra before accepting E1.

## Scope boundaries

- Neither `master` nor `DevElectrum/grand-anthology` should be modified.
- The test town has an independent map ID but reuses the Littleroot region map section/name and tilesets. It is not yet a separately named region on the region map.
- No expansion of save memory, PC storage, story flags or encounter logic in E1.
- The baseline `pokeemerald.gba` build is under 32 MiB; the packer is the only step that creates a 64 MiB tagged XGBA cartridge.
- Read [the living handoff](NEXT_ASTRA_HANDOFF.md) for current validation status, CI run, and next steps.
