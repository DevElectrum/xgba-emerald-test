# XGBA E6: rapid full-world virtualization plan

## 2026-10-31 E6 playability acceleration (implemented, runtime unverified)

Commit `f09e785c` on E6 game branch changed `tools/xgba_generate_e2.py` to **restore ordinary object NPCs, trainers and BG interactions** from original Hoenn into cloned maps, except Littleroot which retains accessible lab/E4/E6 diagnostic NPCs. Automatic coordinate events and map callbacks remain neutral, as original story script warp destinations have not been fully audited/remapped. Some maps using `shared_events_map` may still have missing NPCs because shared event references are not yet resolved. This is *not* yet 20 complete story campaigns. ROM CI for this NPC change: https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41183201138 (pending at checkpoint). Earlier **full E6 C world-switch code** successfully built in https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41183020017. No E6 user gameplay acceptance yet.


## Next acceleration: 112 PC boxes per world without growing EWRAM (DESIGN, not code)

Use **eight switchable PC pages of fourteen native boxes**, yielding **112 boxes × 20 worlds = 2,240 boxes (67,200 slots)**. The normal Emerald PC UI continues to see 14 resident boxes; when switching page, save its 33,744-byte `PokemonStorage` into E6 extension and stream another page into the same EWRAM allocation. This is a far smaller code change than increasing `TOTAL_BOXES_COUNT` globally and breaking the 95%-full EWRAM.

Proposed separate dual-copy box-bank area: E6 file offset `0x380000` through `0xE1FFFF`, 20 worlds × 2 copies × `0x44000` bytes (278,528 B) each. Each copy has v2 magic + CRC32 header, active-page index, and eight 33,744-byte native storage pages (269,952 bytes total). This fits within the 16 MiB save, with a substantial reserve before E6's backup header at `0xFFF000`. Keep one page resident in `gPokemonStoragePtr` and remember active-page metadata in the box record; snapshot current page on save/exit and load the appropriate page on world entry.

Implement an initial page selector at a reachable cloned Littleroot test NPC if wiring it into every PC menu is too costly. Eventually integrate into the PC interface. **NO box-bank code exists yet; this is the next implementation target.** Preserve two-copy CRC integrity and avoid large new RAM buffers. Before coding, recheck actual `PokemonStorage` size and E6 offset math.

## Active implementation checkpoint (2026-10-31)

**E6 development HAS STARTED.** Feature branches are real: emulator `xgba/e6-large-save` and game `xgba/e6-world-virtualization`. This section supersedes the older "no E6 code started" status below; retain the original design narrative for historical context.

- **Emulator written and CI green:** 16 MiB opt-in revision E6 with complete v2 `XGBAE6S\0` superblocks (primary 0x20000, backup 0xFFF000), CRC32, and byte-addressed persistent 0x0F extension spanning save-file offsets 0x20000..0xFFFFFF. Native 128 KiB Flash1M remains unchanged. E5 1 MiB mapping remains independent. Changes to `memory.h`, `savedata.h`, `savedata.c`, `memory.c` and core tests. Emulator CI **success**: https://github.com/DevElectrum/xgba/actions/runs/41182582688.
- **Game ROM build:** `make e6` marks 64 MiB ROM revision 0xE6 and recalculates header checksum, without changing `make e5`. `tools/xgba_pack_e3.py` supports `--e6-save`. E6 save-format Python checks passed; game runtime compilation CI ongoing at time of this checkpoint.
- **E6 migration tool:** `tools/xgba_e6_save.py init OLD_E5.sav NEW_E6.sav` or from a 128 KiB native file. It refuses overwrite, retains native original byte-for-byte, old E5 world records at their original offsets and the E5 backup superblock, moves optional RTC trailer to 16 MiB end, writes duplicated E6 v2 headers. 20 E6 worlds × two **64 KiB slots**, starting at file offset 0x100000; max E6 payload 65,504 B. Host CRC and fallback tests pass in `tests/test_xgba_e6_save.py`.
- **Guest runtime state bank:** `src/xgba_e6.c` and `include/xgba_e6.h` implement byte-streamed snapshots of `SaveBlock1` (15,752 B), `SaveBlock2` (3,884 B), and current native `PokemonStorage` (33,744 B), combined 53,380 B per E6 world record, with v2 record header and CRC32. This does **not** yet add >14 PC boxes. Snapshot avoids allocating another large EWRAM block. E6 audit verifies persisted record integrity, not equality with current live RAM after intervening saves.
- **World transition experiment:** `XgbaE6SpecialLeaveWorld` checkpoints active World 2–20 before returning to XGBA Test Town, and `XgbaE6SpecialEnterWorld` restores a valid target record before the portal warp. On a fresh world it first creates/restores a baseline World 1 snapshot. Navigation bytes 0x000..0x233 of SaveBlock1 remain untouched during restore; current selected world ID is preserved; `LoadPlayerParty` and `LoadPlayerBag` are invoked after restore. Normal in-world `SAVE_NORMAL` also checkpoints E6. Edits are in `data/maps/XgbaTestTown/scripts.inc`, `data/specials.inc`, and `src/save.c`. **Unverified in running game; could be buggy.**
- **Preservation:** accepted E5 branches/saves untouched; `master` and `DevElectrum/grand-anthology` untouched. E6 is separately tagged and requires separately named `.sav` generated from an E5 copy. No E6 gameplay tests have been requested or passed yet.
- **Outstanding heavy goals:** restore story NPCs/events to cloned Hoenn, support >14 boxes in streamed PC storage, achieve 20 playable worlds, migrate/repair edge-case state, check normal save/exit/warp behavior. The user wants fast iteration and focused smoke tests, not a production QA matrix.

**Suggested minimal user smoke test only after game CI builds:** build emulator and E6 ROM on respective new branches; make an untouched E6 save from E5 via the copy-only migration tool; launch Qt XGBA. Switch World 20 → World 3 → World 20, checking party/items/flags; save, close and reopen, repeat. Never overwrite `xgba-emerald-e5.sav`. Use the user's 3-command presentation preference.


**Status (2026-10-31): DESIGN APPROVED IN CONVERSATION; NO E6 IMPLEMENTATION HAS STARTED.** Do not mistake proposed scope for working code. This is a personal passion project. The user explicitly prefers ambitious steps, rapid iteration and tolerable setbacks over exhaustive QA. Motto: **Regieleki, speed is god**. Preserve rollback copies and run focused smoke tests, but do not slow development with production-grade test matrices.

## Where we are

- Repositories: `DevElectrum/xgba` (mGBA-derived emulator) and `DevElectrum/xgba-emerald-test` (pret/pokeemerald test game).
- Accepted emulator baseline: `xgba/e5-save-expansion`; accepted game baseline: `xgba/e5-expanded-save`. Keep `master` and `DevElectrum/grand-anthology` untouched.
- E3: one original Hoenn plus nineteen selectable physical cloned Hoenn layouts in a 64 MiB XGBA-tagged ROM. Most cloned story NPCs/events are deliberately neutralized; do not claim 20 playable campaigns yet.
- E4: 20 separate 16-byte world event prototypes (4 u16 vars, 48 flags), in a 384-byte formerly unused area of native SaveBlock1. World 3 and World 20 separately retained values after cold restart in user gameplay.
- E5: opt-in 1 MiB persistent save with original 128 KiB Flash1M preserved; 896 KiB extension accessed via byte operations at 0x0F000000. Twenty worlds, two 20 KiB CRC-checked record slots/world. User verified World 3 and World 20 E5 snapshots, cross-world reads, native save, emulator exit, cold restart and re-audit. E5 does NOT already provide independent real full game saves or expanded boxes.
- E5 game-side convenience: Test Town NPC (18,12) was changed from 19-dialogue world cycling to an Emerald scrollable selection list for Worlds 2–20 plus Exit. Next scientist at (16,12) warps to selected destination. New menu code is committed; user has not explicitly confirmed a post-change gameplay menu test.

## E6: one large aggressive experimental milestone

**Objective:** make all 20 Hoenns independently playable and provide greatly expanded Pokémon PC storage in the same E6 development effort. Accept partial progress and fix setbacks quickly. The earlier conservative flags-only E6 plan has been superseded.

1. **Emulator save expansion:** propose 16 MiB persistent `.sav` envelope, with explicitly versioned E6 tag/header/format and extension mapping via 0x0F. Audit byte address limits, host file mapping, write flushing, header validation, RTC placement and migration. The 16 MiB value is a target, not something E5 already supports. Preserve the original native 128 KiB region and do not silently reinterpret old E5 files as E6.
2. **World state virtualization:** evaluate serialization/switching of SaveBlock1 (15,752 B), SaveBlock2 (3,884 B), PokemonStorage (33,744 B), and appropriate party/current-map/runtime fields. Combined static structs are ~53 KiB per world, but blindly swapping both SaveBlocks is hazardous: distinguish a small shared global meta layer (world selector, transition bookkeeping, perhaps chosen trainer profile) from world-local gameplay. World switching must be atomic at a safe warp boundary: save outgoing state, load incoming state, establish destination map and player position, then let normal map entry resume. Never swap a live save while leaving a stale warp/camera/RAM pointer in use.
3. **Playable cloned worlds:** restore cloned map trainers, scripts, events, encounters and sensible per-world warp/script references. Treat this as an integration challenge, not an already completed cloning job. Check original World 1 remains usable.
4. **Expanded PC boxes, same milestone:** target ~100 boxes per world as an aggressive stretch goal (2,000 total). This requires reworking 14-box UI assumptions, indices and storage access, plus streaming/on-demand loading; disk capacity alone does not create enough GBA EWRAM or enlarge current `PokemonStorage`. Current EWRAM ~95% occupied. Size/layout/protocol must be designed before assuming 100 boxes fit.
5. **Fast acceptance:** spot-check different parties/progress in World 3 versus World 20, retrieve Pokémon from a box >14, then native save, close XGBA, relaunch and confirm. Add the smallest CI/compiler/format checks that catch obvious breakage. Do not demand exhaustive map-by-map verification or 100 edge-case checks.

## Branch / file discipline

- Create new experimental branches **when implementation begins**: emulator `xgba/e6-large-save` from `xgba/e5-save-expansion`, game `xgba/e6-world-virtualization` from `xgba/e5-expanded-save`. These branch names are proposed; they do not exist merely because they appear here.
- Don't overwrite the user's proven E4 or E5 `.sav` or ROM. Create an E6 sibling basename and E6 conversion tool, backing up a native and E5 save; make any migration explicit.
- Never commit generated ROMs, save files or copyrighted binaries; never edit `DevElectrum/grand-anthology` during XGBA experiment.
- Keep accepted branch histories intact and prefer drafts/feature branches for risky changes.
- **The user's preferred terminal UX is almost always three commands:** (1) update and rebuild local repos, (2) copy/migrate save if applicable, (3) run Qt XGBA with the ROM. If no save conversion, give two commands. Avoid shell-command walls and ask for terminal output only on failures.

## Handoff obligation for every Astra

Treat this document as the current strategic plan and `docs/NEXT_ASTRA_HANDOFF.md` as the live factual journal. Update `AGENTS.md`, `docs/NEXT_ASTRA_HANDOFF.md` and this E6 plan when architectural choices change; update the *emulator* handoff and agent instructions whenever emulator changes too. Write a short checkpoint after **each meaningful code/CI/test milestone or blocker**, not only at the end of the chat. In each checkpoint include branch, exact commits/files, CI links and outcomes, user gameplay results versus unverified claims, known issues, next concrete step and the working copy-safe test commands. Push/commit checkpoints before approaching conversation length limits. The user is on Nyx locally; GitHub commits are not magically synchronized to local files until `git pull`.

If chat context disappears, read both repos' `AGENTS.md` and handoffs, then inspect branch HEADs and Actions; continue from verified state rather than redoing accepted E3/E4/E5 tests.
