import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import xgba_e5_save as e5
import xgba_e6_save as e6


class E6SaveTests(unittest.TestCase):
    def test_migrate_e5_and_preserve_two_world_snapshots(self):
        native = bytes([0x37]) * e5.NATIVE_SIZE
        old = e5.initialize(native)
        old = e5.write_world(old, 3, b"world three")
        old = e5.write_world(old, 20, b"world twenty")
        migrated = e6.initialize(old)
        self.assertEqual(len(migrated), e6.FILE_SIZE)
        self.assertEqual(migrated[:e6.NATIVE_SIZE], native)
        self.assertEqual(
            migrated[e5.BANK_START:e5.SECONDARY_HEADER],
            old[e5.BANK_START:e5.SECONDARY_HEADER],
        )
        self.assertTrue(e6.validate(migrated))
        old_part = bytearray(migrated[:e5.FILE_SIZE])
        old_part[e5.PRIMARY_HEADER:e5.PRIMARY_HEADER + e5.HEADER_SIZE] = e5.build_superblock()
        self.assertEqual(e5.read_world(old_part, 3)[2], b"world three")
        self.assertEqual(e5.read_world(old_part, 20)[2], b"world twenty")
        self.assertEqual(e6.read_world(migrated, 3)[0], 0)

    def test_large_world_record_and_backup(self):
        save = e6.initialize(bytes(e5.NATIVE_SIZE))
        payload = bytes([i % 251 for i in range(53380)])
        first = e6.write_world(save, 20, payload)
        seq, slot, restored = e6.read_world(first, 20)
        self.assertEqual((seq, slot, restored), (1, 0, payload))
        updated = e6.write_world(first, 20, b"second")
        self.assertEqual(e6.read_world(updated, 20), (2, 1, b"second"))
        damaged = bytearray(updated)
        damaged[e6.slot_offset(20, 1) + 32] ^= 0x11
        self.assertEqual(e6.read_world(damaged, 20), (1, 0, payload))
        self.assertEqual(e6.read_world(updated, 3), (0, None, b""))

    def test_headers_rtc_and_fail_closed(self):
        source = e5.initialize(bytes([42]) * e5.NATIVE_SIZE + bytes([13]) * 16)
        save = e6.initialize(source)
        self.assertEqual(len(save), e6.FILE_SIZE + 16)
        self.assertEqual(save[-16:], bytes([13]) * 16)
        self.assertTrue(e6.validate(save))
        damaged = bytearray(save)
        damaged[e6.PRIMARY_HEADER] ^= 3
        self.assertTrue(e6.validate(damaged))
        damaged[e6.BACKUP_HEADER] ^= 3
        with self.assertRaises(e6.E6SaveError):
            e6.validate(damaged)

    def test_invalid_input_and_oversized_record(self):
        with self.assertRaises(e6.E6SaveError):
            e6.initialize(bytes(100))
        save = e6.initialize(bytes(e5.NATIVE_SIZE))
        with self.assertRaises(e6.E6SaveError):
            e6.write_world(save, 1, bytes(e6.MAX_WORLD_DATA + 1))
        with self.assertRaises(e6.E6SaveError):
            e6.read_world(save, 21)


    def test_box_banks_dual_copy_and_112_box_layout(self):
        import struct
        import zlib

        self.assertEqual(e6.BOX_PAGES * 14, 112)
        self.assertEqual(e6.BOX_PAGE_SIZE, 33744)
        self.assertLess(e6.box_slot_offset(20, 1) + e6.BOX_SLOT_SIZE, e6.BACKUP_HEADER)
        save = bytearray(e6.initialize(bytes(e6.NATIVE_SIZE)))
        world = 3
        pages = bytearray(bytes(e6.BOX_DATA_SIZE))
        pages[0] = 23

        def write_slot(slot, sequence, active_page):
            data_crc = zlib.crc32(pages)
            prefix = struct.pack(
                "<8sHHIIIII",
                e6.BOX_MAGIC, e6.BOX_VERSION, world, sequence,
                active_page, 1 | (1 << active_page), e6.BOX_DATA_SIZE, data_crc,
            )
            header = prefix + struct.pack("<I", zlib.crc32(prefix))
            offset = e6.box_slot_offset(world, slot)
            save[offset:offset + len(header)] = header
            save[offset + len(header):offset + len(header) + len(pages)] = pages

        self.assertIsNone(e6.read_box_bank(save, world))
        write_slot(0, 1, 0)
        self.assertEqual(e6.read_box_bank(save, world)[:4], (1, 0, 0, 1))

        pages[7 * e6.BOX_PAGE_SIZE] = 99
        write_slot(1, 2, 7)
        self.assertEqual(e6.read_box_bank(save, world)[:4], (2, 1, 7, 129))
        self.assertEqual(e6.read_box_bank(save, world)[4][7 * e6.BOX_PAGE_SIZE], 99)
        save[e6.box_slot_offset(world, 1) + e6.BOX_HEADER_SIZE] ^= 0x11
        self.assertEqual(e6.read_box_bank(save, world)[:4], (1, 0, 0, 1))


if __name__ == "__main__":
    unittest.main()
