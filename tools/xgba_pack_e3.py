#!/usr/bin/env python3
"""Build/verify a 64 MiB Emerald ROM holding World 1 plus 19 Hoenn instances."""

import argparse
from pathlib import Path

import xgba_generate_e3 as generator
import xgba_pack_e2 as e2

OUTPUT_SIZE = 64 * 1024 * 1024
WORLD_FIRST = 3
WORLD_LAST = 20




def plan(args):
    prefix, existing, used = e2.plan(args)
    if getattr(args, "e5_save", False) and getattr(args, "e6_save", False):
        raise ValueError("Choose E5 or E6 save format, not both")
    if getattr(args, "e5_save", False) or getattr(args, "e6_save", False):
        prefix = bytearray(prefix)
        if bytes(prefix[0xB5:0xBC]) != b"XGBA256":
            raise ValueError("E5/E6 ROM must retain the XGBA256 cartridge tag")
        prefix[0xBC] = 0xE6 if getattr(args, "e6_save", False) else 0xE5
        prefix[0xBD] = (-0x19 - sum(prefix[0xA0:0xBD])) & 0xFF
        prefix = bytes(prefix)
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
    parser.add_argument("--e5-save", action="store_true", help="Opt in to E5 extended save mapping (ROM revision E5)")
    parser.add_argument("--e6-save", action="store_true", help="Opt in to E6 16 MiB save mapping (ROM revision E6)")
    args = parser.parse_args()
    if args.command == "pack":
        pack(args)
    else:
        verify(args)


if __name__ == "__main__":
    main()
