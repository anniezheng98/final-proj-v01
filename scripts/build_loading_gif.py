#!/usr/bin/env python3
"""
Build assets/loading-footprints.gif: 10 unique footprints, 500ms per frame, loop forever.

Uses matplotlib + svgpathtools (pure Python wheels; no system Cairo).

  python3 -m pip install pillow matplotlib svgpathtools
  python3 scripts/build_loading_gif.py
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
OUT_GIF = os.path.join(ASSETS, "loading-footprints.gif")
SIZE = 240
VIEW = 200.0
BG = "#d3d3d3"

# Order: 5 borough irregular + most common + average + 3 distinct paths from buildings.json
STATIC_SVGS = [
    "most-irregular-manhattan.svg",
    "most-irregular-brooklyn.svg",
    "most-irregular-queens.svg",
    "most-irregular-bronx.svg",
    "most-irregular-staten-island.svg",
    "most-common-footprint.svg",
    "average-footprint.svg",
]


def pick_three_paths_from_buildings(data: list) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    step = max(1, len(data) // 12)
    for i in range(0, len(data), step):
        if len(out) >= 3:
            break
        p = data[i].get("path")
        if isinstance(p, str) and p.strip() and p not in seen:
            seen.add(p)
            out.append(p)
    i = 0
    while len(out) < 3 and i < len(data):
        p = data[i].get("path")
        if isinstance(p, str) and p.strip() and p not in seen:
            seen.add(p)
            out.append(p)
        i += 1
    return out[:3]


def rasterize_svgpathtools_path(path_obj, size: int = SIZE) -> Image.Image:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dpi = 100
    fig_in = size / dpi
    fig, ax = plt.subplots(figsize=(fig_in, fig_in), dpi=dpi)

    for sub in path_obj.continuous_subpaths():
        pts: list[complex] = []
        for seg in sub:
            try:
                ln = float(seg.length())
            except (TypeError, ValueError):
                ln = 0.0
            seg_n = max(2, int(ln * 2) + 2)
            for k in range(seg_n):
                t = k / (seg_n - 1) if seg_n > 1 else 0.0
                pts.append(seg.point(t))
        if len(pts) < 3:
            continue
        x = [p.real for p in pts]
        y = [VIEW - p.imag for p in pts]
        ax.fill(x, y, color="#000000", linewidth=0)

    ax.set_xlim(0, VIEW)
    ax.set_ylim(0, VIEW)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor(BG)
    fig.patch.set_facecolor(BG)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=BG, edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    im = Image.open(buf).convert("RGBA")
    if im.size != (size, size):
        im = im.resize((size, size), Image.Resampling.LANCZOS)
    return im


def rasterize_svg_file(svg_path: str) -> Image.Image:
    from svgpathtools import svg2paths

    paths, _attrs = svg2paths(svg_path)
    if not paths:
        raise ValueError(f"No paths in {svg_path}")
    # Merge into one logical path object for subpath iteration
    combined = paths[0]
    for p in paths[1:]:
        combined = combined + p
    return rasterize_svgpathtools_path(combined)


def rasterize_path_d(path_d: str) -> Image.Image:
    from svgpathtools import parse_path

    return rasterize_svgpathtools_path(parse_path(path_d))


def main() -> int:
    try:
        import matplotlib  # noqa: F401
        from svgpathtools import svg2paths  # noqa: F401
    except ImportError:
        print("Install: python3 -m pip install pillow matplotlib svgpathtools", file=sys.stderr)
        return 1

    frames: list[Image.Image] = []

    for name in STATIC_SVGS:
        fp = os.path.join(ASSETS, name)
        if not os.path.isfile(fp):
            print(f"Missing: {fp}", file=sys.stderr)
            return 1
        print(f"Rasterizing {name} …")
        frames.append(rasterize_svg_file(fp))

    buildings_path = os.path.join(ROOT, "buildings.json")
    if not os.path.isfile(buildings_path):
        print(f"Missing {buildings_path}", file=sys.stderr)
        return 1
    with open(buildings_path, encoding="utf-8") as f:
        buildings = json.load(f)

    extras = pick_three_paths_from_buildings(buildings)
    if len(extras) < 3:
        print("Need 3 distinct paths in buildings.json", file=sys.stderr)
        return 1

    for i, path_d in enumerate(extras):
        print(f"Rasterizing buildings sample {i + 1} …")
        frames.append(rasterize_path_d(path_d))

    if len(frames) != 10:
        print(f"Expected 10 frames, got {len(frames)}", file=sys.stderr)
        return 1

    os.makedirs(ASSETS, exist_ok=True)
    flat: list[Image.Image] = []
    for im in frames:
        bg = Image.new("RGBA", im.size, (211, 211, 211, 255))
        bg.paste(im, (0, 0), im)
        flat.append(bg.convert("P", palette=Image.ADAPTIVE, colors=256))

    flat[0].save(
        OUT_GIF,
        save_all=True,
        append_images=flat[1:],
        duration=500,
        loop=0,
        optimize=False,
    )
    print(f"Wrote {OUT_GIF} (10 frames × 500ms, loop)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
