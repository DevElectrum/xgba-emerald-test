# XGBA E6: rapid full-world virtualization plan

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
