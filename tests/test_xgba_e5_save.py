import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import xgba_e5_save as e5


class E5SaveTests(unittest.TestCase):
    def setUp(self):
        self.native = bytes([i % 251 for i in range(e5.NATIVE_SIZE)])
        self.save = e5.initialize(self.native)

    def test_native_save_preserved_and_file_is_one_megabyte(self):
        self.assertEqual(len(self.save), e5.FILE_SIZE)
        self.assertEqual(self.save[:e5.NATIVE_SIZE], self.native)
        self.assertTrue(e5.validate(self.save))

    def test_all_twenty_worlds_are_empty_and_distinct(self):
        self.assertEqual(e5.slot_offset(1, 0), e5.BANK_START)
        self.assertEqual(
            e5.slot_offset(20, 1) + e5.SLOT_SIZE,
            0xE9000,
        )
        self.assertLess(e5.slot_offset(20, 1) + e5.SLOT_SIZE, e5.SECONDARY_HEADER)
        for world in range(1, 21):
            self.assertEqual(e5.read_world(self.save, world), (0, None, b""))

    def test_two_worlds_survive_and_native_bytes_remain_untouched(self):
        saved = e5.write_world(self.save, 3, b"progress=1;flag=SET")
        saved = e5.write_world(saved, 20, b"progress=3;flag=SET")
        self.assertEqual(e5.read_world(saved, 3)[2], b"progress=1;flag=SET")
        self.assertEqual(e5.read_world(saved, 20)[2], b"progress=3;flag=SET")
        self.assertEqual(e5.read_world(saved, 8), (0, None, b""))
        self.assertEqual(saved[:e5.NATIVE_SIZE], self.native)
        self.assertEqual(self.save, e5.initialize(self.native))

    def test_double_buffer_alternates_and_recovers_after_corruption(self):
        first = e5.write_world(self.save, 20, b"first")
        second = e5.write_world(first, 20, b"second")
        self.assertEqual(e5.read_world(second, 20), (2, 1, b"second"))
        broken = bytearray(second)
        broken[e5.slot_offset(20, 1) + e5.RECORD_HEADER_SIZE] ^= 0x01
        self.assertEqual(e5.read_world(bytes(broken), 20), (1, 0, b"first"))

    def test_both_corrupted_copies_refuse_to_silently_reset(self):
        saved = e5.write_world(self.save, 3, b"first")
        saved = e5.write_world(saved, 3, b"second")
        broken = bytearray(saved)
        broken[e5.slot_offset(3, 0) + e5.RECORD_HEADER_SIZE] ^= 0x80
        broken[e5.slot_offset(3, 1) + e5.RECORD_HEADER_SIZE] ^= 0x40
        with self.assertRaises(e5.E5SaveError):
            e5.read_world(bytes(broken), 3)

    def test_one_superblock_corrupted_still_validates(self):
        broken = bytearray(self.save)
        broken[e5.PRIMARY_HEADER] ^= 0x01
        self.assertTrue(e5.validate(bytes(broken)))
        broken[e5.SECONDARY_HEADER] ^= 0x01
        with self.assertRaises(e5.E5SaveError):
            e5.validate(bytes(broken))

    def test_rejects_truncation_wrong_world_and_oversized_payload(self):
        with self.assertRaises(e5.E5SaveError):
            e5.initialize(self.native[:-1])
        with self.assertRaises(e5.E5SaveError):
            e5.validate(self.save[:-1])
        with self.assertRaises(e5.E5SaveError):
            e5.read_world(self.save, 21)
        with self.assertRaises(e5.E5SaveError):
            e5.write_world(self.save, 1, bytes(e5.MAX_WORLD_DATA + 1))

    def test_atomic_output_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "world.xsav"
            e5.atomic_write(target, self.save)
            self.assertEqual(target.read_bytes(), self.save)
            with self.assertRaises(e5.E5SaveError):
                e5.atomic_write(target, b"bad")
            self.assertEqual(target.read_bytes(), self.save)

    def test_maximum_payload_roundtrip(self):
        payload = bytes([i % 239 for i in range(e5.MAX_WORLD_DATA)])
        saved = e5.write_world(self.save, 1, payload)
        self.assertEqual(e5.read_world(saved, 1), (1, 0, payload))


if __name__ == "__main__":
    unittest.main()
