#!/usr/bin/env python3
"""Prepare a second, internally connected Hoenn map network for XGBA E2.

Generated maps are intentionally untracked. Run before 'make all', or use 'make e2'.
The original 34 map groups and all their map constants remain unchanged.
"""

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP_ROOT = ROOT / "data/maps"
GROUPS_FILE = MAP_ROOT / "map_groups.json"
LAYOUTS_FILE = ROOT / "data/layouts/layouts.json"
GROUP_PREFIX = "gMapGroup_Xgba2_"
MAP_PREFIX = "Xgba2_"
LAYOUT_PREFIX = "LAYOUT_XGBA2_"
SPECIAL_DESTINATIONS = {"MAP_UNDEFINED", "MAP_DYNAMIC"}


def load_json(path):
    return json.loads(path.read_text())


def write_if_changed(path, value):
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if not path.exists() or path.read_text() != text:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def clone_map_id(old):
    if not old.startswith("MAP_"):
        raise ValueError(f"Unexpected Emerald map ID {old}")
    return "MAP_XGBA2_" + old[4:]


def main():
    groups = load_json(GROUPS_FILE)
    layouts = load_json(LAYOUTS_FILE)

    original_groups = [g for g in groups["group_order"] if not g.startswith(GROUP_PREFIX)]
    if len(original_groups) != 34:
        raise ValueError(f"Expected 34 original groups, found {len(original_groups)}")

    originals = []
    for group in original_groups:
        for name in groups[group]:
            if name == "XgbaTestTown":
                continue
            source = MAP_ROOT / name / "map.json"
            original = load_json(source)
            if original["name"] != name:
                raise ValueError(f"Map name/path mismatch: {source}")
            originals.append((group, name, original))

    original_ids = {entry["id"] for _, _, entry in originals}
    if len(original_ids) != len(originals):
        raise ValueError("Duplicate original map IDs")
    translated_ids = {map_id: clone_map_id(map_id) for map_id in original_ids}

    base_layouts = [
        layout for layout in layouts["layouts"]
        if not layout["id"].startswith(LAYOUT_PREFIX)
    ]
    layout_ids = {
        layout["id"] for layout in base_layouts
        if layout["id"] != "LAYOUT_XGBA_TEST_TOWN"
    }
    if len(base_layouts) != 442:
        raise ValueError(f"Expected 442 E1 source layouts, got {len(base_layouts)}")
    if len(layout_ids) != 441:
        raise ValueError(f"Expected 441 original Hoenn layouts, got {len(layout_ids)}")

    cloned_layouts = []
    for entry in base_layouts:
        if entry["id"] == "LAYOUT_XGBA_TEST_TOWN":
            continue
        clone = copy.deepcopy(entry)
        clone["id"] = LAYOUT_PREFIX + entry["id"][len("LAYOUT_"):]
        clone["name"] = MAP_PREFIX + entry["name"]
        cloned_layouts.append(clone)
    layouts["layouts"] = base_layouts + cloned_layouts

    cloned_groups = [GROUP_PREFIX + group[len("gMapGroup_"):] for group in original_groups]
    if len(groups["group_order"]) not in (34, 68):
        raise ValueError("Unexpected existing map group count")
    groups["group_order"] = original_groups + cloned_groups

    unresolved = set()
    total_warps = 0
    total_connections = 0
    for group, name, original in originals:
        if original["layout"] not in layout_ids:
            raise ValueError(f"{name} references missing layout {original['layout']}")

        clone_name = MAP_PREFIX + name
        clone = copy.deepcopy(original)
        clone["name"] = clone_name
        clone["id"] = translated_ids[original["id"]]
        clone["layout"] = LAYOUT_PREFIX + original["layout"][len("LAYOUT_"):]

        # The cloned map network keeps a single canonical set of scripts.
        # Reuse original scripts but resolve map/event ownership to the clone.
        # Neutralizing every callback leaves gyms and story triggers inert.
        shared = original.get("shared_events_map")
        if shared is not None:
            if shared not in {entry[1] for entry in originals}:
                raise ValueError(f"{name}: unknown shared events map {shared}")
            clone["shared_events_map"] = MAP_PREFIX + shared
        else:
            clone.pop("shared_events_map", None)
        clone["shared_scripts_map"] = original.get("shared_scripts_map", name)

        for key in ("object_events", "coord_events", "bg_events"):
            if key in original:
                clone[key] = copy.deepcopy(original[key])
            else:
                clone.pop(key, None)

        # Keep the sibling in place while the cloned rival-house callback
        # determines its story visibility. Other original NPCs remain intact.

        # The rival sibling at May's east wall can wander across the boundary
        # before indoor map transitions have settled. Keep the sibling still.
        if name == "LittlerootTown_MaysHouse_1F":
            for obj in clone["object_events"]:
                if obj["script"] == "RivalsHouse_1F_EventScript_RivalSibling":
                    obj["movement_type"] = "MOVEMENT_TYPE_FACE_DOWN"
                    obj["movement_range_x"] = 0
                    obj["movement_range_y"] = 0

        for warp in clone.get("warp_events", []):
            dest = warp["dest_map"]
            if dest in translated_ids:
                warp["dest_map"] = translated_ids[dest]
            elif dest not in SPECIAL_DESTINATIONS:
                unresolved.add((name, dest))
            total_warps += 1

        for connection in clone.get("connections") or []:
            dest = connection["map"]
            if dest in translated_ids:
                connection["map"] = translated_ids[dest]
            else:
                unresolved.add((name, dest))
            total_connections += 1

        if name == "LittlerootTown":
            # Retain vanilla introduction/story actors and add the laboratory
            # portal + diagnostics without clearing original objects or triggers.
            clone.setdefault("object_events", []).append({
                "graphics_id": "OBJ_EVENT_GFX_SCIENTIST_1",
                "x": 14, "y": 12, "elevation": 3,
                "movement_type": "MOVEMENT_TYPE_FACE_DOWN",
                "movement_range_x": 0, "movement_range_y": 0,
                "trainer_type": "TRAINER_TYPE_NONE",
                "trainer_sight_or_berry_tree_id": "0",
                "script": "Xgba2Littleroot_EventScript_Return",
                "flag": "0",
            })
            clone["object_events"].append({
                "graphics_id": "OBJ_EVENT_GFX_SCIENTIST_2",
                "x": 16, "y": 12, "elevation": 3,
                "movement_type": "MOVEMENT_TYPE_FACE_DOWN",
                "movement_range_x": 0, "movement_range_y": 0,
                "trainer_type": "TRAINER_TYPE_NONE",
                "trainer_sight_or_berry_tree_id": "0",
                "script": "XgbaE4_EventScript_AdvanceProgress",
                "flag": "0",
            })
            clone["object_events"].append({
                "graphics_id": "OBJ_EVENT_GFX_BOY_1",
                "x": 18, "y": 12, "elevation": 3,
                "movement_type": "MOVEMENT_TYPE_FACE_DOWN",
                "movement_range_x": 0, "movement_range_y": 0,
                "trainer_type": "TRAINER_TYPE_NONE",
                "trainer_sight_or_berry_tree_id": "0",
                "script": "XgbaE4_EventScript_ReadProgress",
                "flag": "0",
            })

            for x, graphic, script in [
                (14, "OBJ_EVENT_GFX_SCIENTIST_1", "XgbaE5_EventScript_Snapshot"),
                (16, "OBJ_EVENT_GFX_BOY_1", "XgbaE5_EventScript_Audit"),
            ]:
                clone["object_events"].append({
                    "graphics_id": graphic,
                    "x": x, "y": 15, "elevation": 3,
                    "movement_type": "MOVEMENT_TYPE_FACE_DOWN",
                    "movement_range_x": 0, "movement_range_y": 0,
                    "trainer_type": "TRAINER_TYPE_NONE",
                    "trainer_sight_or_berry_tree_id": "0",
                    "script": script,
                    "flag": "0",
                })

        write_if_changed(MAP_ROOT / clone_name / "map.json", clone)

    if unresolved:
        problems = ", ".join(f"{name}->{dest}" for name, dest in sorted(unresolved)[:25])
        raise ValueError("Unmapped map-to-map links: " + problems)

    for source, name in zip(original_groups, cloned_groups):
        groups[name] = [
            MAP_PREFIX + entry for entry in groups[source] if entry != "XgbaTestTown"
        ]

    if sum(len(groups[g]) for g in cloned_groups) != len(originals):
        raise ValueError("Generated map group and file counts differ")
    if any(len(groups[group]) > 256 for group in groups["group_order"]):
        raise ValueError("A map group exceeds the 8-bit map-number limit")
    if len(groups["group_order"]) > 256:
        raise ValueError("Map group count exceeds GBA's 8-bit group limit")
    if len(layouts["layouts"]) >= 65536:
        raise ValueError("Layout IDs exceed 16-bit storage")

    write_if_changed(GROUPS_FILE, groups)
    write_if_changed(LAYOUTS_FILE, layouts)

    manifest = {
        "original_group_count": len(original_groups),
        "clone_group_count": len(cloned_groups),
        "cloned_map_count": len(originals),
        "cloned_layout_count": len(cloned_layouts),
        "remapped_warp_count": total_warps,
        "remapped_connection_count": total_connections,
        "unresolved_links": len(unresolved),
        "entry_map": translated_ids["MAP_LITTLEROOT_TOWN"],
        "expected_total_groups": len(groups["group_order"]),
        "expected_total_layouts": len(layouts["layouts"]),
    }
    write_if_changed(ROOT / "build/xgba-e2-manifest.json", manifest)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
