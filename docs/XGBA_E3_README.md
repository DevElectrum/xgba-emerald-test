# E3: Twenty Hoenn worlds in a 64 MiB XGBA cartridge

E3 builds on E2's user-tested two-Hoenn map routing. It makes **20 selectable Hoenn geography instances**, not 20 independent full game saves or stories. The accepted E1/E2 branches, original Hoenn and Grand Anthology remain unchanged.

## Architectural leap

- World 1 is the original Emerald Hoenn (original map groups).
- World 2 reuses E2's independently linked 34-map-group network and expanded geometry.
- Worlds 3 through 20 **share E2's 518 map headers, warp and route graph**, but select independent physical sets of 441 map tile layouts and 441 border assets at runtime.
- The world selection is stored in an unused existing persistent SaveBlock1 event variable at 0x40FF (VAR_XGBA_WORLD_ID). It survives normal saving without enlarging save structures.
- Only native World Two layout IDs are redirected. World 1 and E1's test town keep their existing layouts. Both current-map tiles and connected-route border tiles follow the world ID.
- The 18 additional physical worlds occupy aligned blocks from ROM file offset 0x02400000 (XGBA CPU address 0x12400000). Each block has a 1 MiB stride; total cartridge remains exactly 64 MiB.
- The lookup-table header is generated from existing source layout binaries, which avoids manually maintained offsets. All payloads and E2's source pointers are byte-verified.

## Building on Nyx

Use the previously installed pret/agbcc toolchain and your working XGBA Qt frontend. In ~/Projects/xgba-emerald-test:

```bash
git fetch origin
git switch --track origin/xgba/e3-20-worlds
make e3
~/Projects/xgba/build-xgba-gui/qt/mgba-qt ~/Projects/xgba-emerald-test/xgba-emerald-e3.gba
```

IMPORTANT: Use `make e3`, not plain `make`, on a fresh checkout. It generates E2 maps/groups and then include/xgba_world_e3_data.h before compiling the modified C sources. It creates an output ROM named xgba-emerald-e3.gba. The packer refuses overwriting existing ROMs. Earlier E1/E2 ROMs remain intact.

The E3 generator changes tracked `data/maps/map_groups.json` and `data/layouts/layouts.json` in your *working tree* only. Its generated map folders and layout header are ignored by Git. Once the ROM is built you may restore the two tracked JSON files with `git restore data/maps/map_groups.json data/layouts/layouts.json`, but rerun `make e3` before any future rebuild.

## Visiting the worlds

1. From original Littleroot, use the original scientist to enter XGBA Test Town.
2. In Test Town, the **new scientist at coordinates (18,12)** is the world selector. Talk repeatedly to cycle destination **World 2 → World 3 → ... → World 20 → World 2**. The dialogue reports the selected numeric world ID.
3. The existing scientist at **(16,12)** now sends you to the selected world's Littleroot. If no destination was selected, it defaults to World 2.
4. World 2 through 20 use a shared internal map network. Navigate outside to Route 101 or into houses; return normally. A return scientist in cloned Littleroot at **(14,12)** warps to Test Town without clearing the world selection.
5. For a rigorous test, visit World 3, then World 20, save inside a World 20 interior, quit and relaunch the ROM. Verify that it loads the same world and the selector still reports World 20.
6. Verify a normal Route 101/Oldale boundary in Worlds 3 and 20. Also check the menu-driven Qt XGBA interface and hold-Tab fast-forward.

## Major limits

- The geometry is **physically duplicated** in ROM, but the world instances share the same object/event scripts, tilesets, wild encounter logic and persistent flags. Story isolation and per-world progression are **not** part of E3.
- World 1 uses the ordinary Hoenn map network; Worlds 2 through 20 share E2's map IDs. Therefore checking only the map group/number cannot distinguish Worlds 3-20. Use the persistent world variable.
- World-specific content is currently identical tile-for-tile; the experiment proves instance routing and ROM addressability, not bespoke visual changes.
- Teleport, Fly, script-driven warps and respawn-to-heal-location may bypass the World Two route graph. They remain future tests.
- E3 automated checks establish build and ROM bytes, **not gameplay success**. Do not mark E3 accepted before user tests the selector, world traversal, and save/reload.

See the living handoff at docs/NEXT_ASTRA_HANDOFF.md and E3 Actions workflow `.github/workflows/xgba-e3.yml`.
