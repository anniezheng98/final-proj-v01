import json
import math
from shapely.geometry import shape
from shapely import affinity

with open("data/footprints.geojson") as f:
    data = json.load(f)

SIZE = 200
PADDING = 10
# Limit so the browser can load and render (increase or remove for full export)
MAX_BUILDINGS = 8000
output = []

for i, feature in enumerate(data["features"]):
    if len(output) >= MAX_BUILDINGS:
        break
    try:
        geom = shape(feature["geometry"])
        props = feature["properties"]

        if geom.geom_type == "Polygon":
            polys = [geom]
        elif geom.geom_type == "MultiPolygon":
            polys = list(geom.geoms)
        else:
            continue

        # Normalize orientation: rotate so min-area bounding box is axis-aligned (flat on page)
        try:
            mrr = geom.minimum_rotated_rectangle
            if mrr and not mrr.is_empty and len(mrr.exterior.coords) >= 3:
                coords = list(mrr.exterior.coords)
                dx = coords[1][0] - coords[0][0]
                dy = coords[1][1] - coords[0][1]
                angle_rad = math.atan2(dy, dx)
                angle_deg = -math.degrees(angle_rad)
                geom = affinity.rotate(geom, angle_deg, origin="center")
                if geom.geom_type == "Polygon":
                    polys = [geom]
                else:
                    polys = list(geom.geoms)
        except Exception:
            pass

        minx, miny, maxx, maxy = geom.bounds
        scale = (SIZE - PADDING * 2) / max(maxx - minx, maxy - miny)

        path_data = ""
        for poly in polys:
            points = [
                (PADDING + (x - minx) * scale, SIZE - PADDING - (y - miny) * scale)
                for x, y in poly.exterior.coords
            ]
            path_data += "M " + " L ".join(f"{px:.2f},{py:.2f}" for px, py in points) + " Z "

        bbl = props.get("base_bbl") or ""
        boro_code = props.get("boro_code") or (str(bbl)[:1] if bbl else "")

        output.append({
            "bin": props.get("bin", i),
            "year": props.get("cnstrct_yr") or 0,
            "height": props.get("heightroof") or 0,
            "area": round(geom.area, 2),
            "boro": boro_code,
            "path": path_data
        })

    except Exception as e:
        print(f"Skipped {i}: {e}")

with open("buildings.json", "w") as f:
    json.dump(output, f)

print(f"Exported {len(output)} buildings to buildings.json")