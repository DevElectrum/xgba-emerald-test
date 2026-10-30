# E2: Second connected Hoenn network

Experimental ROM for XGBA expanded cartridge mapping. Builds on successful E1 two-town proof. Grand Anthology and master are untouched.

## What E2 adds

- Creates another 34 map groups and clones all original Hoenn maps with separate map IDs and headers.
- Rewrites static warp destinations and route connections to stay within World Two.
- Creates 441 separate layout descriptors; copies both map tiles and borders into expanded ROM beyond 32 MiB.
- Reuses original graphics and music, but suppresses story NPCs, coordinate triggers and map transition scripts in World Two. This is a navigable geography test, not independent story progression.
- Keeps original Hoenn and E1 Test Town intact.

## Local build (on Nyx)

Run from ~/Projects/xgba-emerald-test after your existing agbcc toolchain is installed:

```bash
git fetch origin
git switch --track origin/xgba/e2-hoenn-network
make e2
~/Projects/xgba/build-xgba-gui/qt/mgba-qt ~/Projects/xgba-emerald-test/xgba-emerald-e2.gba
```

make e2 generates 518 additional map.json files into ignored data/maps/Xgba2_* folders, temporarily extends tracked data/maps/map_groups.json and data/layouts/layouts.json in the local working tree, compiles Emerald, and packs/verifies a 64 MiB output. Generated ROM files are never committed. If the output ROM exists already, rename it first: the packer refuses overwrites.

After building, restore the two temporarily changed tracked JSON files (optional):

```bash
git restore data/maps/map_groups.json data/layouts/layouts.json
```

## Gameplay navigation

1. In original Littleroot, scientist at (14,12) transports to XGBA Test Town.
2. Test Town now has a second scientist at (16,12), who transports to World Two Littleroot (13,12).
3. World Two Littleroot's scientist at (14,12) returns to Test Town (15,12).
4. Walk north from World Two Littleroot into World Two Route 101, then World Two Oldale Town. Verify the borders work.
5. Visit a house or laboratory from World Two, exit, and confirm it returns to World Two rather than original Hoenn.
6. Save in World Two, quit, relaunch, and confirm map identity persists. Test Tab fast-forward in Qt.

## Limits

- This clones geography with working static warps and connections; scripted teleports, HM access, wild encounters, NPC/quest progression, fly map and per-world event state remain separate engineering.
- Native Emerald map IDs carry 8-bit group and map numbers. E2 uses 68 groups total, within limits. Twenty native copies would require 680 groups and cannot be implemented this way. Future E3 needs instance identity independent of group/number.
- E1 maps are stored at expanded CPU addresses 0x12000000 and 0x12001000. World Two tile/border payloads start at 0x12002000.
- CI confirms compilation/ROM pointer integrity only. Actual navigation and saving require user testing.

See docs/NEXT_ASTRA_HANDOFF.md and .github/workflows/xgba-e2.yml for progress and CI.
