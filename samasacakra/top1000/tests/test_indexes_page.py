"""H8638 — gates for docs/samasa-indexes.html (the cross-linked indexes page).

The page is GENERATED (samasacakra/build_samasa_indexes.py); these tests gate
the committed output:

  * canary: the committed page is byte-identical to a fresh generator render
    (hand-editing the page fails the suite — regenerate instead);
  * every id is unique and every internal #anchor resolves;
  * taxonomy completeness: exactly the 4 classes / 9 families / 58 leaves of
    samasacakra-taxonomy.json, once each, plus kevala outside the count;
  * reciprocity: every type<->material edge appears on BOTH sides (chip on the
    type row and back-chip in the material card) with the same kind, and no
    chip exists without a model edge;
  * published targets: external links stay inside the verified-published
    allowlist (the dead csl-guides quiz URL must never return), paragraph
    anchors exist on the paragrafy page, gallery plates and lesson files
    exist on disk, every type id also routes on the wheel (docs/index.html
    data-id parity), and the wheel navigation is preserved (kevalachip,
    corpus-share controls, quiz) with the new indexchip present.
"""

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "samasacakra"))

import build_samasa_indexes as idx  # noqa: E402

PAGE_PATH = REPO / "docs" / "samasa-indexes.html"
WHEEL_PATH = REPO / "docs" / "index.html"
PARAGRAFY_PATH = REPO / "docs" / "paragrafy" / "index.html"


class Collector(HTMLParser):
    """Collect ids, internal anchors and edge chips from the rendered page."""

    def __init__(self):
        super().__init__()
        self.ids = []
        self.hrefs = []
        self.chips = []  # (href, data-kind, data-tp, data-mat)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if "href" in a:
            self.hrefs.append(a["href"])
            if a["href"].startswith(("#mat-", "#tp-")) and "data-tp" in a:
                self.chips.append((a["href"], a.get("data-kind"),
                                   a.get("data-tp"), a.get("data-mat")))


def page_html():
    return PAGE_PATH.read_text(encoding="utf-8")


def collected():
    c = Collector()
    c.feed(page_html())
    return c


def model():
    return idx.build_model()


def type_ids(m):
    ids = {idx.KEVALA_ID}
    for c in m["tax"]["classes"]:
        ids.add(c["id"])
        for f in c["families"]:
            ids.add(c["id"] + "--" + f["id"])
            for leaf in f["leaves"]:
                ids.add(c["id"] + "--" + f["id"] + "--" + leaf["id"])
    return ids


# --- canary -----------------------------------------------------------------

def test_committed_page_is_generator_output():
    m = model()
    rendered = idx.render(m)
    assert rendered == idx.render(m), "generator must be deterministic"
    assert page_html() == rendered, (
        "docs/samasa-indexes.html diverged from the generator — "
        "rerun `python samasacakra/build_samasa_indexes.py` instead of "
        "hand-editing the page")


# --- anchors ----------------------------------------------------------------

def test_ids_are_unique_and_internal_anchors_resolve():
    c = collected()
    dupes = {i for i in c.ids if c.ids.count(i) > 1}
    assert not dupes, f"duplicate ids: {sorted(dupes)}"
    idset = set(c.ids)
    broken = sorted({h for h in c.hrefs
                     if h.startswith("#") and h[1:] not in idset})
    assert not broken, f"internal anchors with no target: {broken}"


# --- taxonomy completeness ---------------------------------------------------

def test_taxonomy_is_complete_and_accurate():
    m = model()
    raw = json.loads((REPO / "samasacakra" / "samasacakra-taxonomy.json")
                     .read_text(encoding="utf-8"))
    assert m["n_classes"] == len(raw["classes"]) == 4
    assert m["n_families"] == sum(len(c["families"]) for c in raw["classes"]) == 9
    assert m["n_leaves"] == sum(len(f["leaves"]) for c in raw["classes"]
                                for f in c["families"]) == 58
    c = collected()
    idset = set(c.ids)
    missing = sorted("tp-" + t for t in type_ids(m) if "tp-" + t not in idset)
    assert not missing, f"taxonomy anchors missing from the page: {missing}"
    # the summary line states the canonical counts
    assert "4 класса · 9 семейства · 58 лепестков-подтипов" in page_html()


def test_leaf_rows_are_numbered_like_the_wheel():
    m = model()
    html_doc = page_html()
    no = 0
    for cl in m["tax"]["classes"]:
        for f in cl["families"]:
            for leaf in f["leaves"]:
                no += 1
                lid = f'{cl["id"]}--{f["id"]}--{leaf["id"]}'
                row = html_doc.split(f'id="tp-{lid}"', 1)[1][:400]
                assert f"№ {no}" in row, f"leaf {lid} must be numbered {no}"


def test_legacy_alias_resolution():
    m = model()
    valid = type_ids(m)
    for alias, target in m["aliases"].items():
        assert target in valid, f"alias {alias} -> unknown id {target}"
    # ekadesin is surfaced on the merged prathama row, not as its own anchor
    assert "бывший идентификатор «ekadesin»" in page_html()


def test_d1_family_relation_is_reciprocal_and_marked():
    html_doc = page_html()
    assert 'id="rel-d1-a"' in html_doc and 'id="rel-d1-b"' in html_doc
    a_block = html_doc.split('id="rel-d1-a"', 1)[1][:1200]
    b_block = html_doc.split('id="rel-d1-b"', 1)[1][:1200]
    assert 'href="#rel-d1-b"' in a_block
    assert 'href="#rel-d1-a"' in b_block
    assert "голосование D1" in a_block and "голосование D1" in b_block


def test_every_family_row_links_its_wheel_card():
    m = model()
    html_doc = page_html()
    for c in m["tax"]["classes"]:
        for f in c["families"]:
            fid = f'{c["id"]}--{f["id"]}'
            seg = html_doc.split(f'id="tp-{fid}"', 1)[1][:1500]
            assert f'href="{idx.PAGES}#k={fid}"' in seg, fid


def test_paragrafy_card_carries_direct_published_anchor_links():
    m = model()
    html_doc = page_html()
    card = html_doc.split('id="mat-paragrafy"', 1)[1].split('id="mat-', 1)[0]
    expected = sorted({e["href"] for e in m["edges"]
                       if e["mat"] == "paragrafy" and e["href"]})
    assert expected, "no § edges"
    for href in expected:
        assert href in card, href


# --- reciprocity -------------------------------------------------------------

def test_edges_are_reciprocal_between_both_indexes():
    m = model()
    model_edges = {(e["tp"], e["mat"], e["kind"]) for e in m["edges"]}
    type_side = set()
    mat_side = set()
    for href, kind, tp, mat in collected().chips:
        if href.startswith("#mat-"):
            assert href == f"#mat-{mat}"
            type_side.add((tp, mat, kind))
        else:
            assert href == f"#tp-{tp}"
            mat_side.add((tp, mat, kind))
    assert type_side == model_edges, (
        "classification-side chips diverge from the evidence model")
    assert mat_side == model_edges, (
        "material-side back-chips diverge from the evidence model")
    valid = type_ids(m)
    known = {x[0] for x in m["materials"]} | {
        "uroki-" + l["slug"].split("-")[0] for l in m["pilot"]["lessons"]}
    for tp, mat, _k in model_edges:
        assert tp in valid and mat in known


def test_example_edges_never_point_at_whole_classes():
    # ◆ "example" is reserved for concrete leaf/kevala proofs; class-level
    # coverage must be ◇ "family" — the distinction the page exists to keep.
    m = model()
    for e in m["edges"]:
        depth = e["tp"].count("--")
        if e["kind"] == "example":
            assert e["tp"] == idx.KEVALA_ID or depth == 2, e
        else:
            assert depth == 0, e


# --- published targets -------------------------------------------------------

ALLOWLIST = (
    re.compile(r"^https://gasyoun\.github\.io/SamasaChakram(/|$)"),
    re.compile(r"^https://gasyoun\.github\.io/kosha/reading/samasa/drills/?$"),
    re.compile(r"^https://github\.com/gasyoun/SamasaChakram/blob/main/"),
)


def test_external_links_stay_on_verified_published_surfaces():
    html_doc = page_html()
    assert idx.DEAD_QUIZ_URL not in html_doc, (
        "the dead csl-guides quiz URL must never return to the page")
    bad = []
    for h in collected().hrefs:
        if h.startswith("http"):
            if not any(p.match(h) for p in ALLOWLIST):
                bad.append(h)
    assert not bad, f"links outside the published allowlist: {bad}"


def test_paragraph_anchors_exist_on_the_paragrafy_page():
    m = model()
    para_ids = set(re.findall(r'id="(p-[0-9-]+)"',
                              PARAGRAFY_PATH.read_text(encoding="utf-8")))
    checked = 0
    for e in m["edges"]:
        if e["mat"] == "paragrafy" and e["href"]:
            anchor = e["href"].rsplit("#", 1)[1]
            assert anchor in para_ids, f"{anchor} missing in docs/paragrafy/"
            checked += 1
    assert checked >= 8, "expected the pilot § edges to be verified"


def test_gallery_plates_and_lesson_files_exist():
    m = model()
    for e in m["edges"]:
        if e["mat"] == "gallery" and e["detail"]:
            for plate in e["detail"].split("пластина: ", 1)[1].split(", "):
                assert (REPO / "klammerdiagramm" / plate).exists(), plate
    for l in m["pilot"]["lessons"]:
        assert (REPO / "docs" / "uroki" / (l["slug"] + ".html")).exists(), l["slug"]


def test_kosha_drills_link_is_the_live_url():
    m = model()
    live = [e for e in m["edges"] if e["mat"] == "kosha-drills"]
    assert live, "kosha drills material missing"
    card_url = next(x[2] for x in m["materials"] if x[0] == "kosha-drills")
    assert card_url == ("https://gasyoun.github.io/kosha/reading/"
                        "samasa/drills/")


def test_every_type_id_routes_on_the_wheel():
    html_doc = WHEEL_PATH.read_text(encoding="utf-8")
    m = model()
    for t in type_ids(m):
        if t == idx.KEVALA_ID:
            assert '"kevala": {"kind": "kevala"' in html_doc
        else:
            assert f'data-id="{t}"' in html_doc, f"wheel has no segment {t}"


def test_wheel_navigation_preserved_and_indexes_discoverable():
    html_doc = WHEEL_PATH.read_text(encoding="utf-8")
    # pre-existing navigation (H8573 pilot) untouched
    for marker in ('id="kevalachip"', 'class="freqbar"', 'id="quizbtn"',
                   'id="scripttoggle"', 'id="bandlegend"'):
        assert marker in html_doc, f"wheel nav lost: {marker}"
    # the new discoverable entry at the generator source
    assert 'id="indexchip"' in html_doc
    assert "samasa-indexes.html" in html_doc
    # and the indexes page links back to the wheel
    assert f'href="{idx.PAGES}"' in page_html()
