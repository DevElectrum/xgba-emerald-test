# E4: Save-backed, independent event state for 20 Hoenn worlds

## Scope

E4 extends the user-tested E3 geography experiment with **20 independent, save-backed prototype event banks**. It deliberately does **not** claim to isolate all Emerald story flags, trainers or encounters. Accepted E1/E2/E3 branches and Grand Anthology remain untouched.

## Native save format remains unchanged

Emerald's `struct SaveBlock1` is exactly `0x3D88` bytes (15,752). It contains an old `unused_3598[0x180]` region occupying 384 bytes at fixed offset 0x3598. E4 reuses that region without moving any other field or changing the size of `SaveBlock1`, `SaveBlock2` or `PokemonStorage`. Compile-time typedef guards assert the bank is exactly 0x180 bytes and the complete SaveBlock1 is still exactly 0x3D88.

The 384 bytes store a 4-byte version/magic value, 20 worlds × 16 bytes each, plus 60 reserved bytes. Each world's 16-byte record holds **four u16 event variables and 48 event flags (6 bytes)** plus two reserved bytes. Old E3 saves have no E4 signature; the first E4 variable/flag access initializes this bank to zero. This is a one-way experiment: copy the E3 save to a new E4 `.sav` instead of overwriting the E3 backup.

## How the game uses the banks

- `VAR_XGBA_E4_PROGRESS` through `VAR_XGBA_E4_SCORE` are at 0x40F7-0x40FA; four normal `GetVarPointer`, `VarGet`, `VarSet`, and event-script `addvar` accesses transparently use the current world's values.
- `FLAG_XGBA_E4_START` through `FLAG_XGBA_E4_END` are 0x020-0x04F. They were marked unused in the upstream game; `GetFlagPointer`, `FlagSet`, `FlagClear`, `FlagGet` now route this reserved range into the selected world's flag bits.
- The **existing E3 `VAR_XGBA_WORLD_ID`** at 0x40FF selects the active bank. Values 2-20 map to records 1-19; values 0/1 select original World's record 0. World index is read directly from the old global vars array to avoid recursive access.
- Event semantics outside these four variables and 48 flags remain ordinary Emerald global state. No more RAM/flash sectors are consumed.

## Interactive proof

In every cloned Littleroot (Worlds 2-20) there are now **three NPCs near the central area**: return scientist at (14,12), counter researcher at (16,12), and flag/counter auditor at (18,12).

1. On an E4 copy of your existing World 20 save, speak to auditor (18,12) **before** writing anything. It should say `World 20: progress 0. Local event flag: CLEAR.`
2. Talk to counter researcher (16,12) three times. Counter advances to 3 and local first-visit flag becomes SET. Auditor now says `World 20: progress 3. Local event flag: SET.`
3. Return via scientist (14,12) to XGBA Test Town. At (18,12), cycle destination to **World 3**; at (16,12), warp there.
4. In World 3, auditor should say `progress 0, CLEAR`. Talk to researcher only once; auditor should then say `progress 1, SET`.
5. Return to World 20. Auditor must still read `progress 3, SET`, completely independent of World 3.
6. Save in World 20, close XGBA, restart E4 and reload. World 20 auditor should retain `progress 3, SET`. Optionally revisit World 3 and confirm `progress 1, SET` also survived.

These tests validate both C-level event bank routing and persistence across save/reload, but are not exhaustive compatibility checks for global game progression.

## Build on Nyx

From `~/Projects/xgba-emerald-test`, first inspect `git status --short`. If `data/maps/map_groups.json` and `data/layouts/layouts.json` were modified solely by E3's generator, restore those two generated changes before switching branches. Do not reset unrelated work.

```bash
cd ~/Projects/xgba-emerald-test
git status --short
git restore data/maps/map_groups.json data/layouts/layouts.json
git fetch origin
git switch --track origin/xgba/e4-world-state
make e4
cp -n xgba-emerald-e3.sav xgba-emerald-e4.sav
~/Projects/xgba/build-xgba-gui/qt/mgba-qt ~/Projects/xgba-emerald-test/xgba-emerald-e4.gba
```

`make e4` generates both geography manifests and the runtime world layout offset header, builds modified Emerald, then packs/verifies `xgba-emerald-e4.gba` at 64 MiB. A preexisting E4 ROM must be moved aside before rebuilding, since the packer deliberately refuses overwrites. The original E3 save and ROM are unaffected.

## Next-phase design considerations

- A full 20-world copy of ordinary Emerald's thousands of progression flags and 256 ordinary variables exceeds the built-in 384-byte bank. It requires an expanded persistent save/storage format, safe migration, integrity checks, and explicit definitions of shared vs world-local progress.
- Ordinary world 2-20 map NPCs are still a neutral geography test: independent trainer/object/encounter data has not been implemented. E4 is only a controlled proof of event flag/var virtualization.
- Never claim full independent twenty-story compatibility or PC box expansion from this E4 experiment.

See the [living handoff](NEXT_ASTRA_HANDOFF.md) and `.github/workflows/xgba-e4.yml`.
