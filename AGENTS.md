# Astra collaboration rules: XGBA Emerald test fork

## Current priority: E6 rapid-iteration project (2026-10-31)

- **READ FIRST:** [E6 ambitious plan](docs/XGBA_E6_PLAN.md), then the [living handoff](docs/NEXT_ASTRA_HANDOFF.md). The plan is not implemented yet. Read the companion emulator's `AGENTS.md` and handoff before emulator changes.
- The user explicitly prefers large, fast experimental leaps over exhaustive corporate-style QA. Work toward **20 independently playable Hoenn worlds + ~100 PC boxes/world stretch target**, including an approximately **16 MiB versioned save** if feasible. Accept breakage and iterate. Do not demand comprehensive tests before every step.
- Preserve proven E5 branches and user save files. Create separate E6 branches when development starts; backups plus minimal CI and a focused gameplay test are the preferred safety net. E5 game: `xgba/e5-expanded-save`; E5 emulator: `xgba/e5-save-expansion`. E6 branch names are proposals only (see plan).
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
