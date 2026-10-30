# XGBA Emerald E0: 64 MiB map relocation experiment

This isolated experiment starts from the `pret/pokeemerald` source tree. It proves that a **real Emerald map layout** can be fetched from XGBA's extended ROM mapping instead of the traditional 32 MiB cartridge space.

## Scope

- Upstream `master` remains unmodified.
- Experiment branch: `xgba/e0-expanded-layout`
- XGBA emulator validation branch: `DevElectrum/xgba` / `xgba/p0-validation-20261030`
- The first experiment **relocates** the existing Littleroot Town tile layout. It does not yet create a separately accessible cloned town or a second Hoenn region.

## Build and pack

Install the ordinary prerequisites from upstream `INSTALL.md`, including agbcc, GNU Arm binutils and the asset-building tools.

```bash
make -j2 all

python3 tools/xgba_pack_emerald.py pack \
  --rom pokeemerald.gba \
  --elf pokeemerald.elf \
  --map-bin data/layouts/LittlerootTown/map.bin \
  --output xgba-emerald-e0.gba

python3 tools/xgba_pack_emerald.py verify \
  --rom pokeemerald.gba \
  --elf pokeemerald.elf \
  --map-bin data/layouts/LittlerootTown/map.bin \
  --output xgba-emerald-e0.gba
```

Outputs are ignored by Git (`*.gba`); do not commit or redistribute generated Pokémon ROM images.

## Cartridge design

- Size: **64 MiB** / 67,108,864 bytes.
- XGBA header marker: ASCII `XGBA256` at ROM offsets `0xB5..0xBB`. Header complement byte `0xBD` is recalculated.
- Source map: `data/layouts/LittlerootTown/map.bin`, expected 20 × 20 × 2 = **800 bytes**.
- Expanded map target: file offset `0x02000000` (32 MiB), CPU address `0x12000000`.
- Original `LittlerootTown_Layout` structure lives in conventional ROM; only its 4-byte `map` field (at byte offset 12 within the descriptor) is repointed.
- Other layout fields (dimensions, borders, primary/secondary tilesets) remain as they were, and the source ROM is never changed.
- The packer uses `arm-none-eabi-nm` on `pokeemerald.elf` to locate the symbols and refuses to patch if the descriptor pointer or linked map bytes do not match.

## Verification gates

Static validation checks the exact output size, header marker and checksum, payload contents, descriptor pointer, and absence of unexpected mutations to the conventional-ROM prefix.

**Static validation is not the same as gameplay verification.** E0's next manual gate is to boot the resulting ROM with XGBA, reach Littleroot, walk, interact, warp, save, exit and reload. Ordinary mGBA and physical GBAs cannot provide the extended `0x12000000` mapping.

GitHub Actions workflow `XGBA Emerald E0` builds the ROM and performs static verification but does not upload the generated copyrighted cartridge.

For current status, exact commits, and next steps, read [the living Astra handoff](NEXT_ASTRA_HANDOFF.md).
