#!/usr/bin/env python3
"""Check every E3 world marker against the real Littleroot tile layout."""

from pathlib import Path

from xgba_pack_e3 import marker_cells, world_marker


def main():
    source = Path("data/layouts/LittlerootTown/map.bin").read_bytes()
    slots = marker_cells(source)
    if len(slots) != 5:
        raise ValueError("Expected exactly five marker positions")

    for world in range(3, 21):
        marked = world_marker(source, world)
        if len(marked) != len(source):
            raise ValueError(f"World {world} changed the layout size")

        differences = 0
        for position in range(0, len(source), 2):
            original_tile = source[position:position + 2]
            marked_tile = marked[position:position + 2]
            if original_tile != marked_tile:
                differences += 1
                before = int.from_bytes(original_tile, "little") & 0xFC00
                after = int.from_bytes(marked_tile, "little") & 0xFC00
                if before != after:
                    raise ValueError(f"World {world} changed a tile's attributes")
                if position not in [slot_position for slot_position, _ in slots]:
                    raise ValueError(f"World {world} modified an unexpected tile")

        expected = (world - 2).bit_count()
        if differences != expected:
            raise ValueError(
                f"World {world}: {differences} marker bits changed; expected {expected}"
            )

    print("E3 marker preflight PASS: all 18 world IDs, five safe tile slots")


if __name__ == "__main__":
    main()
