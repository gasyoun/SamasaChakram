import sys
sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Provenance companion to make_charis_subset.py: charis-klammer-italic-subset.woff2.
#
# Source: Charis 7.000 Italic, SIL (https://software.sil.org/charis/),
#   release https://github.com/silnrsi/font-charis/releases/tag/v7.000 — OFL 1.1.
# The subset is a Modified Version under the OFL, so it must NOT carry the
# Reserved Font Name "Charis": the family is renamed to "Klammer Serif".
# Copyright (ID 0), license description (ID 13) and license URL (ID 14) are
# retained; OFL-Charis.txt (the release's OFL.txt verbatim) sits next to the
# output. See OFL 1.1 conditions 2-3 and the OFL-FAQ on webfont subsetting.
#
# Ranges kept are identical to the Regular subset, so <em>/<i> is a real italic
# face and not a browser-synthesised slant of the Regular outlines.
#
# Usage: python make_charis_italic_subset.py <path-to-Charis-Italic.ttf>
# ---------------------------------------------------------------------------

import os
from fontTools.subset import Subsetter, Options
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "charis-klammer-italic-subset.woff2")
NEW_FAMILY = "Klammer Serif"

UNICODES = (
    list(range(0x0020, 0x007F)) + list(range(0x00A0, 0x0100)) +
    list(range(0x0100, 0x0180)) + list(range(0x1E00, 0x1F00)) +
    list(range(0x0400, 0x0460)) + list(range(0x2010, 0x2028))
)

src = sys.argv[1]
font = TTFont(src)

opts = Options()
opts.flavor = "woff2"
opts.layout_features = ["*"]        # keep ccmp/mark/mkmk — stacked diacritics
opts.name_IDs = [0, 1, 2, 3, 4, 6, 13, 14, 16, 17]
opts.name_legacy = True
opts.glyph_names = False
sub = Subsetter(options=opts)
sub.populate(unicodes=UNICODES)
sub.subset(font)

# Rename family away from the Reserved Font Name (OFL condition 3).
name = font["name"]
for rec in name.names:
    if rec.nameID in (1, 16):
        rec.string = NEW_FAMILY
    elif rec.nameID in (2, 17):
        rec.string = "Italic"
    elif rec.nameID == 3:
        rec.string = f"{NEW_FAMILY}-Italic:subset-of-Charis-7.000"
    elif rec.nameID == 4:
        rec.string = f"{NEW_FAMILY} Italic"
    elif rec.nameID == 6:
        rec.string = "KlammerSerif-Italic"

font.flavor = "woff2"
font.save(OUT)
print(f"wrote {OUT} ({os.path.getsize(OUT)} bytes, {len(UNICODES)} codepoints requested)")
