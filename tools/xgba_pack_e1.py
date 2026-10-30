#!/usr/bin/env python3
"""Generate and verify E1: two distinct Emerald towns in XGBA's expanded ROM."""

import argparse
import struct
import subprocess
from pathlib import Path

BASE_ROM = 0x08000000
EXTENDED_ROM = 0x10000000
FIRST_OFFSET = 0x02000000
SECOND_OFFSET = FIRST_OFFSET + 0x1000
OUTPUT_SIZE = 64 * 1024 * 1024
POINTER_FIELD = 12
MAGIC = b"XGBA256"
MAGIC_OFFSET = 0xB5
CHECKSUM_OFFSET = 0xBD
TILE_COUNT = 20 * 20
TILE_BYTES = TILE_COUNT * 2

MAPS = (
    ("LittlerootTown_Layout", "LittlerootTown_Layout_Blockdata",
     "data/layouts/LittlerootTown/map.bin", FIRST_OFFSET),
    ("XgbaTestTown_Layout", "XgbaTestTown_Layout_Blockdata",
     "data/layouts/XgbaTestTown/map.bin", SECOND_OFFSET),
)


def symbols_from_elf(elf, nm):
    output = subprocess.run(
        [nm, "--defined-only", str(elf)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    result = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        try:
            address = int(parts[0], 16)
        except ValueError:
            continue
        result[parts[2]] = address
    return result


def addr_offset(address, size, rom_size):
    if address < BASE_ROM or address >= BASE_ROM + rom_size:
        raise ValueError(f"Unexpected GBA source address: 0x{address:08X}")
    offset = address - BASE_ROM
    if offset + size > rom_size:
        raise ValueError(f"Linked data exceeds source ROM: 0x{address:08X}")
    return offset


def fix_checksum(data):
    data[CHECKSUM_OFFSET] = (-sum(data[0xA0:0xBD]) - 0x19) & 255


def clone_variant(data):
    result = bytearray(data)
    if len(result) != TILE_BYTES:
        raise ValueError("E1 test town must remain 20 x 20 metatiles")

    # Use a known, originally present ground tile to make a visible marker.
    # This changes the test-town tile layout only, not the source Littleroot.
    mark = data[(9 * 20 + 1) * 2:(9 * 20 + 1) * 2 + 2]
    grass = data[(12 * 20 + 9) * 2:(12 * 20 + 9) * 2 + 2]
    if mark == grass:
        raise ValueError("Test marker tile is indistinguishable from the ground tile")
    for x in (9, 10, 11):
        at = (12 * 20 + x) * 2
        if data[at:at + 2] != grass:
            raise ValueError("Expected uninterrupted ground for E1 test marker")
        result[at:at + 2] = mark
    return bytes(result)


def inputs(args):
    path = Path(args.rom)
    original = path.read_bytes()
    if len(original) > FIRST_OFFSET or len(original) <= CHECKSUM_OFFSET:
        raise ValueError("Expected ordinary Emerald ROM of at most 32 MiB")

    found = symbols_from_elf(args.elf, args.nm)
    descriptors = []
    for name, map_name, file_name, target in MAPS:
        if name not in found or map_name not in found:
            raise ValueError(f"Missing map symbols: {name} or {map_name}")
        layout_at = addr_offset(found[name], 24, len(original))
        linked_map = addr_offset(found[map_name], TILE_BYTES, len(original))
        pointer = struct.unpack_from("<I", original, layout_at + POINTER_FIELD)[0]
        if pointer != found[map_name]:
            raise ValueError(f"Map pointer does not match {map_name}")
        map_bytes = Path(file_name).read_bytes()
        if len(map_bytes) != TILE_BYTES or original[linked_map:linked_map + TILE_BYTES] != map_bytes:
            raise ValueError(f"Linked map content does not match source: {file_name}")
        payload = clone_variant(map_bytes) if name.startswith("Xgba") else map_bytes
        descriptors.append((layout_at, target, payload))

    if descriptors[0][0] == descriptors[1][0]:
        raise ValueError("Original and test map layouts cannot share a descriptor")
    if descriptors[0][2] == descriptors[1][2]:
        raise ValueError("Test town must have independent visible map content")
    return original, descriptors


def expected_prefix(original, descriptors):
    prefix = bytearray(original)
    for layout_at, target, _ in descriptors:
        struct.pack_into("<I", prefix, layout_at + POINTER_FIELD, EXTENDED_ROM + target)
    prefix[MAGIC_OFFSET:MAGIC_OFFSET + len(MAGIC)] = MAGIC
    fix_checksum(prefix)
    return prefix


def verify(args):
    original, descriptors = inputs(args)
    path = Path(args.output)
    if path.stat().st_size != OUTPUT_SIZE:
        raise ValueError("Expected a 64 MiB output ROM")

    expected = expected_prefix(original, descriptors)
    with path.open("rb") as stream:
        actual = stream.read(len(expected))
        if actual != expected:
            raise ValueError("Invalid ROM header, pointers, or changed conventional ROM data")
        for _, target, payload in descriptors:
            stream.seek(target)
            if stream.read(len(payload)) != payload:
                raise ValueError(f"Wrong E1 tile payload at file offset 0x{target:08X}")
        stream.seek(FIRST_OFFSET + len(descriptors[0][2]))
        if stream.read(SECOND_OFFSET - FIRST_OFFSET - len(descriptors[0][2])) != bytes(
            SECOND_OFFSET - FIRST_OFFSET - len(descriptors[0][2])
        ):
            raise ValueError("Unexpected data between map payloads")
    print("E1 verified: two distinct map layouts in a 64 MiB XGBA cartridge")
    print("Littleroot: 0x12000000; XGBA Test Town: 0x12001000")


def pack(args):
    if Path(args.rom).resolve() == Path(args.output).resolve():
        raise ValueError("Refusing to overwrite original Emerald")
    original, descriptors = inputs(args)
    prefix = expected_prefix(original, descriptors)
    with Path(args.output).open("xb") as stream:
        stream.write(prefix)
        for _, target, payload in descriptors:
            stream.seek(target)
            stream.write(payload)
        stream.truncate(OUTPUT_SIZE)
    verify(args)
    print(f"Built {args.output} ({OUTPUT_SIZE} bytes)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("pack", "verify"))
    parser.add_argument("--rom", default="pokeemerald.gba")
    parser.add_argument("--elf", default="pokeemerald.elf")
    parser.add_argument("--output", default="xgba-emerald-e1.gba")
    parser.add_argument("--nm", default="arm-none-eabi-nm")
    args = parser.parse_args()
    if args.command == "pack":
        pack(args)
    else:
        verify(args)


if __name__ == "__main__":
    main()
