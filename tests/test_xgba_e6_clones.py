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
                expected_objects = original_objects
                if name == "LittlerootTown":
                    # Clone return portal must replace the original World 1
                    # portal at (14, 12), not overlap it.
                    expected_objects = [
                        obj for obj in original_objects
                        if obj.get("script") != "LittlerootTown_EventScript_XgbaPortal"
                    ]
                    at_portal = [
                        obj for obj in clone_objects
                        if obj.get("x") == 14 and obj.get("y") == 12
                    ]
                    self.assertEqual(len(at_portal), 1)
                    self.assertEqual(
                        at_portal[0]["script"],
                        "Xgba2Littleroot_EventScript_Return"
                    )
                    self.assertEqual(
                        sum(obj.get("script") == "Xgba2Littleroot_EventScript_Return"
                            for obj in clone_objects), 1
                    )
                    self.assertFalse(any(
                        obj.get("script") == "LittlerootTown_EventScript_XgbaPortal"
                        for obj in clone_objects
                    ))
                self.assertGreaterEqual(len(clone_objects), len(expected_objects), name)
                if name == "LittlerootTown_MaysHouse_1F":
                    for index in range(len(original_objects)):
                        old_obj = original_objects[index]
                        new_obj = clone_objects[index]
                        if old_obj.get("script") == "RivalsHouse_1F_EventScript_RivalSibling":
                            self.assertEqual(new_obj["movement_type"], "MOVEMENT_TYPE_FACE_DOWN")
                        else:
                            self.assertEqual(new_obj, old_obj, name)
                else:
                    self.assertEqual(clone_objects[:len(expected_objects)], expected_objects, name)

        self.assertEqual(original_count, 518)

    def test_every_cloned_warp_and_connection_stays_in_its_world(self):
        generator.main()
        groups = json.loads((ROOT / "data/maps/map_groups.json").read_text())
        original_count = 0
        total_warps = 0
        total_connections = 0

        for group in groups["group_order"][:34]:
            for name in groups[group]:
                if name == "XgbaTestTown":
                    continue

                original_count += 1
                original = json.loads((ROOT / "data/maps" / name / "map.json").read_text())
                clone = json.loads((ROOT / "data/maps" / ("Xgba2_" + name) / "map.json").read_text())

                for index, source in enumerate(original.get("warp_events", [])):
                    expected = dict(source)
                    if expected["dest_map"] not in ("MAP_DYNAMIC", "MAP_UNDEFINED"):
                        expected["dest_map"] = generator.clone_map_id(expected["dest_map"])
                    actual = clone.get("warp_events", [])[index]
                    self.assertEqual(actual, expected, (name, "warp", index))
                    total_warps += 1

                self.assertEqual(len(clone.get("warp_events", [])),
                                 len(original.get("warp_events", [])), name)

                for index, source in enumerate(original.get("connections") or []):
                    expected = dict(source)
                    expected["map"] = generator.clone_map_id(expected["map"])
                    actual = (clone.get("connections") or [])[index]
                    self.assertEqual(actual, expected, (name, "connection", index))
                    total_connections += 1

                self.assertEqual(len(clone.get("connections") or []),
                                 len(original.get("connections") or []), name)

        self.assertEqual(original_count, 518)
        self.assertGreater(total_warps, 1000)
        self.assertGreater(total_connections, 100)


    def test_story_layout_changes_select_same_world_geometry(self):
        generator.main()
        layouts = json.loads((ROOT / "data/layouts/layouts.json").read_text())["layouts"]
        self.assertEqual(len(layouts), 883)
        self.assertEqual(layouts[441]["id"], "LAYOUT_XGBA_TEST_TOWN")

        for index in range(441):
            original = layouts[index]
            clone = layouts[442 + index]
            expected_id = "LAYOUT_XGBA2_" + original["id"][len("LAYOUT_"):]
            self.assertEqual(clone["id"], expected_id, index)
            self.assertEqual(clone["name"], "Xgba2_" + original["name"], index)

        engine = (ROOT / "src/overworld.c").read_text()
        self.assertIn("mapLayoutId < XGBA_E3_FIRST_LAYOUT_ID - 1", engine)
        self.assertIn("mapLayoutId += XGBA_E3_FIRST_LAYOUT_ID - 1;", engine)


if __name__ == "__main__":
    unittest.main()
