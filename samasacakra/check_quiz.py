#!/usr/bin/env python
"""Fail-closed check for the embedded samāsa quiz (wheel as its own answer key).

Run after build_samasacakra.py:
    python samasacakra/check_quiz.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HERE = ROOT.parent
WHEEL = ROOT / "samasacakra-wheel.html"
PAGES = HERE / "docs" / "index.html"

MARKERS = (
    'id="quiz"',
    'id="quizbtn"',
    'data-qmode="type"',
    'data-qmode="vigraha"',
    'const QUIZ_LEAVES',
    'id="qreveal"',
    'href="#k=',
)


def extract_meta(html: str) -> dict:
    token = "const META = "
    at = html.find(token)
    assert at >= 0, "const META not found in generated page"
    obj, _ = json.JSONDecoder().raw_decode(html[at + len(token):])
    return obj


def main() -> int:
    errors = []
    for path in (WHEEL, PAGES):
        if not path.exists():
            errors.append(f"missing generated page: {path}")
            continue
        html = path.read_text(encoding="utf-8")
        for marker in MARKERS:
            if marker not in html:
                errors.append(f"{path.name}: missing quiz marker {marker!r}")
        meta = extract_meta(html)
        leaves = [(lid, m) for lid, m in meta.items() if m.get("kind") == "leaf"]
        playable = [(lid, m) for lid, m in leaves if m.get("ex") and m.get("vigraha") and m.get("ru")]
        if len(leaves) < 58:
            errors.append(f"{path.name}: only {len(leaves)} leaves in META (expected >= 58)")
        if len(playable) < 58:
            errors.append(f"{path.name}: only {len(playable)} quiz-eligible leaves")
        classes = {m["class"] for _, m in playable}
        if len(classes) < 4:
            errors.append(f"{path.name}: only {len(classes)} classes in quiz pool")
        examples = [m["ex"] for _, m in playable]
        if len(examples) != len(set(examples)):
            errors.append(f"{path.name}: duplicate examples in quiz pool")
        # every correct answer must resolve to a wheel segment via #k=<id>
        ids = set(re.findall(r'data-id="([^"]+)"', html))
        for lid, _ in playable:
            if lid not in ids:
                errors.append(f"{path.name}: quiz answer id has no wheel segment: {lid}")

    if errors:
        print("QUIZ CHECK: FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print(f"QUIZ CHECK: PASS ({len(MARKERS)} markers, 2 generated pages, 58+ leaf answers)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
