"""E7 high-address ROM layout and 256 MiB boundary guards."""

import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import xgba_pack_e7 as e7


class E7BoundaryTests(unittest.TestCase):
    def test_real_geometry_placements_cover_all_five_remote_boundaries(self):
        self.assertEqual(
            [e7.world_base(world) for world in e7.REMOTE_WORLDS],
            [0x04000000, 0x08000000, 0x0C000000, 0x0E000000, 0x0FF00000],
        )
        self.assertEqual(len({e7.world_base(world) for world in range(3, 21)}), 18)

    def test_exact_final_byte_probe_and_sparse_host_file(self):
        with tempfile.TemporaryFile() as f:
            f.truncate(e7.ROM_SIZE)
            for world in e7.REMOTE_WORLDS:
                offset, blob = e7.marker(world)
                self.assertEqual(len(blob), 16)
                self.assertEqual(blob[:8], e7.MARKER_MAGIC)
                f.seek(offset)
                f.write(blob)
            self.assertEqual(e7.marker(20)[0] + 16, e7.ROM_SIZE)
            for world in e7.REMOTE_WORLDS:
                offset, blob = e7.marker(world)
                f.seek(offset)
                self.assertEqual(f.read(16), blob)
            f.seek(-1, 2)
            self.assertNotEqual(f.read(1), b"\x00")

    def test_reject_overlaps_and_out_of_bounds(self):
        e7.validate_intervals([(0, 32, "native"), (64, 16, "asset")])
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            e7.validate_intervals([(0, 100, "source"), (80, 30, "overlap")])
        with self.assertRaisesRegex(ValueError, "Out of bounds"):
            e7.validate_intervals([(e7.ROM_SIZE - 8, 16, "bad")])

    def test_cpp_header_matches_generated_offsets(self):
        self.assertEqual((ROOT / "include/xgba_e7_data.h").read_text(), e7.render_header())
        engine = (ROOT / "src/overworld.c").read_text()
        self.assertIn("sXgbaE7WorldBases[worldId - XGBA_E3_FIRST_WORLD]", engine)
        game = (ROOT / "src/xgba_e7.c").read_text()
        self.assertIn("rom[j] != sXgbaE7ProbeBytes[i][j]", game)
        self.assertIn("const volatile u8 *rom", game)


if __name__ == "__main__":
    unittest.main()
