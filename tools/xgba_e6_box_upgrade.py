#!/usr/bin/env python3
"""Offline, create-only E6 PC v1 -> v2 page-record conversion.

Close XGBA first. Never edits the source save or silently overwrites a target.
Original native flash, E5/E6 world records and RTC trailer remain byte-identical.
The v2 format keeps eight independently protected A/B PC pages per world.
"""

import argparse
from pathlib import Path
import struct
import zlib

import xgba_e6_save as e6

WORLD_STRIDE = 0x88000
PAGE_SLOT_SIZE = 0x8400
META_OFFSET = 0x84000
META_SLOT_SIZE = 0x40
PAGE_MAGIC = b"XGBAE6P\x00"
META_MAGIC = b"XGBAE6M\x00"
VERSION = 2
HEADER = struct.Struct("<8sHHBBHIIII")

assert HEADER.size == 32
assert 8 * 2 * PAGE_SLOT_SIZE + 2 * META_SLOT_SIZE <= WORLD_STRIDE
assert 32 + e6.BOX_PAGE_SIZE <= PAGE_SLOT_SIZE
assert e6.BOX_START + e6.WORLD_COUNT * WORLD_STRIDE == 0xE20000


class UpgradeError(e6.E6SaveError):
    pass


def world_offset(world):
    if world < 1 or world > e6.WORLD_COUNT:
        raise UpgradeError("World out of range")
    return e6.BOX_START + (world - 1) * WORLD_STRIDE


def page_offset(world, page, slot):
    if page not in range(8) or slot not in (0, 1):
        raise UpgradeError("Invalid page or copy")
    return world_offset(world) + (page * 2 + slot) * PAGE_SLOT_SIZE


def meta_offset(world, slot):
    if slot not in (0, 1):
        raise UpgradeError("Invalid metadata copy")
    return world_offset(world) + META_OFFSET + slot * META_SLOT_SIZE


def make_header(magic, world, page, seq, length, payload_crc):
    prefix = struct.pack(
        "<8sHHBBHIII", magic, VERSION, world, page, 0, 0,
        seq, length, payload_crc,
    )
    return prefix + struct.pack("<I", zlib.crc32(prefix))


def read_header(data, offset, magic, world, expected_page, length):
    raw = data[offset:offset + HEADER.size]
    if raw[:8] == b"\xFF" * 8:
        return None
    if len(raw) != HEADER.size:
        raise UpgradeError("Truncated record")
    values = HEADER.unpack(raw)
    oldmagic, version, oldworld, page, flags, reserved, seq, size, crc, hdrcrc = values
    if (oldmagic != magic or version != VERSION or oldworld != world
            or page != expected_page or flags or reserved or not seq
            or size != length or zlib.crc32(raw[:28]) != hdrcrc):
        return None
    return seq, crc


def read_page(data, world, page):
    candidates = []
    for slot in (0, 1):
        off = page_offset(world, page, slot)
        header = read_header(data, off, PAGE_MAGIC, world, page, e6.BOX_PAGE_SIZE)
        if header is not None:
            seq, crc = header
            payload = bytes(data[off + HEADER.size:off + HEADER.size + e6.BOX_PAGE_SIZE])
            if zlib.crc32(payload) == crc:
                candidates.append((seq, slot, payload))
    if not candidates:
        return None
    return max(candidates, key=lambda entry: entry[0])


def read_meta(data, world):
    candidates = []
    for slot in (0, 1):
        off = meta_offset(world, slot)
        for page in range(8):
            header = read_header(data, off, META_MAGIC, world, page, 0)
            if header is not None and header[1] == 0:
                candidates.append((header[0], slot, page))
                break
    return max(candidates, key=lambda entry: entry[0]) if candidates else None


def write_page(out, world, page, slot, seq, payload):
    if len(payload) != e6.BOX_PAGE_SIZE:
        raise UpgradeError("Incorrect native PokémonStorage size")
    offset = page_offset(world, page, slot)
    header = make_header(PAGE_MAGIC, world, page, seq, len(payload), zlib.crc32(payload))
    out[offset:offset + HEADER.size + len(payload)] = header + payload


def write_meta(out, world, slot, seq, page):
    offset = meta_offset(world, slot)
    out[offset:offset + HEADER.size] = make_header(
        META_MAGIC, world, page, seq, 0, 0
    )


def find_original_bank(data, world):
    choices = []
    oldslots = []
    for slot in (0, 1):
        off = e6.box_slot_offset(world, slot)
        old = data[off:off + e6.BOX_SLOT_SIZE]
        oldslots.append(old)
        value = e6.read_box_slot(data, world, slot)
        if value is not None:
            choices.append((value[0], slot, value[1], value[2], value[3]))
    if choices:
        return max(choices, key=lambda entry: entry[0])
    if all(all(byte == 0xFF for byte in block) for block in oldslots):
        return None
    raise UpgradeError(f"World {world}: old PC banks damaged or unrecognized")


def upgrade(data):
    e6.validate(data)
    result = bytearray(data)
    expected = {}
    migrated = 0

    # Read and validate ALL existing banks before touching any output bytes.
    for world in range(1, e6.WORLD_COUNT + 1):
        offset = world_offset(world)
        segment = data[offset:offset + WORLD_STRIDE]
        if PAGE_MAGIC in segment or META_MAGIC in segment:
            raise UpgradeError(f"World {world}: already uses v2 records")
        old = find_original_bank(data, world)
        if old is None:
            continue
        sequence, slot, selected_page, mask, payload = old
        if not (mask & (1 << selected_page)):
            raise UpgradeError(f"World {world}: selected page absent")
        pages = {}
        for page in range(8):
            if mask & (1 << page):
                begin = page * e6.BOX_PAGE_SIZE
                pages[page] = bytes(payload[begin:begin + e6.BOX_PAGE_SIZE])
                if len(pages[page]) != e6.BOX_PAGE_SIZE:
                    raise UpgradeError(f"World {world} page {page + 1}: truncated")
        expected[world] = selected_page, pages

    for world, (selected_page, pages) in expected.items():
        offset = world_offset(world)
        result[offset:offset + WORLD_STRIDE] = b"\xFF" * WORLD_STRIDE
        for page, payload in pages.items():
            write_page(result, world, page, 0, 1, payload)
            write_page(result, world, page, 1, 2, payload)
        write_meta(result, world, 0, 1, selected_page)
        write_meta(result, world, 1, 2, selected_page)
        migrated += 1

    verify_upgrade(data, result, expected)
    return bytes(result), migrated


def verify_upgrade(original, converted, expected):
    e6.validate(converted)
    if len(original) != len(converted):
        raise UpgradeError("Save/RTC length changed")
    # The PC sidecar allocation is the ONLY region allowed to change.
    if original[:e6.BOX_START] != converted[:e6.BOX_START]:
        raise UpgradeError("Native/E5/E6 world records changed")
    end = e6.BOX_START + e6.WORLD_COUNT * WORLD_STRIDE
    if original[end:] != converted[end:]:
        raise UpgradeError("Save metadata, unused extension or RTC changed")

    for world in range(1, e6.WORLD_COUNT + 1):
        meta = read_meta(converted, world)
        known = expected.get(world)
        if known is None:
            if meta is not None:
                raise UpgradeError(f"Unexpected v2 metadata in world {world}")
            continue
        selected_page, pages = known
        if meta is None or meta[2] != selected_page:
            raise UpgradeError(f"World {world}: selected page lost")
        for page in range(8):
            item = read_page(converted, world, page)
            if page in pages:
                if item is None or item[2] != pages[page]:
                    raise UpgradeError(f"World {world} page {page + 1}: Pokémon data changed")
                # Confirm BOTH independent A/B copies survived conversion.
                for slot in (0, 1):
                    off = page_offset(world, page, slot)
                    hdr = read_header(converted, off, PAGE_MAGIC, world, page,
                                      e6.BOX_PAGE_SIZE)
                    payload = converted[off + HEADER.size:off + HEADER.size + e6.BOX_PAGE_SIZE]
                    if hdr is None or zlib.crc32(payload) != hdr[1] or payload != pages[page]:
                        raise UpgradeError(f"World {world} page {page + 1}: copy {slot} invalid")
            elif item is not None:
                raise UpgradeError(f"World {world} page {page + 1}: unexpected data")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if args.source.resolve() == args.output.resolve():
        parser.error("Source and output MUST be different; never overwrite original")
    if args.output.exists():
        parser.error("Output exists; refusing overwrite")
    source = args.source.read_bytes()
    output, count = upgrade(source)
    e6.atomic_write(args.output, output)
    try:
        readback = args.output.read_bytes()
        verify_upgrade(source, readback, {
            world: (bank[2], {
                page: bank[4][page * e6.BOX_PAGE_SIZE:(page + 1) * e6.BOX_PAGE_SIZE]
                for page in range(8) if bank[3] & (1 << page)
            })
            for world in range(1, e6.WORLD_COUNT + 1)
            if (bank := find_original_bank(source, world)) is not None
        })
    except Exception:
        args.output.unlink()
        raise

    print(f"Verified optimized E6 save: {args.output} ({count} migrated worlds)")
    print("Original save unchanged. Close XGBA before replacing its .sav file.")


if __name__ == "__main__":
    main()
