#!/usr/bin/env python3
"""Pack and validate E2's second Hoenn geometry beyond the 32 MiB boundary."""

import argparse
import json
import struct
import subprocess
from pathlib import Path

import xgba_pack_e1 as e1

ROOT = Path(__file__).resolve().parent.parent
LAYOUTS_FILE = ROOT / "data/layouts/layouts.json"
START = 0x02002000
OUTPUT_SIZE = 64 * 1024 * 1024


def align4(value):
    return (value + 3) & ~3


def read_symbols(path, nm):
    output = subprocess.run(
        [nm, "--defined-only", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    symbols = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 3:
            try:
                symbols[parts[2]] = int(parts[0], 16)
            except ValueError:
                pass
    return symbols


def plan(args):
    original, e1_descriptors = e1.inputs(args)
    layouts = json.loads(LAYOUTS_FILE.read_text())["layouts"]
    expanded = [x for x in layouts if x["id"].startswith("LAYOUT_XGBA2_")]
    if len(expanded) != 441:
        raise ValueError(f"E2 expects 441 generated layouts, found {len(expanded)}")

    symbols = read_symbols(args.elf, args.nm)
    prefix = e1.expected_prefix(original, e1_descriptors)
    payloads = [(target, data) for _, target, data in e1_descriptors]
    cursor = START

    for item in expanded:
        name = item["name"]
        if name not in symbols:
            raise ValueError(f"Missing cloned layout symbol: {name}")
        descriptor = e1.addr_offset(symbols[name], 24, len(original))
        width, height = struct.unpack_from("<II", original, descriptor)
        if (width, height) != (item["width"], item["height"]):
            raise ValueError(f"Unexpected dimensions for {name}")

        for field_offset, symbol_suffix, file_key in (
            (8, "_Border", "border_filepath"),
            (12, "_Blockdata", "blockdata_filepath"),
        ):
            symbol = name + symbol_suffix
            if symbol not in symbols:
                raise ValueError(f"Missing linked asset symbol: {symbol}")
            content = (ROOT / item[file_key]).read_bytes()
            if not content:
                raise ValueError(f"Empty layout asset {item[file_key]}")
            if field_offset == 12 and len(content) % 2:
                raise ValueError(f"Map tile data must have a whole number of u16 entries: {name}")
            # Some upstream unused dummy layouts have 1x1 metadata but extra
            # placeholder tile bytes. Validate exact linked bytes instead.

            source_pointer = struct.unpack_from("<I", original, descriptor + field_offset)[0]
            if source_pointer != symbols[symbol]:
                raise ValueError(f"Source descriptor pointer mismatch: {symbol}")
            source_offset = e1.addr_offset(source_pointer, len(content), len(original))
            if original[source_offset:source_offset + len(content)] != content:
                raise ValueError(f"Source ROM differs from map asset: {symbol}")

            cursor = align4(cursor)
            if cursor + len(content) > OUTPUT_SIZE:
                raise ValueError("E2 cloned layout payload exceeds 64 MiB")
            struct.pack_into(
                "<I", prefix, descriptor + field_offset, e1.EXTENDED_ROM + cursor
            )
            payloads.append((cursor, content))
            cursor += len(content)

    if len(payloads) != 2 + 441 * 2:
        raise ValueError("Missing cloned layout map or border payload")
    return prefix, payloads, cursor


def verify(args):
    prefix, payloads, used = plan(args)
    output = Path(args.output)
    if output.stat().st_size != OUTPUT_SIZE:
        raise ValueError("Output must be exactly 64 MiB")
    with output.open("rb") as stream:
        if stream.read(len(prefix)) != prefix:
            raise ValueError("Wrong ROM header, map pointers or unexpected low-ROM changes")
        for position, content in payloads:
            stream.seek(position)
            if stream.read(len(content)) != content:
                raise ValueError(f"Expanded map data mismatch at 0x{position:08X}")
    print(
        f"E2 verified: 441 cloned layouts, 882 relocated border/map assets, "
        f"plus two E1 layouts; occupied expanded region through 0x{used:08X}"
    )


def pack(args):
    if Path(args.rom).resolve() == Path(args.output).resolve():
        raise ValueError("Refusing to overwrite the original ROM")
    prefix, payloads, used = plan(args)
    with Path(args.output).open("xb") as output:
        output.write(prefix)
        for position, content in payloads:
            output.seek(position)
            output.write(content)
        output.truncate(OUTPUT_SIZE)
    verify(args)
    print(f"Built {args.output} ({OUTPUT_SIZE} bytes, used to 0x{used:08X})")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("pack", "verify"))
    parser.add_argument("--rom", default="pokeemerald.gba")
    parser.add_argument("--elf", default="pokeemerald.elf")
    parser.add_argument("--output", default="xgba-emerald-e2.gba")
    parser.add_argument("--nm", default="arm-none-eabi-nm")
    args = parser.parse_args()
    if args.command == "pack":
        pack(args)
    else:
        verify(args)


if __name__ == "__main__":
    main()
