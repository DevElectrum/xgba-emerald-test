#!/usr/bin/env python3
"""E5a host-side prototype for backward-compatible, dual-copy XGBA save banks.

This file format is NOT yet connected to the Emerald ROM or the XGBA emulator.
"""

import argparse
import os
from pathlib import Path
import struct
import tempfile
import zlib

NATIVE_SIZE = 128 * 1024
FILE_SIZE = 1024 * 1024
HEADER_SIZE = 4096
PRIMARY_HEADER = NATIVE_SIZE
SECONDARY_HEADER = FILE_SIZE - HEADER_SIZE
BANK_START = PRIMARY_HEADER + HEADER_SIZE
WORLD_COUNT = 20
SLOT_COUNT = 2
SLOT_SIZE = 20 * 1024
RECORD_HEADER_SIZE = 32
MAX_WORLD_DATA = SLOT_SIZE - RECORD_HEADER_SIZE
MAGIC = b"XGBAE5S\x00"
RECORD_MAGIC = b"XGBAE5W\x00"
VERSION = 1
HEADER = struct.Struct("<8sIIII")
RECORD = struct.Struct("<8sHHIIIII")


class E5SaveError(ValueError):
    pass


def check_world(world):
    if world < 1 or world > WORLD_COUNT:
        raise E5SaveError("World must be between 1 and 20")


def slot_offset(world, slot):
    check_world(world)
    if slot not in (0, 1):
        raise E5SaveError("World has exactly two slots")
    return BANK_START + ((world - 1) * SLOT_COUNT + slot) * SLOT_SIZE


def build_superblock():
    prefix = struct.pack("<8sIII", MAGIC, VERSION, NATIVE_SIZE, FILE_SIZE)
    checksum = zlib.crc32(prefix)
    return HEADER.pack(MAGIC, VERSION, NATIVE_SIZE, FILE_SIZE, checksum).ljust(
        HEADER_SIZE, b"\xFF"
    )


def initialize(native_data):
    if len(native_data) != NATIVE_SIZE:
        raise E5SaveError("Input must be exactly 128 KiB of native Emerald save bytes")
    save = bytearray(b"\xFF" * FILE_SIZE)
    save[:NATIVE_SIZE] = native_data
    header = build_superblock()
    save[PRIMARY_HEADER:PRIMARY_HEADER + HEADER_SIZE] = header
    save[SECONDARY_HEADER:SECONDARY_HEADER + HEADER_SIZE] = header
    return bytes(save)


def validate(save):
    if len(save) != FILE_SIZE:
        raise E5SaveError("E5 file must be exactly 1 MiB")

    valid = False
    expected = build_superblock()[:HEADER.size]
    for offset in (PRIMARY_HEADER, SECONDARY_HEADER):
        if save[offset:offset + HEADER.size] == expected:
            valid = True

    if not valid:
        raise E5SaveError("Neither E5 superblock is valid")
    return True


def read_slot(save, world, slot):
    offset = slot_offset(world, slot)
    block = save[offset:offset + SLOT_SIZE]
    if block == b"\xFF" * SLOT_SIZE:
        return None

    try:
        magic, version, stored_world, sequence, length, crc, header_crc, reserved = (
            RECORD.unpack(block[:RECORD_HEADER_SIZE])
        )
    except struct.error:
        return None

    if magic != RECORD_MAGIC or version != VERSION or stored_world != world:
        return None
    if sequence < 1 or length > MAX_WORLD_DATA or reserved != 0:
        return None
    if zlib.crc32(block[:24]) != header_crc:
        return None

    payload = block[RECORD_HEADER_SIZE:RECORD_HEADER_SIZE + length]
    if zlib.crc32(payload) != crc:
        return None
    return sequence, payload


def read_world(save, world):
    validate(save)
    check_world(world)
    copies = []
    for slot in (0, 1):
        candidate = read_slot(save, world, slot)
        if candidate is not None:
            copies.append((candidate[0], slot, candidate[1]))

    if copies:
        sequence, slot, payload = max(copies, key=lambda item: item[0])
        return sequence, slot, payload

    for slot in (0, 1):
        offset = slot_offset(world, slot)
        if save[offset:offset + SLOT_SIZE] != b"\xFF" * SLOT_SIZE:
            raise E5SaveError(f"World {world} has records but neither copy is valid")
    return 0, None, b""


def encode_record(world, sequence, payload):
    if len(payload) > MAX_WORLD_DATA:
        raise E5SaveError(f"World data exceeds {MAX_WORLD_DATA} bytes")
    prefix = struct.pack(
        "<8sHHIII",
        RECORD_MAGIC,
        VERSION,
        world,
        sequence,
        len(payload),
        zlib.crc32(payload),
    )
    header_crc = zlib.crc32(prefix)
    header = RECORD.pack(
        RECORD_MAGIC,
        VERSION,
        world,
        sequence,
        len(payload),
        zlib.crc32(payload),
        header_crc,
        0,
    )
    return (header + payload).ljust(SLOT_SIZE, b"\xFF")


def write_world(save, world, payload):
    validate(save)
    check_world(world)
    sequence, active_slot, previous = read_world(save, world)
    if sequence >= 0xFFFFFFFF:
        raise E5SaveError("World sequence overflow requires migration")
    inactive_slot = 0 if active_slot is None else 1 - active_slot
    offset = slot_offset(world, inactive_slot)
    changed = bytearray(save)
    changed[offset:offset + SLOT_SIZE] = encode_record(world, sequence + 1, payload)
    return bytes(changed)


def atomic_write(path, data):
    path = Path(path)
    if path.exists():
        raise E5SaveError(f"Refusing to overwrite existing output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".xgba-e5-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.link(temporary, path)
    finally:
        os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init_command = commands.add_parser("init", help="Make a 1 MiB E5 copy from a 128 KiB save")
    init_command.add_argument("native_save", type=Path)
    init_command.add_argument("output", type=Path)

    inspect_command = commands.add_parser("inspect", help="List world-bank copy status")
    inspect_command.add_argument("save", type=Path)

    put_command = commands.add_parser("put", help="Offline write to one world bank")
    put_command.add_argument("save", type=Path)
    put_command.add_argument("world", type=int)
    put_command.add_argument("data", type=Path)
    put_command.add_argument("output", type=Path)

    get_command = commands.add_parser("get", help="Export one world's payload")
    get_command.add_argument("save", type=Path)
    get_command.add_argument("world", type=int)
    get_command.add_argument("output", type=Path)

    native_command = commands.add_parser("extract-native", help="Recover untouched 128 KiB")
    native_command.add_argument("save", type=Path)
    native_command.add_argument("output", type=Path)

    args = parser.parse_args()
    if args.command == "init":
        atomic_write(args.output, initialize(args.native_save.read_bytes()))
        print(f"Created {args.output} (1 MiB; native 128 KiB preserved)")
    elif args.command == "inspect":
        save = args.save.read_bytes()
        validate(save)
        for world in range(1, WORLD_COUNT + 1):
            sequence, slot, payload = read_world(save, world)
            print(f"World {world:2d}: seq={sequence}, active={slot}, bytes={len(payload)}")
    elif args.command == "put":
        save = args.save.read_bytes()
        atomic_write(args.output, write_world(save, args.world, args.data.read_bytes()))
        print(f"Wrote World {args.world} to separate E5 file {args.output}")
    elif args.command == "get":
        _, _, payload = read_world(args.save.read_bytes(), args.world)
        atomic_write(args.output, payload)
    elif args.command == "extract-native":
        save = args.save.read_bytes()
        validate(save)
        atomic_write(args.output, save[:NATIVE_SIZE])


if __name__ == "__main__":
    main()
