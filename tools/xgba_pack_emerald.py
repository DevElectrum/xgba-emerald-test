#!/usr/bin/env python3
"""Build and verify a 64 MiB XGBA Emerald cartridge with relocated map data."""

import argparse
import struct
import subprocess
from pathlib import Path

GBA_ROM_BASE = 0x08000000
XGBA_ROM_BASE = 0x10000000
GBA_MAX_BYTES = 32 * 1024 * 1024
EXTENDED_OFFSET = 32 * 1024 * 1024
ROM_SIZE = 64 * 1024 * 1024
MAP_POINTER_OFFSET = 12
HEADER_MAGIC_OFFSET = 0xB5
HEADER_COMPLEMENT_OFFSET = 0xBD
MAGIC = b"XGBA256"
LAYOUT_SYMBOL = "LittlerootTown_Layout"
BLOCKDATA_SYMBOL = "LittlerootTown_Layout_Blockdata"


def read_symbols(elf_path, nm_path):
    process = subprocess.run(
        [nm_path, "--defined-only", str(elf_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    result = {}
    for line in process.stdout.splitlines():
        fields = line.split()
        if len(fields) == 3:
            try:
                address = int(fields[0], 16)
            except ValueError:
                continue
            if fields[2] in (LAYOUT_SYMBOL, BLOCKDATA_SYMBOL):
                result[fields[2]] = address

    for name in (LAYOUT_SYMBOL, BLOCKDATA_SYMBOL):
        if name not in result:
            raise ValueError(f"Missing ELF symbol: {name}")
    return result


def rom_offset(cpu_address, length, rom_length):
    if cpu_address < GBA_ROM_BASE:
        raise ValueError(f"Invalid conventional ROM address: 0x{cpu_address:08X}")
    offset = cpu_address - GBA_ROM_BASE
    if offset + length > rom_length:
        raise ValueError(f"ROM symbol exceeds input image: 0x{cpu_address:08X}")
    return offset


def header_complement(rom):
    return (-sum(rom[0xA0:0xBD]) - 0x19) & 0xFF


def check_original(original, map_bytes, symbols):
    if len(original) <= HEADER_COMPLEMENT_OFFSET or len(original) > GBA_MAX_BYTES:
        raise ValueError("Expected an ordinary GBA ROM of at most 32 MiB")

    layout = rom_offset(symbols[LAYOUT_SYMBOL], 24, len(original))
    original_map_address = symbols[BLOCKDATA_SYMBOL]
    map_offset = rom_offset(original_map_address, len(map_bytes), len(original))
    descriptor_pointer = struct.unpack_from("<I", original, layout + MAP_POINTER_OFFSET)[0]
    if descriptor_pointer != original_map_address:
        raise ValueError(
            f"Layout pointer 0x{descriptor_pointer:08X} does not match "
            f"ELF map data symbol 0x{original_map_address:08X}"
        )
    if original[map_offset:map_offset + len(map_bytes)] != map_bytes:
        raise ValueError("Linked map data differs from data/layouts/LittlerootTown/map.bin")

    if len(map_bytes) != 20 * 20 * 2:
        raise ValueError(f"Unexpected Littleroot tile data size: {len(map_bytes)}")

    return layout


def pack(args):
    original_path = Path(args.rom).resolve()
    output_path = Path(args.output).resolve()
    if original_path == output_path:
        raise ValueError("Refusing to overwrite the original Emerald ROM")

    original = bytearray(original_path.read_bytes())
    map_bytes = Path(args.map_bin).read_bytes()
    symbols = read_symbols(args.elf, args.nm)
    layout_offset = check_original(original, map_bytes, symbols)

    # GBA map layout pointers are plain 32-bit little-endian CPU addresses.
    extended_cpu_address = XGBA_ROM_BASE + EXTENDED_OFFSET
    struct.pack_into("<I", original, layout_offset + MAP_POINTER_OFFSET, extended_cpu_address)
    original[HEADER_MAGIC_OFFSET:HEADER_MAGIC_OFFSET + len(MAGIC)] = MAGIC
    original[HEADER_COMPLEMENT_OFFSET] = header_complement(original)

    if output_path.exists():
        raise ValueError(f"Refusing to overwrite existing output: {output_path}")

    with output_path.open("xb") as output:
        output.write(original)
        output.seek(EXTENDED_OFFSET)
        output.write(map_bytes)
        output.truncate(ROM_SIZE)

    verify(args)
    print(f"Built {output_path}: {ROM_SIZE} bytes; relocated Littleroot map "
          f"to 0x{extended_cpu_address:08X}")


def verify(args):
    original = Path(args.rom).read_bytes()
    map_bytes = Path(args.map_bin).read_bytes()
    symbols = read_symbols(args.elf, args.nm)
    layout_offset = check_original(original, map_bytes, symbols)
    output_path = Path(args.output)

    if output_path.stat().st_size != ROM_SIZE:
        raise ValueError("XGBA ROM must be exactly 64 MiB for E0")

    with output_path.open("rb") as expanded:
        header_region = expanded.read(len(original))
        expanded.seek(EXTENDED_OFFSET)
        relocated_map = expanded.read(len(map_bytes))

    if header_region[HEADER_MAGIC_OFFSET:HEADER_MAGIC_OFFSET + len(MAGIC)] != MAGIC:
        raise ValueError("Missing opt-in XGBA256 cartridge marker")
    if header_region[HEADER_COMPLEMENT_OFFSET] != header_complement(header_region):
        raise ValueError("Incorrect GBA header complement checksum")
    if struct.unpack_from("<I", header_region, layout_offset + MAP_POINTER_OFFSET)[0] != (
        XGBA_ROM_BASE + EXTENDED_OFFSET
    ):
        raise ValueError("Littleroot layout is not linked to extended ROM")
    if relocated_map != map_bytes:
        raise ValueError("Extended map payload does not match original map data")

    expected = bytearray(original)
    struct.pack_into(
        "<I", expected, layout_offset + MAP_POINTER_OFFSET, XGBA_ROM_BASE + EXTENDED_OFFSET
    )
    expected[HEADER_MAGIC_OFFSET:HEADER_MAGIC_OFFSET + len(MAGIC)] = MAGIC
    expected[HEADER_COMPLEMENT_OFFSET] = header_complement(expected)
    if header_region != expected:
        raise ValueError("Unexpected modifications to the conventional Emerald ROM")

    print(f"Verified XGBA Emerald: {output_path} (64 MiB), Littleroot "
          f"layout data at 0x{XGBA_ROM_BASE + EXTENDED_OFFSET:08X}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("pack", "verify"))
    parser.add_argument("--rom", default="pokeemerald.gba")
    parser.add_argument("--elf", default="pokeemerald.elf")
    parser.add_argument("--map-bin", default="data/layouts/LittlerootTown/map.bin")
    parser.add_argument("--output", default="xgba-emerald-e0.gba")
    parser.add_argument("--nm", default="arm-none-eabi-nm")
    args = parser.parse_args()

    if args.command == "pack":
        pack(args)
    else:
        verify(args)


if __name__ == "__main__":
    main()
