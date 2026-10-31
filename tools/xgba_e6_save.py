#!/usr/bin/env python3
"""E6 save-envelope migration and dual-copy world-bank inspection.

Creates a new 16 MiB file without overwriting the input. E5 records remain
byte-for-byte in the first MiB, except for the E6 primary superblock.
The old E5 duplicate header at 0xFF000 permits offline E5 inspection.
E6 large world records start at offset 0x100000; none are initialized yet.
"""

import argparse
import os
from pathlib import Path
import struct
import tempfile
import zlib

import xgba_e5_save as e5

NATIVE_SIZE = 0x20000
E5_SIZE = 0x100000
FILE_SIZE = 0x1000000
RTC_SIZE = 16
HEADER_SIZE = 0x1000
PRIMARY_HEADER = NATIVE_SIZE
BACKUP_HEADER = FILE_SIZE - HEADER_SIZE
WORLD_START = E5_SIZE
WORLD_COUNT = 20
WORLD_SLOTS = 2
SLOT_SIZE = 0x10000
RECORD_HEADER_SIZE = 32
MAX_WORLD_DATA = SLOT_SIZE - RECORD_HEADER_SIZE
MAGIC = b"XGBAE6S\x00"
RECORD_MAGIC = b"XGBAE6W\x00"
TEMPLATE_MAGIC = b"XGBAE6T\x00"
TEMPLATE_START = 0xE20000
VERSION = 2

# E6 eight-page PC sidecar (20 worlds × 2 bank copies × 8 native PC pages).
BOX_START = 0x380000
BOX_SLOT_SIZE = 0x44000
BOX_HEADER_SIZE = 36
BOX_PAGES = 8
BOX_PAGE_SIZE = 33744
BOX_DATA_SIZE = BOX_PAGES * BOX_PAGE_SIZE
BOX_MAGIC = b"XGBAE6B\x00"
BOX_VERSION = 1
BOX_HEADER = struct.Struct("<8sHHIIIIII")
HEADER = struct.Struct("<8sIIII")
RECORD = struct.Struct("<8sHHIIIII")


class E6SaveError(ValueError):
    pass


def superblock():
    prefix = struct.pack("<8sIII", MAGIC, VERSION, NATIVE_SIZE, FILE_SIZE)
    checksum = zlib.crc32(prefix)
    return HEADER.pack(MAGIC, VERSION, NATIVE_SIZE, FILE_SIZE, checksum).ljust(
        HEADER_SIZE, b"\xFF"
    )


def initialize(source):
    if len(source) in (NATIVE_SIZE, NATIVE_SIZE + RTC_SIZE):
        native = source[:NATIVE_SIZE]
        rtc = source[NATIVE_SIZE:]
        original_e5 = e5.initialize(native + rtc)[:E5_SIZE]
    elif len(source) in (E5_SIZE, E5_SIZE + RTC_SIZE):
        e5.validate(source)
        original_e5 = source[:E5_SIZE]
        rtc = source[E5_SIZE:]
    else:
        raise E6SaveError("Input must be a 128 KiB native save or valid 1 MiB E5 save")

    result = bytearray(b"\xFF" * FILE_SIZE)
    result[:E5_SIZE] = original_e5
    block = superblock()
    result[PRIMARY_HEADER:PRIMARY_HEADER + HEADER_SIZE] = block
    result[BACKUP_HEADER:BACKUP_HEADER + HEADER_SIZE] = block
    return bytes(result) + rtc


def validate(data):
    if len(data) not in (FILE_SIZE, FILE_SIZE + RTC_SIZE):
        raise E6SaveError("E6 save must be 16 MiB, optionally with a 16-byte RTC trailer")
    prefix = superblock()[:HEADER.size]
    primary = data[PRIMARY_HEADER:PRIMARY_HEADER + HEADER.size] == prefix
    backup = data[BACKUP_HEADER:BACKUP_HEADER + HEADER.size] == prefix
    if not primary and not backup:
        raise E6SaveError("Neither E6 superblock is valid")
    return True


def template_slot_offset(slot):
    if slot not in (0, 1):
        raise E6SaveError("Template slot must be 0 or 1")
    offset = TEMPLATE_START + slot * SLOT_SIZE
    if offset + SLOT_SIZE > BACKUP_HEADER:
        raise E6SaveError("Template overlaps E6 superblock")
    return offset


def read_template_slot(data, slot):
    offset = template_slot_offset(slot)
    block = data[offset:offset + SLOT_SIZE]
    if block == b"\xFF" * SLOT_SIZE:
        return None
    if len(block) != SLOT_SIZE:
        return None
    magic, version, world, seq, size, crc, header_crc, reserved = RECORD.unpack(
        block[:RECORD_HEADER_SIZE]
    )
    if magic != TEMPLATE_MAGIC or version != VERSION or world != 0:
        return None
    if not seq or size != 53380 or reserved != 0:
        return None
    if zlib.crc32(block[:24]) != header_crc:
        return None
    payload = block[RECORD_HEADER_SIZE:RECORD_HEADER_SIZE + size]
    if zlib.crc32(payload) != crc:
        return None
    return seq, slot, payload


def read_template(data):
    choices = []
    for slot in (0, 1):
        found = read_template_slot(data, slot)
        if found is not None:
            choices.append(found)
    if choices:
        return max(choices, key=lambda item: item[0])
    if data[template_slot_offset(0):template_slot_offset(0) + SLOT_SIZE] == b"\xFF" * SLOT_SIZE:
        if data[template_slot_offset(1):template_slot_offset(1) + SLOT_SIZE] == b"\xFF" * SLOT_SIZE:
            return 0, None, b""
    raise E6SaveError("Both E6 new-game template records are damaged")


def slot_offset(world, slot):
    if not 1 <= world <= WORLD_COUNT:
        raise E6SaveError("World must be between 1 and 20")
    if slot not in (0, 1):
        raise E6SaveError("Slot must be 0 or 1")
    return WORLD_START + ((world - 1) * WORLD_SLOTS + slot) * SLOT_SIZE


def read_slot(data, world, slot):
    offset = slot_offset(world, slot)
    block = data[offset:offset + SLOT_SIZE]
    if block == b"\xFF" * SLOT_SIZE:
        return None
    if len(block) != SLOT_SIZE:
        return None
    magic, version, stored_world, sequence, size, crc, header_crc, reserved = RECORD.unpack(block[:RECORD_HEADER_SIZE])
    if magic != RECORD_MAGIC or version != VERSION or stored_world != world:
        return None
    if not sequence or size > MAX_WORLD_DATA or reserved != 0:
        return None
    if zlib.crc32(block[:24]) != header_crc:
        return None
    payload = block[RECORD_HEADER_SIZE:RECORD_HEADER_SIZE + size]
    if zlib.crc32(payload) != crc:
        return None
    return sequence, payload


def read_world(data, world):
    validate(data)
    candidates = []
    for slot in (0, 1):
        value = read_slot(data, world, slot)
        if value is not None:
            candidates.append((value[0], slot, value[1]))
    if candidates:
        return max(candidates, key=lambda entry: entry[0])
    for slot in (0, 1):
        off = slot_offset(world, slot)
        if data[off:off + SLOT_SIZE] != b"\xFF" * SLOT_SIZE:
            raise E6SaveError(f"World {world}: both slots corrupt")
    return 0, None, b""


def encode_record(world, sequence, payload):
    if len(payload) > MAX_WORLD_DATA or sequence < 1 or sequence > 0xFFFFFFFF:
        raise E6SaveError("E6 record payload or sequence out of bounds")
    prefix = struct.pack(
        "<8sHHIII", RECORD_MAGIC, VERSION, world,
        sequence, len(payload), zlib.crc32(payload)
    )
    checksum = zlib.crc32(prefix)
    record = RECORD.pack(
        RECORD_MAGIC, VERSION, world, sequence,
        len(payload), zlib.crc32(payload), checksum, 0
    )
    return (record + payload).ljust(SLOT_SIZE, b"\xFF")


def write_world(data, world, payload):
    sequence, active, previous = read_world(data, world)
    if sequence == 0xFFFFFFFF:
        raise E6SaveError("E6 sequence overflow")
    slot = 0 if active is None else 1 - active
    off = slot_offset(world, slot)
    result = bytearray(data)
    result[off:off + SLOT_SIZE] = encode_record(world, sequence + 1, payload)
    return bytes(result)


def box_slot_offset(world, slot):
    if not 1 <= world <= WORLD_COUNT or slot not in (0, 1):
        raise E6SaveError("Invalid E6 PC world or bank slot")
    off = BOX_START + ((world - 1) * 2 + slot) * BOX_SLOT_SIZE
    if off + BOX_SLOT_SIZE > BACKUP_HEADER:
        raise E6SaveError("E6 PC bank overlaps the end-of-save header")
    return off


def read_box_slot(data, world, slot):
    offset = box_slot_offset(world, slot)
    record = data[offset:offset + BOX_SLOT_SIZE]
    if record[:8] == b"\\xFF" * 8:
        return None
    if len(record) < BOX_HEADER_SIZE:
        return None
    magic, version, stored_world, seq, page, mask, size, crc, header_crc = BOX_HEADER.unpack(
        record[:BOX_HEADER_SIZE]
    )
    if (magic != BOX_MAGIC or version != BOX_VERSION or stored_world != world
            or seq < 1 or page >= BOX_PAGES or mask > 255 or not (mask & (1 << page))
            or size != BOX_DATA_SIZE):
        return None
    if zlib.crc32(record[:32]) != header_crc:
        return None
    payload = record[BOX_HEADER_SIZE:BOX_HEADER_SIZE + size]
    if zlib.crc32(payload) != crc:
        return None
    return seq, page, mask, payload


def read_box_bank(data, world):
    validate(data)
    values = []
    for slot in (0, 1):
        found = read_box_slot(data, world, slot)
        if found is not None:
            values.append((found[0], slot, found[1], found[2], found[3]))
    return max(values, key=lambda item: item[0]) if values else None


def atomic_write(output, data):
    output = Path(output)
    if output.exists():
        raise E6SaveError(f"Output already exists, refusing overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".xgba-e6-", dir=output.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, output)
    finally:
        os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    cmd = parser.add_subparsers(dest="command", required=True)
    init = cmd.add_parser("init", help="Create a separate 16 MiB E6 save from native/E5")
    init.add_argument("source", type=Path)
    init.add_argument("output", type=Path)
    inspect = cmd.add_parser("inspect", help="Report E6 banks and legacy E5 snapshots")
    inspect.add_argument("save", type=Path)
    put = cmd.add_parser("put", help="Write payload to a new E6 file for offline experiments")
    put.add_argument("save", type=Path)
    put.add_argument("world", type=int)
    put.add_argument("data", type=Path)
    put.add_argument("output", type=Path)
    get = cmd.add_parser("get", help="Export one E6 world payload")
    get.add_argument("save", type=Path)
    get.add_argument("world", type=int)
    get.add_argument("output", type=Path)

    args = parser.parse_args()
    if args.command == "init":
        atomic_write(args.output, initialize(args.source.read_bytes()))
        print(f"Created {args.output}: 16 MiB E6 copy; original untouched")
    elif args.command == "inspect":
        data = args.save.read_bytes()
        validate(data)
        template_seq, template_slot, template = read_template(data)
        print(f"E6 fresh-world template: sequence={template_seq}, "
              f"slot={template_slot}, size={len(template)}")
        for world in range(1, WORLD_COUNT + 1):
            sequence, slot, payload = read_world(data, world)
            print(f"E6 World {world:2d}: sequence={sequence}, slot={slot}, size={len(payload)}")
        import xgba_e6_box_upgrade as boxes
        for world in range(1, WORLD_COUNT + 1):
            box = read_box_bank(data, world)
            if box:
                seq, slot, page, mask, payload = box
                print(f"E6 PC v1 World {world:2d}: page={page + 1}/8, "
                      f"pages_initialized={mask.bit_count()}, seq={seq}, slot={slot}")
                continue
            metadata = boxes.read_meta(data, world)
            if metadata is not None:
                seq, slot, page = metadata
                active = boxes.read_page(data, world, page)
                if active is None:
                    raise E6SaveError(f"World {world}: v2 active PC page is unreadable")
                count = 0
                for index in range(8):
                    if boxes.read_page(data, world, index) is not None:
                        count += 1
                print(f"E6 PC v2 World {world:2d}: page={page + 1}/8, "
                      f"pages_initialized={count}, seq={seq}, slot={slot}")
        legacy = bytearray(data[:E5_SIZE])
        legacy[PRIMARY_HEADER:PRIMARY_HEADER + HEADER_SIZE] = e5.build_superblock()
        for world in range(1, WORLD_COUNT + 1):
            try:
                sequence, slot, payload = e5.read_world(legacy, world)
                if sequence:
                    print(f"Preserved E5 World {world}: seq={sequence}, bytes={len(payload)}")
            except e5.E5SaveError:
                print(f"Preserved E5 World {world}: damaged or unreadable")
    elif args.command == "put":
        data = args.save.read_bytes()
        atomic_write(args.output, write_world(data, args.world, args.data.read_bytes()))
        print(f"Wrote World {args.world} to separate E6 save {args.output}")
    elif args.command == "get":
        _, _, payload = read_world(args.save.read_bytes(), args.world)
        atomic_write(args.output, payload)


if __name__ == "__main__":
    main()
