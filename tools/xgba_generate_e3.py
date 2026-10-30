#!/usr/bin/env python3
"""Generate fixed-stride layout metadata for 18 additional Hoenn world instances."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYOUTS_FILE = ROOT / "data/layouts/layouts.json"
HEADER = ROOT / "include/xgba_world_e3_data.h"
MANIFEST = ROOT / "build/xgba-e3-manifest.json"
WORLD_FIRST = 3
WORLD_LAST = 20
FIRST_OFFSET = 0x02400000
STRIDE = 0x00100000
OUTPUT_SIZE = 64 * 1024 * 1024


def align4(x):
    return (x + 3) & ~3


def layout_plan():
    layouts = json.loads(LAYOUTS_FILE.read_text())["layouts"]
    clones = [entry for entry in layouts if entry["id"].startswith("LAYOUT_XGBA2_")]
    if len(clones) != 441:
        raise ValueError(f"E3 requires 441 World Two source layouts, got {len(clones)}")
    if clones[0]["id"] != "LAYOUT_XGBA2_PETALBURG_CITY":
        raise ValueError("E3 first clone layout changed, review map index assumptions")

    offsets = []
    offset = 0
    for layout in clones:
        fields = []
        for key in ("border_filepath", "blockdata_filepath"):
            source = ROOT / layout[key]
            data = source.read_bytes()
            if len(data) == 0 or len(data) % 2:
                raise ValueError(f"Invalid tile data: {source}")
            offset = align4(offset)
            fields.append((offset, data))
            offset += len(data)
        offsets.append(fields)
    if offset > STRIDE:
        raise ValueError(f"World geometry uses {offset} bytes, exceeds {STRIDE} stride")
    end = FIRST_OFFSET + (WORLD_LAST - WORLD_FIRST) * STRIDE + offset
    if end > OUTPUT_SIZE:
        raise ValueError(f"World 20 exceeds 64 MiB ROM: 0x{end:08X}")
    return clones, offsets, offset, end


def main():
    clones, offsets, used, end = layout_plan()
    lines = [
        "#ifndef GUARD_XGBA_WORLD_E3_DATA_H",
        "#define GUARD_XGBA_WORLD_E3_DATA_H",
        "",
        "#define XGBA_E3_FIRST_LAYOUT_ID LAYOUT_XGBA2_PETALBURG_CITY",
        "#define XGBA_E3_LAYOUT_COUNT 441",
        "#define XGBA_E3_FIRST_WORLD 3",
        "#define XGBA_E3_LAST_WORLD 20",
        "#define XGBA_E3_START_OFFSET 0x02400000u",
        "#define XGBA_E3_WORLD_STRIDE 0x00100000u",
        "",
        "static const u32 sXgbaE3BorderOffsets[441] =",
        "{",
    ]
    for fields in offsets:
        lines.append(f"    0x{fields[0][0]:08X}u,")
    lines += ["};", "", "static const u32 sXgbaE3MapOffsets[441] =", "{"]
    for fields in offsets:
        lines.append(f"    0x{fields[1][0]:08X}u,")
    lines += ["};", "", "#endif", ""]
    text = "\n".join(lines)
    if not HEADER.exists() or HEADER.read_text() != text:
        HEADER.write_text(text)

    manifest = {
        "worlds_total_including_original": 20,
        "world_2_uses_e2_network": True,
        "additional_physical_worlds": 18,
        "layout_count_per_world": len(clones),
        "assets_per_world": len(clones) * 2,
        "per_world_bytes": used,
        "first_world_3_file_offset": FIRST_OFFSET,
        "last_data_end_file_offset": end,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
