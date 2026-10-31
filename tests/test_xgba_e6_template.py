"""Immutable fresh-campaign template layout, recovery, and compatibility tests."""

import struct
import sys
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import xgba_e6_save as e6
import xgba_e6_box_upgrade as boxes


def encode_template(sequence, payload):
    crc = zlib.crc32(payload)
    prefix = struct.pack("<8sHHIII", e6.TEMPLATE_MAGIC, e6.VERSION, 0,
                         sequence, len(payload), crc)
    header = e6.RECORD.pack(e6.TEMPLATE_MAGIC, e6.VERSION, 0,
                            sequence, len(payload), crc,
                            zlib.crc32(prefix), 0)
    return (header + payload).ljust(e6.SLOT_SIZE, b"\xFF")


class TemplateTests(unittest.TestCase):
    def test_reserve_does_not_overlap_pc_worlds_or_backup_header(self):
        self.assertEqual(e6.TEMPLATE_START, 0xE20000)
        self.assertEqual(e6.TEMPLATE_START,
                         e6.BOX_START + e6.WORLD_COUNT * boxes.WORLD_STRIDE)
        self.assertLess(e6.template_slot_offset(1) + e6.SLOT_SIZE,
                        e6.BACKUP_HEADER)

    def test_blank_legacy_save_uses_existing_world_one_fallback(self):
        data = e6.initialize(bytes(e6.NATIVE_SIZE))
        self.assertEqual(e6.read_template(data), (0, None, b""))
        self.assertTrue(e6.validate(data))

    def test_complete_template_and_torn_newest_copy(self):
        data = bytearray(e6.initialize(bytes(e6.NATIVE_SIZE)))
        payload = bytes([19]) * 53380
        older = encode_template(1, payload)
        newer = encode_template(2, payload)
        first = e6.template_slot_offset(0)
        second = e6.template_slot_offset(1)
        data[first:first + len(older)] = older
        data[second:second + len(newer)] = newer
        self.assertEqual(e6.read_template(data), (2, 1, payload))
        self.assertTrue(e6.validate(data))
        data[second + e6.RECORD_HEADER_SIZE + 100] ^= 0x17
        self.assertEqual(e6.read_template(data), (1, 0, payload))
        data[first] = 0
        with self.assertRaises(e6.E6SaveError):
            e6.read_template(data)


if __name__ == "__main__":
    unittest.main()
