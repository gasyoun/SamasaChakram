"""Independent browser replay and native pixel comparison for H8424."""
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
from scipy.ndimage import distance_transform_edt

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("source", type=Path)
parser.add_argument("candidate", type=Path, help="SVG, SVG-embedded HTML, or PNG")
parser.add_argument("output", type=Path, help="Scratch output folder")
parser.add_argument("--browser", help="Chromium executable; defaults to Playwright's Chromium")
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
original = Image.open(args.source).convert("RGB")
if args.candidate.suffix.lower() in {".svg", ".html"}:
    rendered = args.output / "browser.png"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=args.browser, args=["--disable-background-networking"]
        )
        page = browser.new_page(viewport={"width": 1600, "height": 1100}, color_scheme="light")
        page.route("**/*", lambda route: (
            route.continue_() if route.request.url.startswith(("file:", "data:")) else route.abort()
        ))
        page.goto(args.candidate.resolve().as_uri())
        page.evaluate("document.fonts.ready.then(() => true)")
        svg = page.locator("svg")
        print("SVG viewBox:", svg.get_attribute("viewBox"))
        print("SVG browser rectangle:", svg.bounding_box())
        # Pin SVG CSS layout to its native coordinate size, without resampling.
        # Report the natural HTML layout above as a separate observable.
        svg.evaluate("""svg => {
            const {width, height} = svg.viewBox.baseVal;
            if (svg.parentElement) svg.parentElement.style.cssText = "margin:0;padding:0;max-width:none";
            Object.assign(svg.style, {width: width + "px", height: height + "px"});
        }""")
        svg.screenshot(path=rendered, animations="disabled")
        browser.close()
else:
    rendered = args.candidate
candidate = Image.open(rendered).convert("RGB")
print("Native dimensions:", original.size, candidate.size)
same_dimensions = original.size == candidate.size
candidate_at_origin = Image.new("RGB", original.size, "white")
candidate_at_origin.paste(candidate, (0, 0))
a, b = (np.array(im, dtype=np.int32) for im in (original, candidate_at_origin))
delta = np.abs(a - b)
print("Exact decoded pixel match:", same_dimensions and not bool(delta.any()))
worse = delta.max(axis=2)
print("Changed pixels:", int(np.count_nonzero(worse)))
print("Pixels with channel error >16 / >64:",
      int(np.count_nonzero(worse > 16)), "/", int(np.count_nonzero(worse > 64)))
print("Mean absolute channel error:", round(float(delta.mean()), 4))
print("RMS channel error:", round(float(np.sqrt(np.mean(delta * delta))), 4))
source_ink = a.min(axis=2) < 170
candidate_ink = b.min(axis=2) < 170
near_source = distance_transform_edt(~source_ink)
near_candidate = distance_transform_edt(~candidate_ink)
for label, rows in (("caption", slice(24, 96)), ("text", slice(96, 149)), ("geometry", slice(149, 664))):
    s, c = source_ink[rows], candidate_ink[rows]
    sd, cd = near_source[rows], near_candidate[rows]
    print(label, "dark pixels (original/remake):", int(s.sum()), int(c.sum()))
    for tolerance in (0, 1, 2, 4):
        recall = 100 * np.count_nonzero(cd[s] <= tolerance) / max(int(s.sum()), 1)
        precision = 100 * np.count_nonzero(sd[c] <= tolerance) / max(int(c.sum()), 1)
        print(" ", tolerance, "px recall/precision:", f"{recall:.2f}% / {precision:.2f}%")

# Shared ink is dark; missing original ink is red; excess remake ink is blue.
orig_weight = (255 - a.min(axis=2)) / 255
candidate_weight = (255 - b.min(axis=2)) / 255
shared = np.minimum(orig_weight, candidate_weight)
only_source, only_candidate = orig_weight - shared, candidate_weight - shared
overlay = np.stack((
    255 - 225 * shared - 220 * only_candidate,
    255 - 225 * shared - 210 * only_source - 145 * only_candidate,
    255 - 225 * shared - 225 * only_source,
), axis=-1).clip(0, 255).astype(np.uint8)
Image.fromarray(overlay).save(args.output / "overlay.png")
triptych = Image.new("RGB", (original.width * 3, original.height), "white")
triptych.paste(original, (0, 0))
triptych.paste(candidate_at_origin, (original.width, 0))
triptych.paste(Image.fromarray(overlay), (original.width * 2, 0))
triptych.save(args.output / "original-remake-overlay.png")
