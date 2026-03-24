"""
Find the most common footprint shape (by vertex count) and output a representative SVG.
Output: assets/most-common-footprint.svg
"""
import json
import re


def vertex_count(path_str):
    """Count vertices across all polygons in path."""
    parts = path_str.strip().rstrip(" Z").split(" Z ")
    total = 0
    for part in parts:
        if not part.strip():
            continue
        coords = re.findall(r"[\d.]+", part)
        total += len(coords) // 2
    return total


def main():
    print("Loading buildings.json...")
    with open("buildings.json") as f:
        data = json.load(f)

    by_count = {}
    for b in data:
        p = b.get("path", "")
        if not p:
            continue
        n = vertex_count(p)
        if n >= 3:
            by_count.setdefault(n, []).append(b)

    most_common_n = max(by_count.keys(), key=lambda k: len(by_count[k]))
    buildings = by_count[most_common_n]
    print(f"Most common: {most_common_n} vertices ({len(buildings):,} buildings)")

    # Pick representative: median area
    sorted_by_area = sorted(buildings, key=lambda b: b.get("area", 0))
    median_idx = len(sorted_by_area) // 2
    rep = sorted_by_area[median_idx]
    path_d = rep["path"].strip().rstrip(" ")

    view_size = 200
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_size} {view_size}" width="{view_size}" height="{view_size}">
  <path d="{path_d}" fill="#000000"/>
</svg>
'''

    out_path = "assets/most-common-footprint.svg"
    with open(out_path, "w") as f:
        f.write(svg_content)
    print(f"Wrote {out_path} (representative: {most_common_n}-vertex, area {rep.get('area')} sq ft)")


if __name__ == "__main__":
    main()
