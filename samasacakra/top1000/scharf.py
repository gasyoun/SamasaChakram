import csv
import re
from pathlib import Path

LABELS = [
    (re.compile(r"ṣaṣṭhī|tatpuruṣa|upapada|nañ|gati|prādi", re.I), "tatpurusa"),
    (re.compile(r"karmadhāraya|dvigu", re.I), "karmadharaya"),
    (re.compile(r"dvandva", re.I), "dvandva"),
    (re.compile(r"bahuvrīhi", re.I), "bahuvrihi"),
]


def coarse_of(fine: str) -> str:
    for pattern, coarse in LABELS:
        if pattern.search(fine):
            return coarse
    return "unknown"


def extract_scharf(text: str) -> list:
    out = []
    for line in text.splitlines():
        if "—" not in line:
            continue
        compound, label = (p.strip() for p in line.split("—", 1))
        if not compound or " " in compound:
            continue
        ambiguous = "ambiguous" in label.lower() or "/" in label
        coarse = "unknown" if ambiguous else coarse_of(label)
        out.append({"compound": compound, "fine": label, "coarse": coarse,
                    "ambiguous": ambiguous})
    return out


def load_scharf(path: Path) -> list:
    with Path(path).open(encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh, delimiter="\t") if r["ambiguous"] != "True"]


if __name__ == "__main__":
    import argparse
    from pypdf import PdfReader
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", default=str(Path(__file__).with_name("data") / "scharf_gold.tsv"))
    args = ap.parse_args()
    text = "\n".join(p.extract_text() or "" for p in PdfReader(args.pdf).pages)
    rows = extract_scharf(text)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("compound\tfine\tcoarse\tambiguous\n")
        for r in rows:
            fh.write(f'{r["compound"]}\t{r["fine"]}\t{r["coarse"]}\t{r["ambiguous"]}\n')
    print("wrote", out, len(rows), "rows")
