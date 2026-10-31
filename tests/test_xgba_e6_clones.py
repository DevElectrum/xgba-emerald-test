"""Validate clone story events against the canonical Emerald map definitions."""

import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import xgba_generate_e2 as generator


class CloneEventTests(unittest.TestCase):
    def test_all_maps_keep_story_events_and_callbacks(self):
        generator.main()
        groups = json.loads((ROOT / "data/maps/map_groups.json").read_text())
        original_count = 0
        for group in groups["group_order"][:34]:
            for name in groups[group]:
                if name == "XgbaTestTown":
                    continue
                original = json.loads((ROOT / "data/maps" / name / "map.json").read_text())
                clone = json.loads((ROOT / "data/maps" / ("Xgba2_" + name) / "map.json").read_text())
                original_count += 1

                expected_scripts = original.get("shared_scripts_map", name)
                self.assertEqual(clone["shared_scripts_map"], expected_scripts, name)

                shared = original.get("shared_events_map")
                if shared is not None:
                    self.assertEqual(clone["shared_events_map"], "Xgba2_" + shared, name)
                else:
                    self.assertNotIn("shared_events_map", clone, name)

                self.assertEqual(clone.get("coord_events", []),
                                 original.get("coord_events", []), name)
                self.assertEqual(clone.get("bg_events", []),
                                 original.get("bg_events", []), name)

                original_objects = original.get("object_events", [])
                clone_objects = clone.get("object_events", [])
                self.assertGreaterEqual(len(clone_objects), len(original_objects), name)
                if name == "LittlerootTown_MaysHouse_1F":
                    for index in range(len(original_objects)):
                        old_obj = original_objects[index]
                        new_obj = clone_objects[index]
                        if old_obj.get("script") == "RivalsHouse_1F_EventScript_RivalSibling":
                            self.assertEqual(new_obj["movement_type"], "MOVEMENT_TYPE_FACE_DOWN")
                        else:
                            self.assertEqual(new_obj, old_obj, name)
                else:
                    self.assertEqual(clone_objects[:len(original_objects)], original_objects, name)

        self.assertEqual(original_count, 518)


if __name__ == "__main__":
    unittest.main()
