# Astra collaboration rules: XGBA Emerald test fork

## Mandatory E(i) engineering standard: adversarial planning before coding

**Standing instruction from the user (2026-10-31):** Move fast, but anticipate optimization and error handling as part of the original design. Post-test optimization is permitted for genuine surprises, **not** as the routine second/third wave for predictable performance problems. Do not ask the user to repeatedly QA design oversights. A feature working is necessary, not sufficient, for an E(i) milestone to count as complete.

For **every new E(i), significant feature and save-format change**, complete a lightweight but substantive design gate before coding:

1. **Correctness/invariants:** specify actual user-visible behavior, state ownership, isolation of worlds and PC pages, live vs cached data, and rules that must never be violated.
2. **Performance up front:** estimate hot-path call counts and real worst-case cost in cycles, CPU operations, volatile 0x0F accesses, ROM/RAM/EWRAM/IWRAM, flash/save footprint, byte copies, CRCs and observable latency. Include full-storage and repeated-operation cases. Define a measurable budget; reject wasteful whole-bank rewrites when one page/record changes.
3. **Error/recovery up front:** analyze adversarial corruption, CRC mismatch, interrupted writes, failed migration, missing records, wrong versions, offset overlap, save/load ordering, cache invalidation, capacity exhaustion, and cross-world contamination. Preserve the last good copy and make failure behavior explicit.
4. **Compatibility first:** check E5 and already populated E6 saves, native game format, player progress, RTC, rollback and migration. Never overwrite user saves, silently make old data unreadable, or use an old ROM on an incompatible converted save. Create verifiable backup and versioned migration before deployment.
5. **Architect vs adversary:** independently challenge the initial proposal; compare at least one simpler or lower-cost alternative, explain tradeoffs and remaining assumptions. Keep this internal unless a real user decision is required.
6. **CI and acceptance:** automate deterministic correctness, capacity, failure injection, migration/rollback and performance-sensitive tests where practical. Request one concise gameplay acceptance wave with explicit expected results and a latency check, not three cycles of discovering predictable design mistakes. Do not retest user-accepted features without a new reason.
7. **Three gates:** (i) design approved against the above, (ii) implementation/build/CI and error paths validated, (iii) focused gameplay acceptance with correctness **and** performance. Status labels must distinguish plan, implementation, passing CI, and proven in-game results.

**Concrete E6 lesson:** Eight-page PC storage works, but the original implementation rewrote ~270 KiB banks repeatedly with a bitwise CRC32 and now takes **6–7 seconds at 5×** for PC page changes, while world changes take **3–4 seconds at 5×**. This is an avoidable design oversight. Next optimization should use independent page writes, faster CRC and safe preservation/migration of the already-populated E6 saves, with full-capacity and failure-mode analysis **before any optimization code**. The user approved planning, not a change in this request.


## Current priority: E7 256 MiB ROM experiment (2026-10-31)

E6 is frozen at xgba/e6-audited-baseline-20261031. User asked for E7 implemented with big steps and MUCH less time. Work only on xgba/e7-256mib; no retesting old Birch, 20-world PC or unrelated E6 systems. E7 adds actually-rendered map assets at 64/128/192/224/255 MiB while leaving E6 16 MiB save, original Flash and RTC untouched. Automated high-address tests and ONE compact gameplay acceptance (Test Town witness + World 20 rendering), then return to Grand Anthology. See latest docs/NEXT_ASTRA_HANDOFF.md. No new save migration.

## Historical priority: E6 rapid-iteration project (2026-10-31)

- **READ FIRST:** [E6 ambitious plan](docs/XGBA_E6_PLAN.md), then the [living handoff](docs/NEXT_ASTRA_HANDOFF.md). E6 implementation is IN PROGRESS on `xgba/e6-world-virtualization`; do not mistake ambitious goals for completed features. Read the companion emulator's `AGENTS.md` and handoff before emulator changes.
- The user explicitly prefers large, fast experimental leaps over exhaustive corporate-style QA. Work toward **20 independently playable Hoenn worlds + ~100 PC boxes/world stretch target**, including an approximately **16 MiB versioned save** if feasible. Accept breakage and iterate. Do not demand comprehensive tests before every step.
- Preserve proven E5 branches and user save files. E6 experimental branches have been created; backups plus minimal CI and a focused gameplay test are the preferred safety net. E5 game: `xgba/e5-expanded-save`; E5 emulator: `xgba/e5-save-expansion`. E6 branches now exist: game `xgba/e6-world-virtualization`, emulator `xgba/e6-large-save` (see plan).
- **Mandatory incremental written handoffs:** update this `AGENTS.md` when instructions change, and `docs/NEXT_ASTRA_HANDOFF.md` after each meaningful milestone, blocker, or changed plan. Keep the E6 plan current; update the emulator handoff/AGENTS whenever emulator work changes. Record exact branch/commit, changed files, CI outcomes, gameplay verification, blockers and *next step* before the chat can lose context. Distinguish "planned", "implemented" and "user tested".
- User expects **at most three copy-paste terminal commands** in nearly all test instructions: update/build, copy/migrate save only if needed, launch Qt `mgba-qt` with ROM. Two commands if the save needs no update. Local Nyx repos only change after the user pulls; GitHub commits are not local edits.
- Never touch `DevElectrum/grand-anthology` for this experiment or overwrite proven E4/E5 saves. Do not repeat user-accepted E4/E5 gameplay tests.

1. Before coding, read [docs/NEXT_ASTRA_HANDOFF.md](docs/NEXT_ASTRA_HANDOFF.md) and inspect the current branch and latest GitHub Actions result. Treat the handoff as the project's living progress log.
2. Keep `master` as the clean `pret/pokeemerald` fork baseline. Develop ROM experiments on feature branches and draft pull requests.
3. Do not modify `DevElectrum/grand-anthology`, and do not silently modify the separate emulator repo `DevElectrum/xgba`.
4. Update the living handoff after each completed or blocked milestone, before handing off, and whenever a plan/architecture changes. Include commit SHA, CI URL/status, changed files, verified results, failures and immediate next steps.
5. Do not commit or publicly upload generated copyrighted Pokémon ROM binaries, commercial BIOS files, user save files, or huge generated test images. Keep the upstream copyright and licensing notes intact.
6. Distinguish static ROM verification, emulator CPU-core tests and actual human gameplay testing. A successful build is not a claim that the map renders in a running game.
7. E0 through E5 are historical milestones; E5 storage persistence has passed actual user gameplay tests. Do not present past E0 test tasks as active blockers. E6 is the current planned milestone.
8. Use plain, maintainable code and deterministic CI where useful. The extended ROM pointer and E5 save path have already been proven; prioritize ambitious E6 integration speed over elaborate test bureaucracy.
