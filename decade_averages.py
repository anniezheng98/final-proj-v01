"""
Compute average footprint area (sq ft) per decade from buildings.json.
Output: data/decade-averages.json
"""
import json
from collections import defaultdict

def main():
    print("Loading buildings.json...")
    with open("buildings.json") as f:
        buildings = json.load(f)

    # Group by decade: floor(year/10)*10
    by_decade = defaultdict(lambda: {"sum": 0, "count": 0})
    for b in buildings:
        year = b.get("year") or 0
        area = b.get("area") or 0
        if year <= 0 or area <= 0:
            continue
        decade = (year // 10) * 10
        by_decade[decade]["sum"] += area
        by_decade[decade]["count"] += 1

    # Build output: [{decade, avgArea, count}, ...] sorted by decade
    output = []
    for decade in sorted(by_decade.keys()):
        d = by_decade[decade]
        avg = d["sum"] / d["count"] if d["count"] > 0 else 0
        output.append({"decade": decade, "avgArea": round(avg, 2), "count": d["count"]})

    out_path = "data/decade-averages.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Wrote {len(output)} decades to {out_path}")

if __name__ == "__main__":
    main()
