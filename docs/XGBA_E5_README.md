# E5: Expand XGBA save storage without compromising E4

**Status (2026-10-30): E5 experimental branches created; 1 MiB save-format prototype and automated corruption-recovery tests pass. E5 gameplay integration is NOT accepted yet.**

## Existing save-sector audit

Ordinary Pokémon Emerald uses a 128 KiB / 32-sector flash save. Per `src/save.c` and `include/save.h`:

| Sectors | Purpose |
|---|---|
| 0-13 | Normal game save, alternating slot A |
| 14-27 | Normal game save, alternating slot B |
| 28-29 | Hall of Fame |
| 30 | Trainer Hill |
| 31 | Recorded Battle |

**There are no unused standard flash sectors.** Stealing sectors 28-31 would regress native gameplay. E4 already uses the only carefully repurposed 384 bytes of spare SaveBlock1 space; enlarging SaveBlock1 inside existing 4-sector capacity is not acceptable.

## E5 save envelope: 1 MiB + optional 16-byte RTC trailer

E5 separates old, accepted game data from expanded world history:

| Offset (hex) | Length | Use |
|---|---:|---|
| 00000-1FFFF | 128 KiB | Original byte-for-byte Emerald save |
| 20000-20FFF | 4 KiB | E5 primary superblock (magic, version, sizes, CRC) |
| 21000-E8FFF | 800 KiB | Twenty independent worlds, two 20 KiB slots per world |
| E9000-FEFFF | 88 KiB | Reserved future expansion / recovery space |
| FF000-FFFFF | 4 KiB | E5 duplicate superblock |
| 100000-10000F | optional 16 B | mGBA RTC trailer, retained in its proper new location |

Each world has two independently verifiable 20 KiB records, with sequence number, world ID, payload length, record-header CRC32 and payload CRC32. The payload can hold up to **20,448 bytes**. The newest valid copy is selected, with automatic fallback to the older copy if the newest is damaged; both corrupt copies produce an explicit error rather than silently erasing history. This is **format-level** validation so far, not yet an in-game transactional protocol.

## E5 live guest API work (2026-10-31)

The E5 test branch now contains `src/xgba_e5.c` and `include/xgba_e5.h`.
The guest probes both 24-byte v1 superblocks, checks the cartridge's XGBA256/E5 opt-in header, and **never writes 0x0F memory until a complete superblock matches**.
The API reads and writes bytewise through the emulator's experimental 896 KiB save window; it does not assume 16-bit/32-bit writes are supported.
Each world keeps two 20 KiB slots with the host-tool-compatible record layout, sequence number, header CRC32, payload CRC32 and newest-valid-copy selection.
Writes invalidate only the inactive slot, fill its payload, then write the record header, magic last. This supports fallback to a previously complete copy but **does not constitute a guarantee against sudden power loss or OS write reordering**.

The clone generator adds two E5-only test NPCs to each World 2–20 Littleroot at (20,12) and (22,12).
The first writes a 16-byte snapshot of the current E4 world's four prototype variables and 48 flags; the second reads the newest E5 record and checks it against live E4 RAM without modifying storage.
The original three E4 NPCs and world-selection behavior remain.
The original E4 state always continues to reside in standard SaveBlock1 and normal Emerald flash. E5 snapshotting is explicit and does not replace native saving.
This is **not** a full per-world save migration or independent storyline implementation.

### Live acceptance protocol (after the E5 ROM build CI passes)

1. Preserve the user's working E4 ROM and `.sav` **as independent backups**. Do not run E5 against that save basename.
2. On the E5 branch, build `make e5`. If the intended E5 ROM filename already exists, move the old experimental artifact aside first; the packer refuses accidental replacement.
3. Use `python3 tools/xgba_e5_save.py init E4_BACKUP.sav xgba-emerald-e5.sav` to create a fresh 1 MiB E5 save file. It refuses overwrites and leaves its input unchanged.
4. Launch `xgba-emerald-e5.gba` with the **E5 branch** of the emulator, preferably the Qt GUI built from the E5 branch. Confirm original E4 progress remains before testing extension writes.
5. In World 20, talk to the new writer (20,12), then auditor (22,12), expecting success and match. Do the same in World 3. Revisit both without modifying E4 counters; auditors must agree.
6. Save normally, fully exit the emulator, reopen, and audit World 20 and World 3 again.
7. Inspect the resulting `.sav` with `python3 tools/xgba_e5_save.py inspect xgba-emerald-e5.sav`; both world records should be valid. Any offline corruption test must run on **another copy**, not on the primary E5 experiment.

No manual user test is requested until both latest branch builds succeed. Emulator unit tests are not a substitute for a full gameplay save/exit/restart.

## Two isolated branches

- **Test ROM and host format:** `DevElectrum/xgba-emerald-test`, branch `xgba/e5-expanded-save` based on accepted E4. `tools/xgba_e5_save.py` creates/verifies/mutates E5 save copies *offline*, and `tests/test_xgba_e5_save.py` covers corruption recovery, 20-way isolation, 128 KiB preservation, overwrite refusal and RTC trailer migration.
- **Emulator bridge:** `DevElectrum/xgba`, branch `xgba/e5-save-expansion` based on accepted `xgba/p1-fast-forward`. It experiments with a 1 MiB mapping of an E5-formatted save and an additional **896 KiB linear writeable save window** visible to GBA code at `0x0F000000..0x0F0DFFFF`.
- E5 uses **explicit opt-in**: the ROM must contain the existing `XGBA256` cartridge tag, have ROM revision byte `0xBC = 0xE5`, and the 1 MiB save file must contain E5's superblock at native file offset `0x20000`. Otherwise the emulator stays with standard flash and refuses extended writes. Ordinary `0x0E000000` flash commands remain in the standard first 128 KiB.
- E5 revision is added in the ROM packer via `--e5-save` and a **recomputed GBA header checksum**; `make e5` creates `xgba-emerald-e5.gba` separately from E4.

## Safe offline prototype: no live game dependencies

From `xgba-emerald-test` branch `xgba/e5-expanded-save`, a 128 KiB E4 save (or 128 KiB + 16-byte RTC trailer) can be copied into an E5 envelope with:

```bash
python3 tools/xgba_e5_save.py init E4_COPY.sav E5_NEW.sav
python3 tools/xgba_e5_save.py inspect E5_NEW.sav
```

These commands **refuse to overwrite** any existing output. They are currently for **format experiments only**. The original E4 ROM and save must not be changed or deleted. No one needs to run these commands until the game-side bridge is ready.

Other offline commands: `put E5_INPUT world payload_file E5_NEW_OUTPUT`, `get E5_INPUT world output`, `extract-native E5_INPUT ORIGINAL_SAVE_OUTPUT`. Every `put` writes a new file, never edits an existing one.

## Acceptance boundary and next tasks

1. Confirm emulator CI and tagged game ROM CI compile and verify. The dedicated host Python format CI has already passed.
2. Add a real **GBA-side E5 storage API** with a version/feature probe, E4-to-E5 bank migration and a small controlled in-game write/read NPC. **No bank write before the emulator reports valid E5 extension support.**
3. End-to-end test on Nyx using a **separately copied E5 save**, never the accepted E4 save: native Emerald save/reload, E5 World 3/20 distinct payloads, repeated save/exit/restart and recovery after intentionally corrupting only an offline copy.
4. Design eventual world-specific progression snapshots, world-transition synchronization and crash-safe commit ordering. All E4 world flags and counters should continue to work unchanged. PC box and complete trainer/story isolation are separate later milestones.
5. The E5 emulator bridge is experimental, not general GBA hardware behavior: it repurposes the normally mirrored 0x0F save region only for explicitly opted-in XGBA ROMs.

See `docs/NEXT_ASTRA_HANDOFF.md` for current E5 status and CI links. Never modify `DevElectrum/grand-anthology` as part of XGBA experiments.
