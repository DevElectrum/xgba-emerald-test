#!/usr/bin/env python3
"""Build/verify a 64 MiB Emerald ROM holding World 1 plus 19 Hoenn instances."""

import argparse
from pathlib import Path

import xgba_generate_e3 as generator
import xgba_pack_e2 as e2

OUTPUT_SIZE = 64 * 1024 * 1024
WORLD_FIRST = 3
WORLD_LAST = 20



def marker_cells(source):
    """Pick five nearby tiles with the same ground elevation and collision bits."""
    tile_a = source[(9 * 20 + 1) * 2:(9 * 20 + 1) * 2 + 2]
    tile_b = source[(12 * 20 + 9) * 2:(12 * 20 + 9) * 2 + 2]
    if tile_a == tile_b:
        raise ValueError("World marker needs two distinct ground metatiles")

    attribute_mask = 0xFC00
    attributes = int.from_bytes(tile_a, "little") & attribute_mask
    if (int.from_bytes(tile_b, "little") & attribute_mask) != attributes:
        raise ValueError("Marker tile variants must have matching collision and elevation")

    slots = []
    for y in (12, 11, 10, 9, 8):
        for x in range(6, 13):
            position = (y * 20 + x) * 2
            original = source[position:position + 2]
            if (int.from_bytes(original, "little") & attribute_mask) != attributes:
                continue
            replacement = tile_a if original != tile_a else tile_b
            slots.append((position, replacement))
            if len(slots) == 5:
                return slots
    raise ValueError("Not enough matching-attribute ground tiles for five world bits")


def world_marker(source, world):
    """Encode World 3..20 without changing metatile collision or elevation."""
    if len(source) != 20 * 20 * 2:
        raise ValueError("Unexpected cloned Littleroot dimensions")
    if not 3 <= world <= 20:
        raise ValueError(f"Invalid world for marker: {world}")

    result = bytearray(source)
    for bit, (position, replacement) in enumerate(marker_cells(source)):
        if (world - 2) & (1 << bit):
            result[position:position + 2] = replacement
    return bytes(result)

def plan(args):
    prefix, existing, used = e2.plan(args)
    clones, positions, stride_used, end = generator.layout_plan()
    if used > generator.FIRST_OFFSET:
        raise ValueError("E2 payloads would overlap the E3 world geometry")
    if end > OUTPUT_SIZE:
        raise ValueError("Twenty-world ROM would exceed 64 MiB")

    payloads = list(existing)
    for world in range(WORLD_FIRST, WORLD_LAST + 1):
        base = generator.FIRST_OFFSET + (world - WORLD_FIRST) * generator.STRIDE
        for layout, fields in zip(clones, positions):
            for source_key, (relative, expected) in zip(
                ("border_filepath", "blockdata_filepath"), fields
            ):
                source = (generator.ROOT / layout[source_key]).read_bytes()
                if source != expected:
                    raise ValueError(f"World {world} input changed: {layout['name']}")
                if layout["name"] == "Xgba2_LittlerootTown_Layout" and source_key == "blockdata_filepath":
                    source = world_marker(source, world)
                payloads.append((base + relative, source))
    expected_count = len(existing) + (WORLD_LAST - WORLD_FIRST + 1) * 441 * 2
    if len(payloads) != expected_count:
        raise ValueError("Missing a world layout payload")
    return prefix, payloads, end


def verify(args):
    prefix, payloads, end = plan(args)
    path = Path(args.output)
    if path.stat().st_size != OUTPUT_SIZE:
        raise ValueError("World ROM must be exactly 64 MiB")
    with path.open("rb") as rom:
        if rom.read(len(prefix)) != prefix:
            raise ValueError("ROM prefix, header marker, E2 pointers, or header checksum differ")
        for offset, data in payloads:
            rom.seek(offset)
            if rom.read(len(data)) != data:
                raise ValueError(f"Expanded geometry mismatch at file offset 0x{offset:08X}")
    print(
        f"E3 VERIFIED: 20 total Hoenn worlds (original, World Two, 18 additional); "
        f"{len(payloads)} checked tile/border payloads, 64 MiB cartridge, "
        f"last payload end 0x{end:08X}"
    )


def pack(args):
    if Path(args.rom).resolve() == Path(args.output).resolve():
        raise ValueError("Refusing to overwrite source Emerald")
    prefix, payloads, end = plan(args)
    with Path(args.output).open("xb") as rom:
        rom.write(prefix)
        for offset, content in payloads:
            rom.seek(offset)
            rom.write(content)
        rom.truncate(OUTPUT_SIZE)
    verify(args)
    print(f"Built {args.output} ({OUTPUT_SIZE} bytes; World 20 ends at 0x{end:08X})")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("pack", "verify"))
    parser.add_argument("--rom", default="pokeemerald.gba")
    parser.add_argument("--elf", default="pokeemerald.elf")
    parser.add_argument("--output", default="xgba-emerald-e3.gba")
    parser.add_argument("--nm", default="arm-none-eabi-nm")
    args = parser.parse_args()
    if args.command == "pack":
        pack(args)
    else:
        verify(args)


if __name__ == "__main__":
    main()
