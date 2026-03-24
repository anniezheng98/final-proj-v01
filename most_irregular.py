"""
Find the most irregular building shape per borough using compactness ratio: perimeter² / area.
Higher ratio = more irregular. Uses path coordinates (dimensionless).
Output: data/most-irregular-by-borough.json
"""
import json
import re
import math


def parse_svg_path(path_str):
    """Parse SVG path 'M x,y L x,y ... Z' into list of polygons (each is list of (x,y) tuples)."""
    polygons = []
    parts = path_str.strip().rstrip(" Z").split(" Z ")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        coords = re.findall(r"[\d.]+", part)
        if len(coords) < 6:  # need at least 3 points
            continue
        points = []
        for i in range(0, len(coords) - 1, 2):
            x, y = float(coords[i]), float(coords[i + 1])
            points.append((x, y))
        if len(points) >= 3:
            polygons.append(points)
    return polygons


def polygon_area(points):
    """Shoelace formula for polygon area."""
    if len(points) < 3:
        return 0
    n = len(points)
    area = 0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area) / 2


def polygon_perimeter(points):
    """Perimeter of polygon (closed)."""
    if len(points) < 2:
        return 0
    n = len(points)
    p = 0
    for i in range(n):
        j = (i + 1) % n
        dx = points[j][0] - points[i][0]
        dy = points[j][1] - points[i][1]
        p += math.sqrt(dx * dx + dy * dy)
    return p


def compactness(path_str):
    """Compactness ratio = perimeter² / area. Higher = more irregular. Returns inf if area=0."""
    polys = parse_svg_path(path_str)
    if not polys:
        return None
    total_area = sum(polygon_area(p) for p in polys)
    total_perim = sum(polygon_perimeter(p) for p in polys)
    if total_area <= 0:
        return None
    return (total_perim * total_perim) / total_area


def main():
    print("Loading buildings.json...")
    with open("buildings.json") as f:
        data = json.load(f)

    BOROUGHS = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"}
    best = {}  # boro -> building with highest compactness

    for b in data:
        boro = str(b.get("boro") or "").strip()
        if boro not in BOROUGHS:
            continue
        path = b.get("path", "")
        if not path:
            continue
        c = compactness(path)
        if c is None or not math.isfinite(c):
            continue
        if boro not in best or c > best[boro]["compactness"]:
            best[boro] = {
                "bin": b.get("bin"),
                "boro": boro,
                "borough_name": BOROUGHS[boro],
                "compactness": round(c, 4),
                "area": b.get("area"),
                "year": b.get("year"),
                "path": path.strip().rstrip(),
            }

    output = [best[b] for b in ["1", "2", "3", "4", "5"] if b in best]
    out_path = "data/most-irregular-by-borough.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Wrote {len(output)} boroughs to {out_path}")

    # Write SVGs for each in assets/
    import os
    os.makedirs("assets", exist_ok=True)
    view_size = 200
    for b in output:
        slug = b["borough_name"].lower().replace(" ", "-")
        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_size} {view_size}" width="{view_size}" height="{view_size}">
  <path d="{b["path"]}" fill="#000000"/>
</svg>
'''
        svg_path = f"assets/most-irregular-{slug}.svg"
        with open(svg_path, "w") as f:
            f.write(svg)
        print(f"  {b['borough_name']}: compactness={b['compactness']:.2f} -> {svg_path}")


if __name__ == "__main__":
    main()
