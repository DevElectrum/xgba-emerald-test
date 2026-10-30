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

## Rebuild after the World 20 roof marker fix (October 30, 2026)

The user confirmed successful **World 20 save, restart and reload** with the previous E3 ROM, but noticed a missing tile on Littleroot's left-hand house roof. This was caused by the cosmetic world marker changing real map metatile IDs. The marker has been **removed entirely**; current E3 duplicates the original map and border data byte-for-byte in every world.

An old `xgba-emerald-e3.gba` file must be preserved/moved before packing because the packer refuses to overwrite it. On Nyx, **close XGBA** and run:

```bash
cd ~/Projects/xgba-emerald-test
git pull --ff-only origin xgba/e3-20-worlds
mv --backup=numbered xgba-emerald-e3.gba xgba-emerald-e3-with-marker.gba
make e3
```

Launch the new `xgba-emerald-e3.gba` in Qt XGBA using the same `xgba-emerald-e3.sav`. **Do not rename or delete the save.** Map IDs, world variable and save structure are unchanged. The World 20 return scientist should still say "World 20" after reload. Revisit the left house roof: the roof should now render normally. Byte-verification passed in [Actions #41034692808](https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41034692808); final visual validation is still up to the user.

IMPORTANT: Use `make e3`, not plain `make`, on a fresh checkout. It generates E2 maps/groups and then include/xgba_world_e3_data.h before compiling the modified C sources. It creates an output ROM named xgba-emerald-e3.gba. The packer refuses overwriting existing ROMs. Earlier E1/E2 ROMs remain intact.

The E3 generator changes tracked `data/maps/map_groups.json` and `data/layouts/layouts.json` in your *working tree* only. Its generated map folders and layout header are ignored by Git. Once the ROM is built you may restore the two tracked JSON files with `git restore data/maps/map_groups.json data/layouts/layouts.json`, but rerun `make e3` before any future rebuild.

## Visiting the worlds

1. From original Littleroot, use the original scientist to enter XGBA Test Town.
2. In Test Town, the **new scientist at coordinates (18,12)** is the world selector. Talk repeatedly to cycle destination **World 2 → World 3 → ... → World 20 → World 2**. The dialogue reports the selected numeric world ID.
3. The existing scientist at **(16,12)** now sends you to the selected world's Littleroot. If no destination was selected, it defaults to World 2.
4. World 2 through 20 use a shared internal map network with **unmodified Hoenn tiles**. Navigate to Route 101 or into houses; return normally. The scientist in cloned Littleroot at **(14,12)** reports the active world number and warps to Test Town without clearing the world selection. **There is no longer a ground-tile world-ID marker**, because it could damage building graphics.
5. User has already confirmed World 20 loads after saving, quitting and relaunching, with the return scientist reporting WORLD 20. After the roof repair, confirm the left house roof is intact; optionally repeat save/reload and check World 3.
6. Verify a normal Route 101/Oldale boundary in Worlds 3 and 20. Also check the menu-driven Qt XGBA interface and hold-Tab fast-forward.

## Major limits

- The geometry is **physically duplicated** in ROM, but the world instances share the same object/event scripts, tilesets, wild encounter logic and persistent flags. Story isolation and per-world progression are **not** part of E3.
- World 1 uses the ordinary Hoenn map network; Worlds 2 through 20 share E2's map IDs. Therefore checking only the map group/number cannot distinguish Worlds 3-20. Use the persistent world variable.
- **Worlds 3-20 contain byte-for-byte copies of the source layout and border data** at independent expanded-ROM offsets. A former cosmetic world marker modified five metatiles using only collision/elevation checks; the user saw a missing roof tile in World 20. That marker has been removed to preserve actual rooftop graphics. Confirm the active world through the scientist's world-number dialogue and the preserved world ID in the save.
- Teleport, Fly, script-driven warps and respawn-to-heal-location may bypass the World Two route graph. They remain future tests.
- E3's **World 20 selector and save/reload were confirmed by user screenshots**. The updated, tile-preserving E3 ROM must still be built and its roof appearance checked interactively.

See the living handoff at docs/NEXT_ASTRA_HANDOFF.md and E3 Actions workflow `.github/workflows/xgba-e3.yml`.
