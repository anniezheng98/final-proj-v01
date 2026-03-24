"""
Compute the average footprint shape from all buildings in buildings.json
by rasterizing each path, averaging, and outputting as SVG.
Output: assets/average-footprint.svg
"""
import json
import re
import numpy as np


def parse_svg_path(path_str):
    """Parse SVG path 'M x,y L x,y ... Z' into list of polygons (each polygon is list of (x,y))."""
    polygons = []
    parts = path_str.strip().rstrip(" Z").split(" Z ")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        coords = re.findall(r"[\d.]+", part)
        if len(coords) < 4:
            continue
        points = []
        for i in range(0, len(coords) - 1, 2):
            x, y = float(coords[i]), float(coords[i + 1])
            points.append((x, y))
        if len(points) >= 3:
            polygons.append(np.array(points))
    return polygons


def points_in_polygon(points, poly):
    """Ray-casting point-in-polygon. points: (N,2), poly: (V,2). Returns (N,) bool."""
    if len(poly) < 3:
        return np.zeros(len(points), dtype=bool)
    px = points[:, 0]
    py = points[:, 1]
    n = len(points)
    inside = np.zeros(n, dtype=bool)
    v = len(poly)
    for i in range(v):
        x1, y1 = poly[i, 0], poly[i, 1]
        x2, y2 = poly[(i + 1) % v, 0], poly[(i + 1) % v, 1]
        if y1 == y2:
            continue
        # Edge crosses horizontal line at py?
        t = (py - y1) / (y2 - y1)
        mask = (t >= 0) & (t <= 1)
        xi = x1 + t * (x2 - x1)
        mask &= (xi > px)
        mask &= ((y1 < py) != (y2 < py))  # py strictly between y1,y2
        inside ^= mask
    return inside


def rasterize_polygon(poly, grid_size):
    """Rasterize one polygon into grid_size x grid_size."""
    if len(poly) < 3:
        return np.zeros((grid_size, grid_size), dtype=np.uint32)
    scale = 200.0 / grid_size
    # Grid cell centers in 0-200 coords
    i = np.arange(grid_size)
    j = np.arange(grid_size)
    y = (i + 0.5) * scale
    x = (j + 0.5) * scale
    X, Y = np.meshgrid(x, y)
    points = np.column_stack([X.ravel(), Y.ravel()])
    inside = points_in_polygon(points, poly)
    return inside.reshape(grid_size, grid_size).astype(np.uint32)


def rasterize_path(path_str, grid_size):
    """Rasterize full path (may have multiple polygons) into one grid."""
    polygons = parse_svg_path(path_str)
    if not polygons:
        return np.zeros((grid_size, grid_size), dtype=np.uint32)
    acc = np.zeros((grid_size, grid_size), dtype=np.uint32)
    for poly in polygons:
        acc += rasterize_polygon(poly, grid_size)
    return np.minimum(acc, 1)


def grid_to_svg_path(avg, grid_size, view_size, threshold=0.5):
    """Convert thresholded grid to SVG path as union of rects (blocky but valid)."""
    cell_w = view_size / grid_size
    cell_h = view_size / grid_size
    paths = []
    for r in range(grid_size):
        for c in range(grid_size):
            if avg[r, c] >= threshold:
                x = c * cell_w
                y = r * cell_h
                d = f"M {x:.2f},{y:.2f} h {cell_w:.2f} v {cell_h:.2f} h {-cell_w:.2f} Z"
                paths.append(d)
    return " ".join(paths)


def main():
    grid_size = 100
    view_size = 200

    print("Loading buildings.json...")
    with open("buildings.json") as f:
        buildings = json.load(f)
    n = len(buildings)
    print(f"Processing {n:,} buildings...")

    accumulator = np.zeros((grid_size, grid_size), dtype=np.uint64)

    for i, b in enumerate(buildings):
        if (i + 1) % 100000 == 0:
            print(f"  {i + 1:,} / {n:,}")
        path_str = b.get("path", "")
        if not path_str:
            continue
        raster = rasterize_path(path_str, grid_size)
        accumulator += raster

    print("Averaging...")
    avg = accumulator.astype(np.float64) / n

    print("Building SVG path (threshold 0.5)...")
    path_d = grid_to_svg_path(avg, grid_size, view_size, 0.5)

    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_size} {view_size}" width="{view_size}" height="{view_size}">
  <path d="{path_d}" fill="#000000"/>
</svg>
'''

    out_path = "assets/average-footprint.svg"
    with open(out_path, "w") as f:
        f.write(svg_content)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
