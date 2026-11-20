import sys, os, re, json, base64, argparse
sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Klammerdiagramm (German-Indological bracket diagram) generator.
# Right-branching binary nesting of a long compound: the rightmost pair is the
# deepest node (A); each member to the LEFT accretes onto the accumulated right
# group; the outermost node (last letter) spans the whole word.
#
# PLATE-CALIBRATED HOUSE MODE (H814, 12-07-2026) — geometry calibrated to the printed
# reference plate (assets/klammerdiagramm-target-plate.png): the H814 pass fitted the
# plate's label grid and proportions in THIS house style; it was not the 1:1 trace the
# earlier prose claimed (misleading claim corrected H8424, 18-11-2026 — the plate's
# own pair-band graphic language is reproduced only by the opt-in plate mode below):
#   * every hatched bar carries TWO up-arrows, one on each vertical edge, tips
#     just under the compound line (pre-H8485 member furniture — the current
#     renderer draws ONE open arrow per member; see OPEN-ARROW MEMBER MODE below)
#   * each node is an L-shaped hatched bracket: the LEFT member's vertical bar
#     turns at node depth into a horizontal hatched band running right, ending
#     at the node label; the label sits in line with the band
#   * a THIN elbow connector runs from the label rightward, then up to the
#     next-deeper node's label (its band bottom)
#   * the deepest node (A) is a ∪: both member bars meet one bottom band, with
#     the label in a white gap near the right bar
#   * "I часть" / "II часть" captions sit INLINE with their dashed rules; the
#     two rules dip toward the part-split hyphen as mirrored ogee (S) curves
#     meeting in a cusp just above the hyphen
#   * the compound ends with a trailing hyphen (svabhāvā-)
#   * per-node label x-positions are plate parameters (label_x below) — tune
#     them against the plate being reproduced, they are NOT derivable
# Style: font Charis (SIL OFL); "II часть" start is ASKED, never guessed.
#
# TIGHT-RUN MEASURED LAYOUT (H792 follow-up, 15-07-2026) — the plate sets the
# compound as ONE tightly hyphenated run (uddāma-ajñāna-…-svabhāvā-), hyphens
# flush after each member. When the config has NO "cx", member positions are
# now DERIVED from real Charis advance widths (read from the committed subset
# charis-klammer-subset.woff2): each member is a left-anchored tspan pinned to
# the metric grid (kerning inside a member cannot drift the bars), bars are
# per-member (min(BW, advance-8)), and the I/II split cusp sits exactly on the
# hyphen after the last I-часть member. A config WITH explicit "cx" keeps the
# legacy spaced layout (centered members, hyphens floating in the gaps).
#
# HISTORICAL PAIR-BAND MODE (H8424, 18-11-2026) — opt-in via a "plate" object in
# the config JSON (see klammerdiagramm-uddama-plate-historical.json). Renders the
# printed plate's OWN graphic language, verbatim from scan-measured coordinates
# carried by the JSON (they are scan parameters, not derivable): four hatched PAIR
# BANDS (node A a rectangle spanning its two members; C, E, G L polygons whose
# vertical arm runs between the pair-member centres and whose foot ends at the
# next-deeper label), 2px stems with OPEN (unfilled) arrowheads at each pair-member
# centre, 13px slash hatch from the band top to the band bottom, band bottoms
# gapped around their labels, and bare elbow labels B/D/F connected right of the
# label to the next-deeper label's x, then up to its gap. The compound stays the
# tight-run measured line (all Sanskrit, the I/II split hyphen, the trailing stem
# hyphen), globally translated so the split hyphen sits under the plate cusp
# (cusp_x), with a short dashed drop from the cusp to drop_y. Configs without
# "plate" render exactly as before — legacy/default output stays byte-identical.
#
# OPEN-ARROW MEMBER MODE (H8485, 20-11-2026) — every real visible member carries
# ONE OPEN (unfilled) arrow aligned to the member's centre, its tail joined by a
# single stem to the member's hatched bar and on into the band; the legacy pair of
# filled edge-arrows and the two border stems protruding on either side are gone.
# Ghost members (madhyamapadalopin restorations) never draw arrows or stems. The
# I/II часть captions are measured against their rule zones: inline where they fit
# (legacy geometry byte-preserved), raised to their own aligned row above when a
# narrow part-split leaves no room (śīta-uṣṇa-sukha-duḥkha-dāḥ, janma-roga-maraṇa-ādiḥ)
# so the caption and the ogee never compete for the same space. PNG export:
# klammerdiagramm/export_png.py (offline Chrome, SVG-bounds crop, 1× light).
#
# CANONICAL TOOL OF /klammerdiagramm (H792, 14-07-2026) — CLI:
#   python build_klammerdiagramm.py                    # committed uddāma example
#   python build_klammerdiagramm.py --config my.json --out my-diagram
# emits <out>.svg AND <out>.html; the HTML embeds a base64 WOFF2 subset of
# Charis 7.000 (family renamed "Klammer Serif" per the OFL Reserved-Font-Name
# rules — see make_charis_subset.py + OFL-Charis.txt) so the render is 1:1 on
# machines WITHOUT Charis installed. Config JSON keys: tokens, II_START, nodes
# ([label, left_idx, right_idx, label_x], deepest first), optional cx (legacy
# spaced layout), title/desc/style{FS,STEP,...} overrides.
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
WOFF2 = os.path.join(HERE, "charis-klammer-subset.woff2")
FONT = "'Klammer Serif', 'Charis SIL', Charis, 'Gentium Plus', Georgia, serif"

STYLE = dict(
    FS=39,          # compound (tight-run mode: plate-proportioned, word fills ~92% of W)
    FS_NODE=26,     # node labels A..G
    FS_PART=21,     # the I/II часть captions
    BW=92,          # hatched bar width (tight-run: per-member cap; legacy: exact width)
    BH2=24,         # half-height of the horizontal hatched band
    X0=44,          # left margin of the compound run (tight-run mode)
    Y_TEXT=126,     # compound baseline
    ARROW_TIP=146,  # y of arrowhead apexes
    HATCH_TOP=162,  # top of the hatched fill
    Y_A=222,        # band centreline of the deepest node A
    STEP=70,        # uniform vertical step between successive nodes
    GAP=17,         # half-width of the white gap holding a node label
)

# The committed worked example — the printed reference plate (H814-traced,
# H792 tight-run refit 15-07-2026). label_x values are plate parameters,
# carried over from the H814 trace by interpolation between member centres.
# Canonical uddāma constituency = E. Leitan's reading (MG vote D5, 16-07-2026, H997):
# the {uddāma-ajñāna-rūpa} block (P→Q) joins the right-branching prabalatama-…-svabhāvā
# tail (A→B→C→D) at the outermost node R; the I/II часть ‖-mark falls before svabhāvā.
# The superseded MG-signed-off plate reading (pure right-branching chain, split at tamaḥ,
# H814 1:1 trace) is preserved as klammerdiagramm-uddama-plate-historical.json — pass it
# with --config to reproduce the historical plate; target-plate.png (the printed scan) is
# unchanged. The label_x values here are the plate calibration grid measured off that scan.
DEFAULT_CONFIG = {
    "tokens": ["uddāma", "ajñāna", "rūpa", "prabalatama", "tamaḥ", "stoma", "soma", "svabhāvā"],
    "II_START": 7,      # I/II часть ‖-mark before svabhāvā (Leitan) — ASK the user per run
    # binary nodes, deepest first: [label, left, right, label_x, level]; a string child
    # names an already-listed node, an int a token index. Left block + right tail, joined:
    "nodes": [
        ["A", 6,   7,   990, 0],   # soma + svabhāvā       (deepest ∪, tail)
        ["P", 0,   1,   183, 0],   # uddāma + ajñāna       (deepest ∪, block: "boundless ignorance")
        ["B", 5,   "A", 895, 1],   # stoma + [A]
        ["Q", "P", 2,   315, 1],   # [P] + rūpa            (mirrored — the {uddāma-ajñāna-rūpa} block)
        ["C", 4,   "B", 780, 2],   # tamaḥ + [B]
        ["D", 3,   "C", 620, 3],   # prabalatama + [C]     (tail spans prabalatama…svabhāvā)
        ["R", "Q", "D", 430, 4],   # [Q] + [D]             (directed join, head = the tail)
    ],
    "title": "Klammerdiagramm",
    "desc": "German-Indological bracket diagram of the uddāma compound in E. Leitan's "
            "constituency (MG vote D5, 16-07-2026): the {uddāma-ajñāna-rūpa} block joins the "
            "right-branching prabalatama-tamaḥ-stoma-soma-svabhāvā tail at the outermost node; "
            "the I/II часть ‖-mark falls before svabhāvā, the ultimate head.",
}

_METRICS = None

def _measure(s, fs):
    # advance width of s at font-size fs, from the committed Charis subset
    global _METRICS
    if _METRICS is None:
        from fontTools.ttLib import TTFont
        f = TTFont(WOFF2)
        _METRICS = (f["head"].unitsPerEm, f.getBestCmap(), f["hmtx"])
    upm, cmap, hmtx = _METRICS
    return sum(hmtx[cmap[ord(c)]][0] for c in s) / upm * fs


_CHANNEL_KEYS = {"token-row", "part-i", "part-ii"} | {f"label-{c}" for c in "ABCDEFG"}
_PATH_RE = re.compile(r"[MLZ0-9.\- ]+")

def _load_plate_lettering(filename, base_dir):
    """Load validated contour layers from an optional sibling JSON asset."""
    if filename is None:
        return {}
    if not isinstance(filename, str) or os.path.basename(filename) != filename or not filename.endswith(".json"):
        raise ValueError("lettering_file must be a sibling JSON basename")
    with open(os.path.join(base_dir, filename), encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or data.get("format") != 2:
        raise ValueError("expected format 2 lettering asset")
    opacities = data.get("opacities")
    if not isinstance(opacities, list) or len(opacities) != 3 or not all(
        type(opacity) in (int, float) and 0 < opacity <= 1 for opacity in opacities
    ):
        raise ValueError("expected three lettering layer opacities")
    channels = data.get("channels")
    if not isinstance(channels, dict) or set(channels) != _CHANNEL_KEYS:
        raise ValueError("lettering asset must contain all ten text groups")
    colors = ("cyan", "magenta", "yellow")
    lettering = {}
    for cid, plates in channels.items():
        if not isinstance(plates, list) or len(plates) != 3:
            raise ValueError(f"{cid}: expected three color planes")
        entries = []
        for ci, plate in enumerate(plates):
            if not isinstance(plate, list) or len(plate) != 3:
                raise ValueError(f"{cid}: expected three contour layers per plane")
            for opacity, d in zip(opacities, plate):
                if not isinstance(d, str) or not _PATH_RE.fullmatch(d) or not d.startswith("M") or not d.endswith("Z"):
                    raise ValueError(f"{cid}: invalid SVG contour path")
                entries.append((colors[ci], opacity, d))
        lettering[cid] = tuple(entries)
    return lettering


def _plate_lettering_element(markup, element_id, lettering):
    """Wrap text markup with outlined color-plate <g> when lettering exists."""
    plates = lettering.get(element_id)
    if not plates:
        return markup
    parts = ['<g id="outlined-%s" aria-hidden="true">' % element_id]
    for color, opacity, d in plates:
        parts.append(
            '<path d="%s" fill="%s" opacity="%s" fill-rule="evenodd" '
            'style="mix-blend-mode:multiply"/>' % (d, color, opacity)
        )
    parts.append("</g>")
    return "".join(parts) + markup.replace("<text", '<text opacity="0"', 1)


def _build_historical_plate(cfg):
    """Reconstruct the 1213x723 printed Sanskrit plate as pure-vector SVG.

    Every coordinate below is a typed-in default collected in D and can be
    overridden piecewise through the optional cfg["plate"] measurement dict.
    """
    from xml.sax.saxutils import escape as _esc

    D = {
        "width": 1213, "height": 723, "font_size": 40, "font_stroke": 0, "baseline": 128,
        "token_xs": [51, 202, 329, 421, 657, 776, 892, 999], "hyphen": "-",
        "captions": ("I часть", "II часть"), "caption_xs": (360, 918),
        "caption_y": 60, "caption_fs": 23, "sans": "Arial",
        "dash_y": 56, "dash_segs": [(51, 307), (414, 590), (710, 862), (975, 1166)],
        "dash_pat": "4 3", "rail_dash": None, "thin_w": 1.0,
        "wing_x": (590, 710), "cusp": (650, 96), "drop_y2": 114,
        "brace_controls": ((633.17, 55.16, 649.15, 90), (669.48, 54.19, 650.1, 88.66)),
        "top": 154.0, "arrow_tip_y": 155, "arrow_leg_y": 162,
        "arrow_half": 6, "arrow_w": 1.5,
        "rect_a": (943, 1076, 154, 222),
        "ells": {"C": (709, 833, 917, 293, 364), "E": (371, 531, 667, 434, 505),
                 "G": (126, 263, 387, 575, 644)},
        "labels": {"A": (1012, 222), "C": (810, 364), "E": (516, 505), "G": (256, 644),
                   "B": (918, 293), "D": (667, 434), "F": (387, 575)},
        "elbows": {"B": (935, 293, 1012, 240), "D": (683, 434, 810, 381),
                   "F": (404, 575, 516, 523)},
        "gap": 17, "label_fs": 21, "label_dy": 8, "label_offsets": {},
        "hatch_step": 13.057, "hatch_slope": 0.899, "hatch_w": 0.82,
        "phase": {"A": 12.84, "C": 12.84, "E": 12.84, "G": 10.39},
        "edge_w": 2.0, "foot_skip": 15,
    }
    D.update(cfg.get("plate") or {})
    lettering = _load_plate_lettering(D.get("lettering_file"), HERE)
    TOP, GAP = float(D["top"]), float(D["gap"])
    LBS, ELS = D["labels"], D["ells"]
    ELBOW_OF = {"C": "B", "E": "D", "G": "F"}

    def pts(poly):
        return " ".join("%.2f,%.2f" % (p[0], p[1]) for p in poly)

    def line(ident, a, b, wid, dash=None, offset=0):
        extra = ' stroke-dasharray="%s"' % dash if dash else ""
        if dash and offset:
            extra += ' stroke-dashoffset="%s"' % offset
        return ('<line id="%s" x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" '
                'stroke="black" stroke-width="%s"%s/>' % (ident, a[0], a[1], b[0], b[1], wid, extra))

    shapes = {}
    ax0, ax1, ay0, ay1 = D["rect_a"]
    la = LBS["A"]
    shapes["A"] = {"poly": [(ax0, ay0), (ax1, ay0), (ax1, ay1), (ax0, ay1)],
                   "bbox": (ax0, ax1, ay0, ay1), "labels": ["A"],
                   "edges": [(ax0, ay0, ax0, ay1), (ax1, ay0, ax1, ay1),
                             (ax0, ay1, la[0] - GAP, ay1), (la[0] + GAP, ay1, ax1, ay1)]}
    for nm in ("C", "E", "G"):
        left, inner, footend, shy, bot = ELS[nm]
        lb, le = LBS[nm], LBS[ELBOW_OF[nm]]
        shapes[nm] = {"poly": [(left, TOP), (inner, TOP), (inner, shy), (footend, shy),
                               (footend, bot), (left, bot)],
                      "bbox": (left, footend, TOP, bot), "labels": [nm, ELBOW_OF[nm]],
                      "edges": [(left, TOP, left, bot), (inner, TOP, inner, shy),
                                (inner, shy, le[0] - GAP, shy),
                                (footend, shy + D["foot_skip"], footend, bot),
                                (left, bot, lb[0] - GAP, bot),
                                (lb[0] + GAP, bot, footend, bot)]}

    def hatch(bbox, phase):
        xlo, xhi, ylo, yhi = bbox
        slope, step = D["hatch_slope"], D["hatch_step"]
        k0 = int((xlo + slope * ylo - phase) // step)
        k1 = int((xhi + slope * yhi - phase) // step) + 1
        out = []
        for k in range(k0, k1 + 1):
            c = phase + k * step
            out.append("M%.2f %.2fL%.2f %.2f" % (c - slope * ylo, ylo, c - slope * yhi, yhi))
        return "".join(out)

    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img">'
         % (D["width"], D["height"], D["width"], D["height"]),
         '<title>%s</title>' % _esc(cfg.get("title", "")),
         '<desc>%s</desc>' % _esc(cfg.get("desc", "")),
         '<rect id="plate-bg" x="0" y="0" width="%d" height="%d" fill="white"/>'
         % (D["width"], D["height"])]
    row = "".join('<tspan x="%s">%s%s</tspan>' % (x, _esc(t), D["hyphen"])
                  for x, t in zip(D["token_xs"], cfg.get("tokens") or ()))
    token_markup = ('<text id="token-row" font-family="%s" font-size="%s" y="%s" '
             'stroke="white" stroke-width="%s">%s</text>'
             % (FONT, D["font_size"], D["baseline"], D["font_stroke"], row))
    s.append(_plate_lettering_element(token_markup, "token-row", lettering))
    for i, cap in enumerate(D["captions"]):
        ident = ("part-i", "part-ii")[i]
        markup = ('<text id="%s" x="%s" y="%s" text-anchor="middle" font-family="%s" '
                 'font-size="%s" fill="black">%s</text>'
                 % (ident, D["caption_xs"][i], D["caption_y"],
                    D["sans"], D["caption_fs"], _esc(cap)))
        s.append(_plate_lettering_element(markup, ident, lettering))
    if D.get("rail_rects"):
        for i, rectangles in enumerate(D["rail_rects"], 1):
            dashes = "".join('<rect x="%s" y="%s" width="%s" height="%s"/>' % tuple(r)
                             for r in rectangles)
            s.append('<g id="span-%d" fill="black">%s</g>' % (i, dashes))
    else:
        for i, (dx1, dx2) in enumerate(D["dash_segs"]):
            dash, offset = D["rail_dash"][i] if D["rail_dash"] else (D["dash_pat"], 0)
            s.append(line("span-%d" % (i + 1), (dx1, D["dash_y"]), (dx2, D["dash_y"]),
                          D["thin_w"], dash, offset))
    cx, cy = D["cusp"]
    dash, offset, weight = D.get("brace_dash", (D["dash_pat"], 0, D["thin_w"]))
    for name, wx, controls in zip(("left", "right"), D["wing_x"], D["brace_controls"]):
        s.append('<path id="brace-%s" d="M%.2f %.2f C%.2f %.2f %.2f %.2f %.2f %.2f" fill="none" '
                 'stroke="black" stroke-width="%s" stroke-dasharray="%s" stroke-dashoffset="%s"/>'
                 % (name, wx, D["dash_y"], *controls, cx, cy, weight, dash, offset))
    if D.get("drop_segments"):
        for i, (start_y, end_y) in enumerate(D["drop_segments"]):
            s.append(line(f"hyphen-drop-{i}", (cx, start_y), (cx, end_y), D["edge_w"]))
    else:
        s.append(line("hyphen-drop", (cx, cy), (cx, D["drop_y2"]), D["thin_w"], D["dash_pat"]))
    for nm in ("A", "C", "E", "G"):
        shp = shapes[nm]
        s.append('<clipPath id="clip-%s"><polygon points="%s"/></clipPath>'
                 % (nm.lower(), pts(shp["poly"])))
        s.append('<mask id="mask-%s"><polygon points="%s" fill="white"/>'
                 % (nm.lower(), pts(shp["poly"])))
        for label in shp["labels"]:
            lx, ly = LBS[label]
            half, up, bevel = D.get("label_mask_profiles", {}).get(label, (GAP, 15, 0))
            left, right, top, bottom = lx-half, lx+half, ly-up, ly+14
            outline = ((left, top+bevel), (left+bevel, top), (right-bevel, top),
                       (right, top+bevel), (right, bottom), (left, bottom))
            s.append('<polygon points="%s" fill="black"/>' % pts(outline))
        s.append('</mask>')
        hatch_path = hatch(shp["bbox"], D["phase"][nm])
        transform = (' transform="translate(%s,0)"' % D["hatch_dx"]) if D.get("hatch_dx") else ""
        hatch_layers = D.get("hatch_layers", ((D["hatch_w"], 1),))
        strokes = "".join('<path d="%s" fill="none" stroke="black" stroke-width="%s" opacity="%s"%s/>'
                          % (hatch_path, width, opacity, transform) for width, opacity in hatch_layers)
        s.append('<g id="hatch-%s" clip-path="url(#clip-%s)" mask="url(#mask-%s)">%s</g>'
                 % (nm.lower(), nm.lower(), nm.lower(), strokes))
        for j, (a, b, c2, d2) in enumerate(shp["edges"]):
            if abs(c2 - a) + abs(d2 - b) < 0.01 or c2 < a:
                continue
            s.append(line("edge-%s-%d" % (nm, j), (a, b), (c2, d2), D["edge_w"]))
    stems = [D["rect_a"][0], D["rect_a"][1]]
    for nm in ("C", "E", "G"):
        stems += [ELS[nm][0], ELS[nm][1]]
    right_edge = D["rect_a"][1]
    s.append('<clipPath id="clip-a-arrow"><rect width="%s" height="%s"/></clipPath>'
             % (right_edge, D["height"]))
    for x in stems:
        # The print trims the last arrow at the outer edge of band A.
        clip = ' clip-path="url(#clip-a-arrow)"' if x == right_edge else ""
        half = D["arrow_half"] + (2.5 if x == right_edge else 0)
        tip = D.get("arrow_tip_overrides", {}).get(str(x), D["arrow_tip_y"])
        leg = D.get("arrow_leg_overrides", {}).get(str(x), D["arrow_leg_y"])
        dx, dh, dt, db, cap = D.get("arrow_detail", {}).get(str(x), (0, 0, 0, 0, "butt"))
        cx_tip, half = x + dx, half + dh
        s.append('<polyline id="arw-%d" points="%.2f,%.2f %.2f,%.2f %.2f,%.2f" fill="none" '
                 'stroke="black" stroke-width="%s" stroke-linecap="%s"%s/>'
                 % (x, cx_tip-half, leg+db, cx_tip, tip+dt, cx_tip+half, leg+db, D["arrow_w"], cap, clip))
    for nm, (lx, ly) in LBS.items():
        dx, dy = D["label_offsets"].get(nm, (0, 0))
        ident = "label-" + nm
        markup = ('<text id="%s" x="%.2f" y="%.2f" text-anchor="middle" font-family="%s" '
                 'font-size="%s" fill="black">%s</text>'
                 % (ident, lx + dx, ly + D["label_dy"] + dy, D["sans"], D["label_fs"], nm))
        s.append(_plate_lettering_element(markup, ident, lettering))
    for nm, (ex, ey, hx, hy2) in D["elbows"].items():
        s.append('<polyline id="elbow-%s" points="%.2f,%.2f %.2f,%.2f %.2f,%.2f" fill="none" '
                 'stroke="black" stroke-width="%s"/>'
                 % (nm, ex, ey, hx, ey, hx, hy2, D["edge_w"]))
    s.append('</svg>')
    return "\n".join(s)


def build_svg(cfg):
    if "plate" in cfg:
        return _build_historical_plate(cfg)
    st = dict(STYLE); st.update(cfg.get("style", {}))
    FS, FS_NODE, FS_PART = st["FS"], st["FS_NODE"], st["FS_PART"]
    BW, BH2 = st["BW"], st["BH2"]
    Y_TEXT, ARROW_TIP, HATCH_TOP = st["Y_TEXT"], st["ARROW_TIP"], st["HATCH_TOP"]
    Y_A, STEP, GAP = st["Y_A"], st["STEP"], st["GAP"]

    tokens, nodes, II_START = cfg["tokens"], cfg["nodes"], cfg.get("II_START")
    n = len(tokens)
    tight = "cx" not in cfg
    trail = cfg.get("trailing_hyphen", True)   # plate style quotes the compound as a stem-

    # GHOST MEMBERS (madhyamapadalopin — MG vote D4, 16-07-2026: the elided middle
    # element is RESTORED in the word line in editorial brackets, e.g. [priya] in
    # śāka-[priya]-pārthivaḥ; «одной только сноски недостаточно»). A ghost is measured
    # into the run but carries NO bar, NO arrows and NO token index (nodes reference
    # real members only). Config: "ghosts": [{"after": <token idx>, "text": "..."}].
    # Tight-run only.
    ghosts = {g["after"]: g["text"] for g in cfg.get("ghosts", [])}

    if tight:
        # tight-run measured layout: one flush-hyphenated run, metric-derived grid
        X0 = st["X0"]
        x = float(X0)
        starts, cx, hyx, bx, gh_runs = [], [], [], [], []
        for i, tok in enumerate(tokens):
            w = _measure(tok, FS)
            starts.append(x); cx.append(x + w / 2)
            half = min(BW, w - 8) / 2
            bx.append((cx[-1] - half, cx[-1] + half))
            x += w
            if i < n - 1 or trail:
                hw = _measure("-", FS)
                hyx.append(x + hw / 2); x += hw
            if i in ghosts:
                gtxt = f"[{ghosts[i]}]"
                gh_runs.append((x, gtxt + ("-" if (i < n - 1 or trail) else "")))
                x += _measure(gtxt, FS)
                if i < n - 1 or trail:
                    x += _measure("-", FS)
        W = st.get("W", round(x + X0))
        split = hyx[II_START - 1] if II_START else None   # cusp exactly on the split hyphen
    else:
        cx = cfg["cx"]
        bx = [(c - BW / 2, c + BW / 2) for c in cx]
        W = st.get("W", 1240)
        split = (cx[II_START - 1] + cx[II_START]) / 2 if II_START else None

    # Node entry: [label, left, right, label_x] + optional 5th element, the depth LEVEL
    # (0 = the Y_A rung). Without it, level = list position — the classic staircase.
    # Explicit levels let SIBLING constituents share a rung (two coordinated dvandva
    # pairs sit side by side before their coordination binds them one rung lower).
    lvl = {nd[0]: (nd[4] if len(nd) > 4 else i) for i, nd in enumerate(nodes)}
    H = Y_A + STEP * max(lvl.values()) + BH2 + 44
    INK = "currentColor"
    y_c = {lab: Y_A + STEP * v for lab, v in lvl.items()}
    lx  = {nd[0]: nd[3] for nd in nodes}

    svg = []
    svg.append(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
               f"font-family=\"{FONT}\">")
    svg.append(f'<title>{cfg.get("title", "Klammerdiagramm")}</title>')
    svg.append(f'<desc>{cfg.get("desc", DEFAULT_CONFIG["desc"])}</desc>')
    svg.append('<defs>')
    svg.append('<pattern id="hatch" width="5.5" height="5.5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
               '<line x1="0" y1="0" x2="0" y2="5.5" stroke="currentColor" stroke-width="0.8"/></pattern>')
    svg.append('</defs>')

    def hatch_rect(x0, y0, x1, y1):
        if x1 - x0 < 1:                          # degenerate on tight layouts — skip
            return
        svg.append(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{x1-x0:.0f}" height="{y1-y0:.0f}" fill="url(#hatch)"/>')

    def line(x0, y0, x1, y1, w=1.3):
        svg.append(f'<line x1="{x0:.0f}" y1="{y0:.0f}" x2="{x1:.0f}" y2="{y1:.0f}" stroke="{INK}" stroke-width="{w}"/>')

    def arrow(x, y_band):
        # ONE OPEN (unfilled) arrow per real visible member (H8485, 20-11-2026):
        # apex just under the member, aligned to the member's centre, tail joined
        # by a single stem that connects it to the member's hatched bar and on into
        # the band — replacing the legacy pair of filled edge arrows and their two
        # border stems protruding on either side. Ghost members never get here:
        # nodes reference real token indices only, ghosts have no cx entry.
        svg.append(f'<path d="M{x-6.5:.0f} {ARROW_TIP+13:.0f} L{x:.0f} {ARROW_TIP:.0f} L{x+6.5:.0f} {ARROW_TIP+13:.0f}" '
                   f'fill="none" stroke="{INK}" stroke-width="1.6"/>')
        svg.append(f'<line x1="{x:.0f}" y1="{ARROW_TIP:.0f}" x2="{x:.0f}" y2="{y_band:.0f}" stroke="{INK}" stroke-width="1.3"/>')

    # --- part captions: dashed rules, captions INLINE, ogee dip at the split ---
    # Omitted entirely when the config has no II_START (e.g. the part-division adds
    # nothing, or a human chose to drop the spans).
    if split is not None:
        Y_RULE, Y_DIP = 52, 96
        Y_UP = Y_RULE - 24                # raised caption row for narrow split zones (H8485)
        DASH = 'stroke-dasharray="2.5 4.5"'
        # Caption fit is MEASURED, not guessed (H8485): a caption sits inline with
        # its rule only when its zone is wide enough for the real text; in a narrow
        # part-split (śīta-uṣṇa-sukha-duḥkha-dāḥ, janma-roga-maraṇa-ādiḥ) the II
        # caption would land on the ogee wing, so it moves to its own aligned row
        # above — legacy inline geometry is byte-preserved wherever it fits.
        zones = ((44, split - 60), (split + 60, W - 50))
        caps = []
        for part, (cap_text, (z0, z1)) in enumerate(zip(("I часть", "II часть"), zones)):
            hw = _measure(cap_text, FS_PART) / 2 + 6
            mid = (z0 + z1) / 2
            if z1 - z0 >= 2 * hw + 8:
                caps.append((cap_text, mid, Y_RULE + 7))          # inline, legacy geometry
            elif part == 0:
                lo, hi = hw + 8, split - hw
                x = (lo + hi) / 2 if lo <= hi else lo
                caps.append((cap_text, min(x, W - hw - 8), Y_UP + 7))
            else:
                lo, hi = max(z0, split + hw), W - hw - 8          # keep inside the canvas,
                caps.append((cap_text, (lo + hi) / 2 if hi > lo else (split + W) / 2, Y_UP + 7))
        cap1, cap2 = caps[0][1], caps[1][1]
        def rule_seg(x0, x1):
            if x1 - x0 < 4:                      # nothing left of the dash on tight layouts
                return
            svg.append(f'<line x1="{x0:.0f}" y1="{Y_RULE}" x2="{x1:.0f}" y2="{Y_RULE}" stroke="{INK}" stroke-width="1.2" {DASH}/>')
        rule_seg(44, cap1 - 58)
        rule_seg(cap1 + 58, split - 60)
        rule_seg(split + 60, cap2 - 62)
        rule_seg(cap2 + 62, W - 50)
        # mirrored ogee curves meeting in a cusp just above the split hyphen
        svg.append(f'<path d="M{split-60:.0f} {Y_RULE} C {split-26:.0f} {Y_RULE+2} {split-6:.0f} {Y_RULE+18} {split:.0f} {Y_DIP}" '
                   f'fill="none" stroke="{INK}" stroke-width="1.2" {DASH}/>')
        svg.append(f'<path d="M{split+60:.0f} {Y_RULE} C {split+26:.0f} {Y_RULE+2} {split+6:.0f} {Y_RULE+18} {split:.0f} {Y_DIP}" '
                   f'fill="none" stroke="{INK}" stroke-width="1.2" {DASH}/>')
        for cap_text, x_cap, y_cap in caps:
            svg.append(f'<text x="{x_cap:.0f}" y="{y_cap:.0f}" font-size="{FS_PART}" text-anchor="middle" fill="{INK}">{cap_text}</text>')

    # --- the compound ----------------------------------------------------------
    if tight:
        # one flush run, each member+hyphen a tspan pinned to the metric grid
        svg.append(f'<text y="{Y_TEXT}" font-size="{FS}" fill="{INK}">')
        for i, (tok, sx) in enumerate(zip(tokens, starts)):
            hy = "-" if (i < n - 1 or trail) else ""
            svg.append(f'<tspan x="{sx:.1f}">{tok}{hy}</tspan>')
        for gx, gtxt in gh_runs:
            svg.append(f'<tspan x="{gx:.1f}">{gtxt}</tspan>')
        svg.append('</text>')
    else:
        # legacy spaced layout: centered members, hyphens floating in the gaps
        svg.append(f'<text y="{Y_TEXT}" font-size="{FS}" fill="{INK}">')
        for tok, c in zip(tokens, cx):
            svg.append(f'<tspan x="{c}" text-anchor="middle">{tok}</tspan>')
        svg.append('</text>')
        for i in range(n):
            if i == n - 1 and not trail:
                continue
            hx = (cx[i] + cx[i+1]) / 2 if i < n - 1 else cx[i] + 60
            svg.append(f'<text x="{hx:.0f}" y="{Y_TEXT}" font-size="{FS}" text-anchor="middle" fill="{INK}">-</text>')

    # --- nodes, deepest (A) first ----------------------------------------------
    # Node children: ints are token indices; a string names an already-drawn node
    # (the composite child); a LIST of token indices is a FLAT DVANDVA BLOCK — the
    # coordinate members share ONE band (an N-bar ∪ with a single label), because a
    # dvandva has no internal head: it is never chained like a determinative compound
    # (MG ruling 15-07-2026: every samāsa binds right-to-left; dvandva is coordinate).
    # Token on the LEFT = the classic right-accreting bracket; token on the RIGHT
    # (left child is a node label) = the MIRRORED bracket for left-nested compounds
    # like (rāja-ṛṣi)-vaṃśaḥ: the token's bar bends LEFT into the band, the label
    # sits at the band's left end, the elbow runs left then up.
    # Legacy configs (both children ints on every node) draw as before.
    for i, nd in enumerate(nodes):
        lab, lch, rch = nd[0], nd[1], nd[2]
        y = y_c[lab]
        bt, bb = y - BH2, y + BH2                    # band top / bottom
        lg0, lg1 = lx[lab] - GAP, lx[lab] + GAP      # label gap
        mirrored = isinstance(lch, str)

        def hline_clip(x0, x1, yy):
            # horizontal outline segment, clipped around the label gap
            if x1 - x0 < 1:
                return
            if lg1 <= x0 or lg0 >= x1:
                line(x0, yy, x1, yy)
            else:
                if lg0 > x0: line(x0, yy, lg0, yy)
                if lg1 < x1: line(lg1, yy, x1, yy)

        if isinstance(lch, (list, tuple)):
            # FLAT DVANDVA BLOCK. Members may be token indices (hatched bars with
            # arrows) or node labels (already-drawn sub-blocks — a coordination of
            # coordinations: a thin connector drops from the sub-block's band bottom,
            # under its label, into this shared band).
            edges = []
            for m in lch:
                if isinstance(m, str):
                    line(lx[m], y_c[m] + BH2 + 2, lx[m], bt)     # connector to the sub-block
                    edges.append((lx[m], lx[m]))
                else:
                    e0, e1 = bx[m]
                    hatch_rect(e0, HATCH_TOP, e1, bt)            # bar above the band
                    arrow(cx[m], bt)                            # one open arrow, stem into the band
                    edges.append((e0, e1))
            bl0, brN = edges[0][0], edges[-1][1]
            hatch_rect(bl0, bt, lg0, bb)             # the shared band, split at the label
            hatch_rect(lg1, bt, brN, bb)
            line(bl0, bt, bl0, bb)                   # band end walls
            line(brN, bt, brN, bb)
            for (pa, pb) in zip(edges[:-1], edges[1:]):
                hline_clip(pa[1], pb[0], bt)         # band top between consecutive members
            hline_clip(bl0, brN, bb)                 # band bottom, clipped at the label
            line(lg0, bt, lg0, bb)                   # label gap walls
            line(lg1, bt, lg1, bb)
        elif isinstance(lch, str) and isinstance(rch, str):
            # DIRECTED JOIN of two composites (tatpuruṣa over two sub-compounds,
            # head = the right child, read right-to-left): no lemma material of its
            # own, so no hatch — just the label with thin elbows to both children.
            line(lg0, y, lx[lch], y)
            line(lx[lch], y, lx[lch], y_c[lch] + BH2 + 2)
            line(lg1, y, lx[rch], y)
            line(lx[rch], y, lx[rch], y_c[rch] + BH2 + 2)
        elif not isinstance(lch, str) and (i == 0 or (len(nd) > 4 and not isinstance(rch, str) and rch is not None)):
            # ∪ pair — the deepest node, or a standalone pair placed on an explicit
            # level (a sub-compound forming beside its sibling, e.g. a bahuvrīhi and
            # a karmadhāraya pre-forming before a join binds them)
            li, ri = lch, rch
            bl, br = bx[li]
            # deepest node ∪: both members' bars drop into one bottom band
            hatch_rect(bl, HATCH_TOP, br, bb)
            hatch_rect(br, bt, lg0, bb)
            arrow(cx[li], bb)                                    # one open arrow per member
            line(bl, bb, lg0, bb)                                # band bottom edge
            rl, rr = bx[ri]
            hatch_rect(rl, HATCH_TOP, rr, bt)
            hatch_rect(lg1, bt, rr, bb)          # band resumes after the label (full stretch)
            arrow(cx[ri], bt)
            line(br, bt, lg0, bt)                                # band top edge
            line(lg0, bt, lg0, bb)                               # band end before the label
            if lg1 < rl:
                line(lg1, bt, rl, bt)
            line(lg1, bt, lg1, bb)                   # band resumes after the label
            line(lg1, bb, rr, bb)
        elif not mirrored:
            # token on the left: bar + band running RIGHT to the label
            li = lch
            prev = rch if isinstance(rch, str) else nodes[i-1][0]
            bl, br = bx[li]
            hatch_rect(bl, HATCH_TOP, br, bb)
            hatch_rect(br, bt, lg0, bb)
            arrow(cx[li], bb)                                    # one open arrow, stem into the band
            line(br, bt, lg0, bt)                                # band top edge
            line(bl, bb, lg0, bb)                                # band bottom edge
            line(lg0, bt, lg0, bb)                               # band end before the label
            # thin elbow connector: right from the label, then up to the deeper node
            line(lg1, y, lx[prev], y)
            line(lx[prev], y, lx[prev], y_c[prev] + BH2 + 2)
        else:
            # MIRRORED: token on the right, composite (deeper node) on the left
            ri = rch
            prev = lch
            bl, br = bx[ri]
            hatch_rect(bl, HATCH_TOP, br, bb)
            hatch_rect(lg1, bt, bl, bb)              # band running LEFT to the label
            arrow(cx[ri], bb)                                    # one open arrow, stem into the band
            line(lg1, bt, bl, bt)                    # band top edge
            line(lg1, bb, br, bb)                    # band bottom edge
            line(lg1, bt, lg1, bb)                   # band end after the label
            # elbow: LEFT from the label, then up to the deeper node
            line(lg0, y, lx[prev], y)
            line(lx[prev], y, lx[prev], y_c[prev] + BH2 + 2)

        svg.append(f'<text x="{lx[lab]}" y="{y+9:.0f}" font-size="{FS_NODE}" text-anchor="middle" fill="{INK}">{lab}</text>')

    svg.append('</svg>')
    return "\n".join(svg)


def wrap_html(svg_markup, cfg):
    # Base64-embed the renamed Charis subset so the diagram is 1:1 without any
    # installed font. OFL compliance: subset family is "Klammer Serif" (the
    # Reserved Font Name "Charis" may not name a Modified Version); licence
    # text ships as OFL-Charis.txt next to this script.
    with open(WOFF2, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    title = cfg.get("title", "Klammerdiagramm")
    # display no larger than the diagram's natural size (small diagrams otherwise inflate)
    m = re.search(r'viewBox="0 0 (\d+)', svg_markup)
    max_w = min(1280, int(m.group(1)) + 32) if m else 1280
    if "plate" in cfg and m:
        max_w = int(m.group(1))
    return f"""<!doctype html>
<html lang="sa">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
@font-face {{
  font-family: 'Klammer Serif'; /* subset of Charis 7.000 (SIL OFL) — see OFL-Charis.txt */
  src: url(data:font/woff2;base64,{b64}) format('woff2');
  font-weight: normal; font-style: normal;
}}
html, body {{ margin: 0; padding: 0; background: #fff; color: #1a1a1a; }}
@media (prefers-color-scheme: dark) {{ html, body {{ background: #14140f; color: #e8e4da; }} }}
main {{ max-width: {max_w}px; margin: 0 auto; padding: 24px 16px; }}
svg {{ display: block; width: 100%; height: auto; }}
</style>
</head>
<body>
<main>
{svg_markup}
</main>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="Klammerdiagramm SVG/HTML generator (canonical tool of /klammerdiagramm)")
    ap.add_argument("--config", help="JSON config (tokens, II_START, nodes, optional cx/title/desc/style); default = the committed uddāma plate")
    ap.add_argument("--out", help="output base path (writes <out>.svg and <out>.html); default = the committed example")
    ap.add_argument("--no-html", action="store_true", help="emit only the bare SVG (references the font by name, needs Charis installed)")
    args = ap.parse_args()

    if args.config:
        with open(args.config, encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = DEFAULT_CONFIG
    base = args.out or os.path.join(HERE, "klammerdiagramm-uddama-example")

    out = build_svg(cfg)
    svg_path = base + ".svg"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"wrote {svg_path} ({len(out)} bytes)")

    if not args.no_html:
        html = wrap_html(out, cfg)
        html_path = base + ".html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"wrote {html_path} ({len(html)} bytes; font embedded, no install needed)")


if __name__ == "__main__":
    main()
