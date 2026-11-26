#!/usr/bin/env python3
"""Check visible frequency tables against the pilot and the published wheel."""
from html import unescape
from html.parser import HTMLParser
import json
import re

from build_frequency import OUTPUT, PILOT, render


class FrequencyTables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = {"measured": [], "estimates": []}
        self.table = None
        self.row = None
        self.cell = None
        self.hrefs = []
        self.estimate_decoration = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table":
            self.table = attrs.get("id")
        if tag == "a" and "href" in attrs:
            self.hrefs.append(attrs["href"])
        if self.table not in self.tables:
            return
        if self.table == "estimates" and any(
            re.search(r"band|rank|class|style|color", key, re.I) for key in attrs
        ):
            self.estimate_decoration.append((tag, attrs))
        if tag == "tr":
            self.row = []
        if tag in {"th", "td"}:
            self.cell = ""

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag):
        if self.table in self.tables:
            if tag in {"th", "td"}:
                self.row.append(self.cell.strip())
                self.cell = None
            if tag == "tr":
                self.tables[self.table].append(self.row)
                self.row = None
        if tag == "table":
            self.table = None


def main():
    html = OUTPUT.read_bytes()
    fresh = render().encode("utf-8")
    if html != fresh or fresh != render().encode("utf-8"):
        raise SystemExit("Frequency output differs from a fresh deterministic render")

    entries = json.loads(PILOT.read_text(encoding="utf-8"))["frequency"]
    shares = [entry for entry in entries["entries"] if entry["kind"] == "share"]
    estimates = [entry for entry in entries["entries"] if entry["kind"] == "estimate"]
    bands = {band["id"]: band["label"] for band in entries["bands"]}
    parsed = FrequencyTables()
    parsed.feed(html.decode("utf-8"))
    measured_rows = parsed.tables["measured"]
    estimate_rows = parsed.tables["estimates"]

    if len(shares) != 5 or len(measured_rows) != len(shares) + 1:
        raise SystemExit("Expected five visible measured rows")
    if estimate_rows[0] != ["Метка", "Подтип или группа", "Оценка"]:
        raise SystemExit("Estimate table has an unexpected column")
    if parsed.estimate_decoration or len(estimate_rows) != len(estimates) + 1:
        raise SystemExit("Estimate rows are missing or carry formatting for bands or ranks")

    wheel_text = (OUTPUT.parents[1] / "index.html").read_text(encoding="utf-8")
    wheel_start = wheel_text.index("const META = ") + len("const META = ")
    wheel_meta, _ = json.JSONDecoder().raw_decode(wheel_text[wheel_start:])
    wheel_banded = {key for key, value in wheel_meta.items() if value.get("band") not in {None, "none"}}
    if wheel_banded != {entry["target"] for entry in shares}:
        raise SystemExit("Wheel and guide cover different measured targets")

    for row, entry in zip(measured_rows[1:], shares):
        tag, label, count, share, band = row
        expected_share = str(entry["pct"]).replace(".", ",") + " %"
        expected_count = f'{entry["count"]:,}'.replace(",", "\u202f")
        if (tag, label, count, share, band) != (
            entry["tag"], entry["label"], expected_count, expected_share, bands[entry["band"]]
        ):
            raise SystemExit(f"Visible measured row differs from pilot data: {entry['tag']}")
        card = wheel_meta[entry["target"]]
        card_text = unescape(card["freq"])
        wheel_pct = f'<b>{entry["pct"]:.2f}%</b>'
        wheel_count = expected_count.replace("\u202f", "\u2009")
        if card["band"] != entry["band"] or wheel_pct not in card_text or f'({tag}, {wheel_count} ' not in card_text:
            raise SystemExit(f"Wheel values differ from the guide: {entry['tag']}")

    for row, entry in zip(estimate_rows[1:], estimates):
        suffix = " · вся группа" if entry["scope"] == "group" else ""
        if row != [entry["tag"], entry["label"] + suffix, entry["value_text"]]:
            raise SystemExit(f"Visible estimate differs from pilot data: {entry['tag']}")
        card = wheel_meta[entry["target"]]
        if entry["value_text"] not in card["est"] or card.get("band", "none") != "none":
            raise SystemExit(f"Wheel estimate differs from the guide: {entry['tag']}")
        if "Корпусный ранг:" in card["freq"]:
            raise SystemExit(f"Wheel estimate carries a rank: {entry['tag']}")

    for entry in shares + estimates:
        if f'../#k={entry["target"]}' not in parsed.hrefs:
            raise SystemExit(f'Missing wheel resolver link: {entry["target"]}')

    print(f"Frequency check PASS: {len(shares)} measured shares, {len(estimates)} unbanded estimates, wheel and build parity")


if __name__ == "__main__":
    main()
