"""E6 world-address isolation and portal wiring regression tests."""

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import xgba_e6_save as e6


class WorldIsolationTests(unittest.TestCase):
    def test_twenty_distinct_world_records_and_corrupt_latest_fallback(self):
        data = bytearray(e6.initialize(bytes(e6.NATIVE_SIZE)))
        for world in range(1, 21):
            old_payload = bytes([world]) * 53380
            new_payload = bytes([world + 50]) * 53380
            old_record = e6.encode_record(world, 1, old_payload)
            new_record = e6.encode_record(world, 2, new_payload)
            first_offset = e6.slot_offset(world, 0)
            second_offset = e6.slot_offset(world, 1)
            data[first_offset:first_offset + len(old_record)] = old_record
            data[second_offset:second_offset + len(new_record)] = new_record

        for world in range(1, 21):
            sequence, slot, payload = e6.read_world(data, world)
            self.assertEqual(sequence, 2)
            self.assertEqual(slot, 1)
            self.assertEqual(payload, bytes([world + 50]) * 53380)

        last = e6.slot_offset(20, 1) + 32
        data[last] ^= 0x80
        sequence, slot, payload = e6.read_world(data, 20)
        self.assertEqual(sequence, 1)
        self.assertEqual(slot, 0)
        self.assertEqual(payload, bytes([20]) * 53380)
        self.assertEqual(e6.read_world(data, 19)[2], bytes([69]) * 53380)

    def test_world_one_portals_and_destination_selection_wired(self):
        original = (ROOT / "data/maps/LittlerootTown/scripts.inc").read_text()
        lab = (ROOT / "data/maps/XgbaTestTown/scripts.inc").read_text()
        engine = (ROOT / "src/xgba_e6.c").read_text()
        travel = (ROOT / "src/overworld.c").read_text()
        self.assertIn("special XgbaE6SpecialLeaveWorldOne", original)
        self.assertIn("special XgbaE6SpecialReturnToWorldOne", lab)
        self.assertIn("copyvar VAR_XGBA_TARGET_WORLD, VAR_RESULT", lab)
        self.assertIn("world = VarGet(VAR_XGBA_TARGET_WORLD);", engine)
        self.assertIn("VarSet(VAR_XGBA_WORLD_ID, world);", engine)
        self.assertIn("XgbaE6NormalizeWarp(&sWarpDestination);", travel)


if __name__ == "__main__":
    unittest.main()
