"""Check the historical SVG against measurements from the 1213×723 source.

The tolerance accounts for rounding scan coordinates to whole pixels. Use
--exact-png to separately require decoded pixel equality in the raster export.
"""
import argparse
from pathlib import Path
from xml.etree import ElementTree as ET

BASE = Path(__file__).resolve().parent
STEM = "klammerdiagramm-uddama-plate-historical"
POLYGONS = {
    "A": ((944, 154), (1076, 154), (1076, 222), (944, 222)),
    "C": ((709, 154), (833, 154), (833, 293), (917, 293), (917, 364), (709, 364)),
    "E": ((371, 154), (531, 154), (531, 434), (667, 434), (667, 505), (371, 505)),
    "G": ((126, 154), (263, 154), (263, 575), (387, 575), (387, 644), (126, 644)),
}
LABELS = {"A": (1012, 222), "B": (918, 293), "C": (810, 364), "D": (667, 434),
          "E": (516, 505), "F": (387, 575), "G": (256, 644)}
ELBOWS = {
    "B": ((935, 293), (1012, 293), (1012, 240)),
    "D": ((683, 434), (810, 434), (810, 381)),
    "F": ((404, 575), (516, 575), (516, 523)),
}
SVG = "{http://www.w3.org/2000/svg}"


def points(element):
    return [tuple(map(float, token.split(","))) for token in element.get("points", "").split()]


def near(actual, expected):
    return len(actual) == len(expected) and all(
        len(got) == len(want) and all(abs(a - b) <= 1 for a, b in zip(got, want))
        for got, want in zip(actual, expected)
    )


def check_svg(path):
    root = ET.parse(path).getroot()
    ids = {el.get("id"): el for el in root.iter() if el.get("id")}
    problems = []

    def require(condition, message):
        if not condition:
            problems.append(message)

    require(root.get("viewBox", "").split() == ["0", "0", "1213", "723"], "native viewBox mismatch")
    require(not list(root.iter(SVG + "image")), "reference or raster embedded in the SVG")
    bands = {ident for ident in ids if ident.startswith("hatch-")}
    require(bands == {"hatch-" + label.lower() for label in POLYGONS}, "expected four hatched bands")
    for label, expected in POLYGONS.items():
        ident = label.lower()
        band = ids.get("hatch-" + ident)
        clip = ids.get("clip-" + ident)
        outline = clip.find(SVG + "polygon") if clip is not None else None
        require(outline is not None and near(points(outline), expected), f"band {label}: wrong outline")
        strokes = band.find(SVG + "path") if band is not None else None
        require(strokes is not None and strokes.get("d", "").count("M") > 5
                and band.get("clip-path") == f"url(#clip-{ident})", f"band {label}: missing clipped hatch")
        mid_x, rung_y = LABELS[label]
        edges = [(float(e.get("x1")), float(e.get("x2"))) for name, e in ids.items()
                 if name.startswith(f"edge-{label}-")
                 and abs(float(e.get("y1")) - rung_y) <= 1 and abs(float(e.get("y2")) - rung_y) <= 1
                 and float(e.get("x2")) > float(e.get("x1"))]
        require(len(edges) == 2 and sum(right < mid_x for _, right in edges) == 1
                and sum(left > mid_x for left, _ in edges) == 1, f"rung {label}: missing label gap")

    expected_arrows = {126, 263, 371, 531, 709, 833, 944, 1076}
    actual_arrows = [points(el) for name, el in ids.items()
                     if name.startswith("arw-") and el.tag == SVG + "polyline"]
    require(len(actual_arrows) == 8 and all(len(p) == 3 for p in actual_arrows)
            and {round(p[1][0]) for p in actual_arrows} == expected_arrows
            and all(abs(p[1][1] - 155) <= 1 and p[0][1] > p[1][1] and p[2][1] > p[1][1]
                    for p in actual_arrows), "expected eight upward arrow tips")

    for label, (x, y) in LABELS.items():
        item = ids.get("label-" + label)
        require(item is not None and item.text == label
                and near([(float(item.get("x")), float(item.get("y")))], [(x, y + 8)]),
                f"label {label}: wrong text or position")
    for label, expected in ELBOWS.items():
        item = ids.get("elbow-" + label)
        require(item is not None and near(points(item), expected), f"elbow {label}: wrong path")
    token_row = ids.get("token-row")
    expected = "uddāma-ajñāna-rūpa-prabalatama-tamaḥ-stoma-soma-svabhāvā-"
    require(token_row is not None and "".join(token_row.itertext()) == expected, "compound text differs")
    for ident, text in (("part-i", "I часть"), ("part-ii", "II часть")):
        item = ids.get(ident)
        require(item is not None and item.text == text, f"{ident}: caption differs")
    for i, (n, first, last) in enumerate(((34, 51, 307), (23, 415, 587),
                                          (20, 711, 862), (26, 971, 1165)), 1):
        rule = ids.get(f"span-{i}")
        dashes = list(rule.findall(SVG + "rect")) if rule is not None else []
        positions = [(float(d.get("x")), float(d.get("width"))) for d in dashes]
        require(len(dashes) == n and abs(positions[0][0] - first) <= 1.5
                and abs(sum(positions[-1]) - last) <= 1.5
                and all(0 < w <= 8 for _, w in positions)
                and all(x + w <= next_x for (x, w), (next_x, _) in zip(positions, positions[1:])),
                f"rule {i}: wrong dash spans")
    for i, (start_y, end_y) in enumerate(((99, 105), (109, 115))):
        leg = ids.get(f"hyphen-drop-{i}")
        require(leg is not None and near(
            [(float(leg.get("x1")), float(leg.get("y1"))),
             (float(leg.get("x2")), float(leg.get("y2")))],
            [(650, start_y), (650, end_y)],
        ), f"cusp drop: wrong dash {i + 1}")
    text_ids = {"token-row", "part-i", "part-ii"} | {f"label-{c}" for c in LABELS}
    for ident in text_ids:
        item = ids.get(ident)
        group = ids.get(f"outlined-{ident}")
        paths = list(group.findall(SVG + "path")) if group is not None else []
        require(item is not None and item.get("opacity") == "0" and len(paths) == 9
                and [p.get("fill") for p in paths] == ["cyan"]*3 + ["magenta"]*3 + ["yellow"]*3
                and all(p.get("d", "").endswith("Z") for p in paths), f"{ident}: missing lettering contours")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", nargs="?", type=Path, default=BASE / (STEM + ".svg"))
    parser.add_argument("--exact-png", action="store_true")
    parser.add_argument("--png", type=Path, default=BASE / (STEM + ".png"))
    parser.add_argument("--source", type=Path, default=BASE / "klammerdiagramm-target-plate.png")
    args = parser.parse_args()
    defects = check_svg(args.svg)
    if args.exact_png:
        from PIL import Image

        with Image.open(args.source) as source, Image.open(args.png) as remake:
            if source.size != remake.size or source.convert("RGBA").tobytes() != remake.convert("RGBA").tobytes():
                defects.append("native PNG does not match the source pixel-for-pixel")
    if defects:
        for defect in defects:
            print("FAIL:", defect)
        return 1
    print("PASS: four bands, eight arrows, four rungs, seven labels, three elbows")
    if args.exact_png:
        print("PASS: native PNG matches all decoded pixels")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
