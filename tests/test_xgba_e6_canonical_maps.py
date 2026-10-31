"""Source regression guards for canonical Hoenn map-table lookups.

Cloned worlds occupy map groups 34..67; normal Hoenn script tables still use
groups 0..33. These checks protect high-impact special cases without changing
live warp IDs or game state.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def source(name):
    return (ROOT / "src" / name).read_text()


class CanonicalMapSourceTests(unittest.TestCase):
    def test_helper_is_bounded_to_the_thirty_four_clone_groups(self):
        helper = (ROOT / "include/xgba_map_compat.h").read_text()
        self.assertIn("group >= 34 && group < 68", helper)
        self.assertIn("return group - 34;", helper)
        self.assertIn("return group;", helper)

    def test_center_save_and_reloads_recognize_cloned_maps(self):
        saved = source("save_location.c")
        self.assertIn(
            "(XgbaCanonicalMapGroup(gSaveBlock1Ptr->location.mapGroup) << 8)",
            saved,
        )
        specials = source("field_specials.c")
        self.assertIn("bool8 InPokemonCenter(void)", specials)
        self.assertIn("bool8 UsedPokemonCenterWarp(void)", specials)
        self.assertIn(
            "XgbaCanonicalMapGroup(gLastUsedWarp.mapGroup) << 8", specials
        )

    def test_rematches_and_battle_terrain_match_original_world_tables(self):
        battles = source("battle_setup.c")
        self.assertEqual(
            battles.count("table[i].mapGroup == XgbaCanonicalMapGroup(mapGroup)"),
            3,
        )
        self.assertIn(
            "XgbaCanonicalMapGroup(gSaveBlock1Ptr->location.mapGroup)"
            " == MAP_GROUP(MAP_ROUTE113)",
            battles,
        )

    def test_story_music_map_and_special_checks_use_canonical_identity(self):
        overworld = source("overworld.c")
        self.assertIn("XgbaCanonicalMapGroup(warp->mapGroup) == 0", overworld)
        self.assertIn("XgbaCanonicalMapGroup(warp->mapGroup) != MAP_GROUP(MAP_MOSSDEEP_CITY_SPACE_CENTER_1F)", overworld)
        self.assertIn("XgbaCanonicalMapGroup(gSaveBlock1Ptr->location.mapGroup) == MAP_GROUP(MAP_SOOTOPOLIS_CITY)", overworld)
        self.assertIn(
            "XgbaCanonicalMapGroup(gSaveBlock1Ptr->location.mapGroup)"
            " == MAP_GROUP(MAP_SS_TIDAL_CORRIDOR)",
            source("region_map.c"),
        )
        specials = source("field_specials.c")
        self.assertIn("XgbaCanonicalMapGroup(gSaveBlock1Ptr->location.mapGroup) == sPokeMarts[i][0]", specials)
        self.assertIn("XgbaCanonicalMapGroup(gSaveBlock1Ptr->location.mapGroup) == 0", specials)

    def test_no_raw_world_one_checks_in_specials(self):
        specials = source("field_specials.c")
        for expression in (
            "gSaveBlock1Ptr->location.mapGroup",
            "gLastUsedWarp.mapGroup",
            "gSaveBlock1Ptr->dynamicWarp.mapGroup",
        ):
            with self.subTest(expression=expression):
                self.assertNotRegex(
                    specials,
                    re.escape(expression) + r"\s*[!=]=\s*MAP_GROUP\(",
                )

    def test_live_mew_uses_actual_clone_map_not_canonical_map(self):
        avatar = source("field_player_avatar.c")
        self.assertIn(
            "LOCALID_FARAWAY_ISLAND_MEW, gSaveBlock1Ptr->location.mapNum,"
            " gSaveBlock1Ptr->location.mapGroup",
            avatar,
        )


if __name__ == "__main__":
    unittest.main()
