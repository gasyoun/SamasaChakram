import sys, os, json
sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# One-shot provenance script for noto-deva-klammer-subset.woff2 (H1017,
# 16-07-2026) — the Devanāgarī layer font of the samāsa-cakra wheel.
#
# Source: Noto Serif Devanagari (variable), Google Fonts / The Noto Project
#   Authors, OFL 1.1 — bundled verbatim as OFL-NotoSerifDevanagari.txt.
# Recipe = FINDINGS §89 / Charis precedent: instantiate wght=400, subset to the
# glyphs the wheel actually uses (text closure keeps the GSUB conjunct/matra
# shaping reachable), RENAME the family ("Klammer Deva") so no Reserved Font
# Name question can arise, retain copyright/licence name records.
#
# Usage: python make_deva_subset.py <path-to-NotoSerifDevanagari-variable.ttf>
# ---------------------------------------------------------------------------

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.subset import Subsetter, Options
from indic_transliteration import sanscript

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "noto-deva-klammer-subset.woff2")
NEW_FAMILY = "Klammer Deva"

def has_cyrillic(s):
    return any("а" <= ch.lower() <= "я" or ch.lower() == "ё" for ch in s)

def deva(s):
    return sanscript.transliterate(s, sanscript.IAST, sanscript.DEVANAGARI)

T = json.load(open(os.path.join(HERE, "samasacakra-taxonomy.json"), encoding="utf-8"))
texts = ["समास", "चक्र", "।॥०१२३४५६७८९"]
for c in T["classes"]:
    texts.append(deva(c["name"]))
    for f in c["families"]:
        if not has_cyrillic(f["name"]):
            texts.append(deva(f["name"]))
        for leaf in f["leaves"]:
            for k in ("term", "ex", "vigraha"):
                if not has_cyrillic(leaf[k]):
                    texts.append(deva(leaf[k]))
text = "".join(sorted(set("".join(texts))))
print("codepoints needed:", len(text))

src = sys.argv[1]
font = TTFont(src)
instantiateVariableFont(font, {"wght": 400, "wdth": 100}, inplace=True)

opts = Options()
opts.flavor = "woff2"
opts.layout_features = ["*"]     # keep the full Devanagari shaping (conjuncts, matras)
opts.name_IDs = [0, 1, 2, 3, 4, 6, 13, 14, 16, 17]
opts.name_legacy = True
opts.glyph_names = False
sub = Subsetter(options=opts)
sub.populate(text=text)
sub.subset(font)

name = font["name"]
for rec in name.names:
    if rec.nameID in (1, 16):
        rec.string = NEW_FAMILY
    elif rec.nameID == 3:
        rec.string = f"{NEW_FAMILY}-Regular:subset-of-NotoSerifDevanagari"
    elif rec.nameID == 4:
        rec.string = f"{NEW_FAMILY} Regular"
    elif rec.nameID == 6:
        rec.string = "KlammerDeva-Regular"

font.flavor = "woff2"
font.save(OUT)
print(f"wrote {OUT} ({os.path.getsize(OUT)} bytes)")
