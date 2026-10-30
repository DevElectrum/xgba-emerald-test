# Astra collaboration rules: XGBA Emerald test fork

1. Before coding, read [docs/NEXT_ASTRA_HANDOFF.md](docs/NEXT_ASTRA_HANDOFF.md) and inspect the current branch and latest GitHub Actions result. Treat the handoff as the project's living progress log.
2. Keep `master` as the clean `pret/pokeemerald` fork baseline. Develop ROM experiments on feature branches and draft pull requests.
3. Do not modify `DevElectrum/grand-anthology`, and do not silently modify the separate emulator repo `DevElectrum/xgba`.
4. Update the living handoff after each completed or blocked milestone, before handing off, and whenever a plan/architecture changes. Include commit SHA, CI URL/status, changed files, verified results, failures and immediate next steps.
5. Do not commit or publicly upload generated copyrighted Pokémon ROM binaries, commercial BIOS files, user save files, or huge generated test images. Keep the upstream copyright and licensing notes intact.
6. Distinguish static ROM verification, emulator CPU-core tests and actual human gameplay testing. A successful build is not a claim that the map renders in a running game.
7. E0 targets a conservative 64 MiB ROM with Littleroot tile-layout relocated past 32 MiB, then XGBA emulator boot, normal movement, warps, events, saving and reloading.
8. Use plain, maintainable scripts and deterministic CI. Avoid changing the whole linker/map runtime before proving a single extended data pointer works.
