# E7 256 MiB Megascale: implemented capacity milestone

E7 is a fast, deliberately large jump from the frozen E6 audited baseline. It proves the upper ROM window using actually rendered map assets, not padding. All E6 gameplay state and its 16 MiB save format remain untouched.

## Architecture

The 256 MiB game packer tools/xgba_pack_e7.py reuses E3's verified assets and relocates all 441 layout tile/border pairs of five selected worlds to 1 MiB slots beginning at 64, 128, 192, 224 and 255 MiB. Other worlds retain E6 geometry locations. Game source uses generated include/xgba_e7_data.h world bases directly. Five offset/CRC markers occupy the final 16 bytes of those slots, including the final byte of the complete cartridge, which the Test Town witness at (3,12) checks via real CPU memory reads.

Cartridge marker remains XGBA256; save revision remains 0xE6. E7 is an experiment number, not a new save revision. No new map count, PC schema, player-state serialization, Flash1M mapping, RTC or migration is introduced.

## Design and failure bounds

The packer streams sparse output without allocating 256 MiB in Python, rejects overlapping/out-of-bounds regions and mismatched generated C headers, and verifies every native and remote tile payload byte. Its Make target packages and verifies a temporary ROM before replacing the E7 output. User saves are never modified by the build.

Runtime uses constant-time world-base lookup; the optional probe reads just 80 ROM bytes. Opening a 256 MiB ROM still entails a one-time emulator CRC over the full ROM, so cold-start latency may increase, but PC page switching and world transitions retain their existing implementation. A guest cannot rely on a stock unmodified GBA emulator for XGBA256 addresses.

The XGBA CTest suite confirms real 8/16/32-bit CPU/View reads at all five remote boundaries, including 0x1FFFFFFF, and retains the pre-existing ARM, Thumb, DMA and save checks.

## Current verification and release contract

Game E7 CI PASSED both address-plan/E6 regression tests and exact 256 MiB ROM build and byte verification: https://github.com/DevElectrum/xgba-emerald-test/actions/runs/41242174037

Emulator E7 CI PASSED CPU high-address and existing core tests: https://github.com/DevElectrum/xgba/actions/runs/41242131166

This is **CI-verified E7**, not yet in-game accepted. Only one focused user gameplay gate remains: use a disposable, copied E6 16 MiB save with E7 ROM, talk to the Test Town witness for all five windows PASS, and visit World 20 to check its real near-255-MiB geometry displays correctly with reasonable loading performance. Do not repeat any earlier E6 story or PC tests. After that return to Grand Anthology. Do not commit ROM binaries or user saves.
