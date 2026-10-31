import sys
from pathlib import Path
import unittest
import struct
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import xgba_e6_save as e6
import xgba_e6_box_upgrade as opt


def legacy_record(save, world, slot, sequence, current, mask, pages):
    data = bytearray(e6.BOX_DATA_SIZE)
    for index, payload in pages.items():
        assert len(payload) == e6.BOX_PAGE_SIZE
        start = index * e6.BOX_PAGE_SIZE
        data[start:start + e6.BOX_PAGE_SIZE] = payload
    prefix = struct.pack(
        "<8sHHIIIII", e6.BOX_MAGIC, e6.BOX_VERSION, world,
        sequence, current, mask, e6.BOX_DATA_SIZE, zlib.crc32(data)
    )
    header = prefix + struct.pack("<I", zlib.crc32(prefix))
    start = e6.box_slot_offset(world, slot)
    save[start:start + len(header)] = header
    save[start + len(header):start + len(header) + len(data)] = data


def sample_page(seed):
    return bytes(((i * 17 + seed) % 256 for i in range(e6.BOX_PAGE_SIZE)))


class OptimizedBoxTests(unittest.TestCase):
    def test_exact_old_save_preservation_with_world_three_page_eight(self):
        data = bytearray(e6.initialize(bytes([27]) * e6.NATIVE_SIZE + b"r" * 16))
        page1 = sample_page(3)
        page8 = bytearray(sample_page(7))
        page8[12:21] = b"ZIGZAGOON"
        page8 = bytes(page8)
        legacy_record(data, 3, 0, 12, 7, 129, {0: page1, 7: page8})
        legacy_record(data, 3, 1, 13, 7, 129, {0: page1, 7: page8})
        legacy_record(data, 20, 0, 3, 0, 1, {0: sample_page(20)})
        data = bytearray(e6.write_world(data, 3, b"world-three-progress"))
        original = bytes(data)

        migrated, worlds = opt.upgrade(original)
        self.assertEqual(worlds, 2)
        self.assertEqual(len(migrated), len(original))
        self.assertEqual(migrated[:e6.BOX_START], original[:e6.BOX_START])
        self.assertEqual(migrated[0xE20000:], original[0xE20000:])
        self.assertEqual(opt.read_meta(migrated, 3)[2], 7)
        self.assertEqual(opt.read_page(migrated, 3, 0)[2], page1)
        self.assertEqual(opt.read_page(migrated, 3, 7)[2], page8)
        self.assertEqual(opt.read_page(migrated, 20, 0)[2], sample_page(20))
        self.assertIsNone(opt.read_page(migrated, 3, 6))
        self.assertIsNone(opt.read_meta(migrated, 19))

        damaged = bytearray(migrated)
        damaged[opt.page_offset(3, 7, 1) + 32 + 100] ^= 1
        self.assertEqual(opt.read_page(damaged, 3, 7)[2], page8)

        with self.assertRaises(opt.UpgradeError):
            opt.upgrade(migrated)

    def test_bad_legacy_fails_without_erasing_data(self):
        original = bytearray(e6.initialize(bytes(e6.NATIVE_SIZE)))
        pos = e6.box_slot_offset(3, 0)
        original[pos:pos + 8] = b"BADBANK!"
        untouched = bytes(original)
        with self.assertRaises(opt.UpgradeError):
            opt.upgrade(original)
        self.assertEqual(bytes(original), untouched)

    def test_corrupt_newest_legacy_falls_back_to_older(self):
        original = bytearray(e6.initialize(bytes(e6.NATIVE_SIZE)))
        page8 = sample_page(33)
        legacy_record(original, 3, 0, 8, 7, 128, {7: page8})
        legacy_record(original, 3, 1, 9, 7, 128, {7: sample_page(44)})
        original[e6.box_slot_offset(3, 1) + 36 + 100] ^= 1
        upgraded, _ = opt.upgrade(bytes(original))
        self.assertEqual(opt.read_page(upgraded, 3, 7)[2], page8)

    def test_full_twenty_worlds_all_eight_pages(self):
        original = bytearray(e6.initialize(bytes(e6.NATIVE_SIZE)))
        for world in range(1, 21):
            pages = {}
            for page in range(8):
                pages[page] = sample_page(world + page)
            legacy_record(original, world, 0, 1, 7, 255, pages)
        converted, count = opt.upgrade(bytes(original))
        self.assertEqual(count, 20)
        for world in range(1, 21):
            self.assertEqual(opt.read_meta(converted, world)[2], 7)
            for page in range(8):
                self.assertEqual(opt.read_page(converted, world, page)[2], sample_page(world + page))

    def test_metadata_corruption_detected(self):
        original = bytearray(e6.initialize(bytes(e6.NATIVE_SIZE)))
        legacy_record(original, 3, 0, 1, 0, 1, {0: sample_page(5)})
        upgraded, _ = opt.upgrade(bytes(original))
        broken = bytearray(upgraded)
        for slot in (0, 1):
            broken[opt.meta_offset(3, slot)] ^= 3
        with self.assertRaises(opt.UpgradeError):
            opt.verify_upgrade(bytes(original), broken, {3: (0, {0: sample_page(5)})})


if __name__ == "__main__":
    unittest.main()
