"""Trace the historical scan's letter contours as SVG paths, not a raster layer."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import label as components


def trace_glyph(ink, ox=0, oy=0, threshold=0.5):
    a = np.asarray(ink, dtype=float)
    if a.ndim != 2:
        raise ValueError("ink must be 2-D")
    h, w = a.shape
    # Pad with zeros so contours close around the glyph.
    g = np.zeros((h + 2, w + 2), dtype=float)
    g[1:-1, 1:-1] = a

    # Edge crossing points, linearly interpolated between corner samples.
    # Vertical edges (between left/right samples) at x = i, y = j + t
    # Horizontal edges (between up/down samples) at y = j, x = i + t
    ny, nx = g.shape
    segs = {}  # pair of edge keys -> pair of crossing points

    def lerp(pa, va, pb, vb):
        f = (threshold - va) / (vb - va) if vb != va else 0.5
        f = min(1.0, max(0.0, f))
        return (pa[0] + (pb[0] - pa[0]) * f, pa[1] + (pb[1] - pa[1]) * f)

    def add_segment(k0, k1, p0, p1):
        segs[(k0, k1)] = (p0, p1)

    for j in range(ny - 1):
        for i in range(nx - 1):
            v00 = g[j, i]       # top-left
            v01 = g[j, i + 1]   # top-right
            v11 = g[j + 1, i + 1]  # bottom-right
            v10 = g[j + 1, i]  # bottom-left
            idx = ((v00 > threshold) << 3) | ((v01 > threshold) << 2) | \
                  ((v11 > threshold) << 1) | ((v10 > threshold) << 0)
            if idx == 0 or idx == 15:
                continue

            # Crossing points on the four cell edges, keyed by exact topology.
            top_key = ('h', i, j)      # between (j,i)-(j,i+1)
            bot_key = ('h', i, j + 1)   # between (j+1,i)-(j+1,i+1)
            left_key = ('v', i, j)      # between (j,i)-(j+1,i)
            right_key = ('v', i + 1, j)  # between (j,i+1)-(j+1,i+1)

            top = lerp((i, j), v00, (i + 1, j), v01)
            bot = lerp((i, j + 1), v10, (i + 1, j + 1), v11)
            left = lerp((i, j), v00, (i, j + 1), v10)
            right = lerp((i + 1, j), v01, (i + 1, j + 1), v11)

            # Saddle resolution via center average.
            center = 0.25 * (v00 + v01 + v10 + v11)
            sad_hi = center > threshold  # high center connects differently

            def emit(b, e, pb, pe):
                add_segment(b, e, pb, pe)

            if idx == 1:      # bottom-left
                emit(left_key, bot_key, left, bot)
            elif idx == 2:    # bottom-right
                emit(bot_key, right_key, bot, right)
            elif idx == 3:    # bottom row
                emit(left_key, right_key, left, right)
            elif idx == 4:    # top-right
                emit(top_key, right_key, top, right)
            elif idx == 5:    # top-right + bottom-left (saddle)
                if sad_hi:
                    emit(left_key, top_key, left, top)
                    emit(right_key, bot_key, right, bot)
                else:
                    emit(left_key, bot_key, left, bot)
                    emit(right_key, top_key, right, top)
            elif idx == 6:    # right column
                emit(top_key, bot_key, top, bot)
            elif idx == 7:    # all but top-left
                emit(left_key, top_key, left, top)
            elif idx == 8:    # top-left
                emit(top_key, left_key, top, left)
            elif idx == 9:    # left column
                emit(top_key, bot_key, top, bot)
            elif idx == 10:   # top-left + bottom-right (saddle)
                if sad_hi:
                    emit(top_key, right_key, top, right)
                    emit(bot_key, left_key, bot, left)
                else:
                    emit(top_key, left_key, top, left)
                    emit(bot_key, right_key, bot, right)
            elif idx == 11:   # all but top-right
                emit(top_key, right_key, top, right)
            elif idx == 12:   # top row
                emit(right_key, left_key, right, left)
            elif idx == 13:   # all but bottom-right
                emit(bot_key, right_key, bot, right)
            else:             # 14: all but bottom-left
                emit(left_key, bot_key, left, bot)

    # Edges form degree-two undirected cycles. Winding is immaterial for evenodd.
    adjacency = {}
    coordinates = {}
    for (k0, k1), (p0, p1) in segs.items():
        adjacency.setdefault(k0, []).append(k1)
        adjacency.setdefault(k1, []).append(k0)
        coordinates[k0], coordinates[k1] = p0, p1
    if any(len(neighbors) != 2 for neighbors in adjacency.values()):
        raise ValueError("contour is not closed")
    loops = []
    visited = set()
    for start in adjacency:
        if start in visited:
            continue
        path = []
        previous, current = None, start
        while current not in visited:
            visited.add(current)
            path.append(coordinates[current])
            left, right = adjacency[current]
            previous, current = current, left if left != previous else right
        if current != start:
            raise ValueError("contour joined a different cycle")
        if len(path) >= 3:
            loops.append(path)

    def rdp(points, eps):
        if len(points) < 3:
            return points
        keep = [False] * len(points)
        keep[0] = keep[-1] = True
        stack = [(0, len(points) - 1)]
        while stack:
            s, e = stack.pop()
            if e <= s + 1:
                continue
            ax, ay = points[s]
            bx, by = points[e]
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            best, bi = -1.0, -1
            for m in range(s + 1, e):
                px, py = points[m]
                if L2 == 0.0:
                    d2 = (px - ax) ** 2 + (py - ay) ** 2
                else:
                    t = ((px - ax) * dx + (py - ay) * dy) / L2
                    t = min(1.0, max(0.0, t))
                    qx, qy = ax + t * dx, ay + t * dy
                    d2 = (px - qx) ** 2 + (py - qy) ** 2
                if d2 > best:
                    best, bi = d2, m
            if best > eps * eps:
                keep[bi] = True
                stack.append((s, bi))
                stack.append((bi, e))
        return [p for p, k in zip(points, keep) if k]

    def fmt(v):
        s = ("%.2f" % (v + 1e-9)).rstrip("0").rstrip(".")
        return "0" if s in ("", "-0") else s

    subpaths = []
    for pts in loops:
        # pixel centers are at (x+.5, y+.5); grid includes a one-pixel pad
        poly = [(x - 0.5 + ox, y - 0.5 + oy) for (x, y) in pts]
        poly = rdp(poly, 0.12)
        if len(poly) < 3:
            continue
        d = "M" + fmt(poly[0][0]) + " " + fmt(poly[0][1])
        for (x, y) in poly[1:]:
            d += "L" + fmt(x) + " " + fmt(y)
        d += "Z"
        subpaths.append(d)

    return "".join(subpaths)

# Crop bounds in native scan coordinates; the connected components below keep
# subpixel-colored text but exclude adjacent monochrome rules.
REGIONS = {
    "token-row": (45, 98, 1175, 143),
    "part-i": (320, 38, 402, 68),
    "part-ii": (875, 38, 960, 68),
    **{f"label-{name}": (x - 14, y - 13, x + 14, y + 13)
       for name, x, y in (("A", 1012, 222), ("B", 918, 293), ("C", 810, 364),
                         ("D", 667, 434), ("E", 516, 505), ("F", 387, 575), ("G", 256, 644))},
}
# Fit against native Chromium samples of individual contour coverage.
THRESHOLDS = (0.36, 0.48, 0.72)
OPACITIES = (0.354305, 0.538804, 1.0)


def generate(source_path):
    with Image.open(source_path) as image:
        if image.size != (1213, 723):
            raise ValueError("lettering trace requires the native 1213 x 723 reference")
        source = np.asarray(image.convert("RGB"))
    channels = {}
    for name, (left, top, right, bottom) in REGIONS.items():
        crop = source[top:bottom, left:right]
        ink = 1 - crop.astype(float) / 255
        if name == "token-row":
            # Do not trace the monochrome drop above the split hyphen.
            ink[:18, 646-left:654-left] = 0
        else:
            occupied = np.any(ink > .01, axis=2)
            cc, _ = components(occupied, structure=np.ones((3, 3), dtype=int))
            seeded = np.unique(cc[(np.ptp(crop, axis=2) > 4) & occupied])
            ink[~np.isin(cc, seeded[seeded != 0])] = 0
        paths = [[trace_glyph(plane, left, top, iso) for iso in THRESHOLDS]
                 for plane in ink.transpose(2, 0, 1)]
        if not all(d for plane in paths for d in plane):
            raise ValueError(f"missing contours in {name}")
        channels[name] = paths
    return {
        "format": 2,
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "coverage_thresholds": THRESHOLDS,
        "opacities": OPACITIES,
        "channels": channels,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    args.output.write_text(json.dumps(generate(args.source), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
