#!/usr/bin/env python3
"""Independent recount check for `samasacakra/top1000/data/base_productivity.tsv`.

Re-derives a random sample of (base, role) counts straight from the two sources — its own
parser, its own fold, its own counting — and compares them with the `count` column.
Deliberately does **not** import the builder.

The fold follows the same *specification* documented in `build_base_productivity.py`
(length-preserving; anusvāra and homorganic nasals fold to `n`; word-final visarga and
word-final anusvara handled; `@` sandhi markers dropped), implemented here from scratch.

Usage:
    python scripts/check_base_productivity.py --cmps <path>/cmps.csv \
        --compounds <path>/compounds.txt [--sample 10] [--seed 8607]

Exit 0 = every sampled group reconciles; 1 = at least one mismatch.
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TSV = ROOT / "samasacakra" / "top1000" / "data" / "base_productivity.tsv"

VARIANTS = {
    "na": ["a", "an"],
    "nir": ["niś", "niṣ", "niḥ"],
    "dus": ["duṣ", "dur", "duḥ"],
    "pañcan": ["pañca"],
    "rājan": ["rāja"],
    "kim": ["kiṃ"],
}


def fold(text: str) -> str:
    s = (text or "").strip().lower().replace("@", "").replace("\u2019", "'").replace("\u02bc", "'")
    s = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", s)
    for variant in ("\u1e41", "\u1e43", "\u0902"):
        s = s.replace(variant, "\u1e43")
    if s.endswith("\u1e25"):
        s = s[:-1]
    if s.endswith(("\u1e43", "\u1e41")):
        s = s[:-1] + "m"
    s = re.sub("[\u1e43\u1e41](?=[pbm])", "m", s)
    for nasal in ("\u1e43", "\u1e41", "\u1e45", "\u00f1", "\u1e47"):
        s = s.replace(nasal, "n")
    for accent in ("\u0301", "\u0300", "\u0951", "\u0952"):
        s = s.replace(accent, "")
    return unicodedata.normalize("NFC", s)


def load_pairs(path: Path) -> list[tuple[str, list[str]]]:
    pairs = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if ";" not in line:
                continue
            compound, members = line.split(";", 1)
            parts = [p for p in members.split() if p]
            if parts:
                pairs.append((compound.strip(), parts))
    return pairs


def load_parents(path: Path) -> dict[str, list[str]]:
    parents: dict[str, list[str]] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            _, parent, children = line.split(":", 2)
            parents[fold(parent)] = [k.lstrip("+") for k in children.split() if k]
    return parents


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cmps", required=True, type=Path)
    parser.add_argument("--compounds", required=True, type=Path)
    parser.add_argument("--tsv", type=Path, default=DEFAULT_TSV)
    parser.add_argument("--sample", type=int, default=10)
    parser.add_argument("--seed", type=int, default=8607)
    args = parser.parse_args()

    pairs = load_pairs(args.cmps)
    parents = load_parents(args.compounds)
    with open(args.tsv, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))

    groups = sorted({(row["base"], row["role"]) for row in rows})
    random.seed(args.seed)
    sample = random.sample(groups, min(args.sample, len(groups)))

    failures = 0
    for base, role in sample:
        found: set[str] = set()
        for form in [base] + VARIANTS.get(base, []):
            key = fold(form)
            if role == "pūrvapada":
                found |= {fold(c) for c, members in pairs if fold(members[0]) == key}
                found |= {fold(kid) for kid in parents.get(key, [])}
            else:
                found |= {fold(c) for c, members in pairs if fold(members[-1]) == key}
        expected = int(next(r["count"] for r in rows if r["base"] == base and r["role"] == role))
        status = "OK" if expected == len(found) else "MISMATCH"
        if status == "MISMATCH":
            failures += 1
        print(f"{status:9s} {base:12s} {role:12s} tsv={expected:6d} recount={len(found):6d}")

    print(f"\n{len(sample) - failures}/{len(sample)} groups reconciled (seed {args.seed})")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
