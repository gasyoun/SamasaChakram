#!/usr/bin/env python3
"""Build `samasacakra/top1000/data/base_productivity.tsv` — the base-productivity layer.

For every one of the 58 canonical taxonomy examples this script takes the example's
pūrvapada and uttarapada (from the example form, cross-checked against its vigraha) and
lists every *other* compound in which the same base occupies the same role.

Sources (both external, never copied into the repo — see reports/BASE_PRODUCTIVITY_*.md):

* ``cmps.csv`` — VisualDCS ``derived-data/Kompozity/cmps.csv`` (DCS, CC BY 4.0):
  401 478 pairs ``compound; member member …``.  Member columns are the *split* of the
  compound; the first member is the leftmost (pūrvapada) morpheme, the last member the
  rightmost (uttarapada).  The file carries **no frequency column**, only the pairs.
* ``compounds.txt`` — MWderivations ``compounds/compounds.txt`` (MW H3 parent-keyed view,
  12 609 lines ``n_children:parent:child …``).  This file is a **pūrvapada-keyed** view by
  construction: it enumerates the children of a parent headword.  Its leading field is
  ``n_children`` (the number of listed children — verified against the child list, 19/12 609
  lines disagree by one), **not** a corpus frequency.

Counts.  ``count`` is the productivity of the base in that role: the number of *distinct
compounds* attested for it in the union of both sources.  It is a compound-inventory count
(dictionary + corpus-attested pair inventory), never a corpus token frequency — ADR 0002
forbids reading a type label out of a frequency figure, and no frequency figure exists in
either source.

``type_label`` is filled only from an exact existing label: a join on
``samasacakra/top1000/data/top1000_typed.tsv`` (``type_fine``).  No rule-based or guessed
labels are written.

Usage:
    python samasacakra/top1000/build_base_productivity.py \
        --cmps  <path>/cmps.csv --compounds <path>/compounds.txt

Deterministic: two runs over the same inputs are byte-identical (no wall-clock values in
the artefacts; ``--date`` only stamps the manifest).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAXONOMY = ROOT / "samasacakra" / "samasacakra-taxonomy.json"
OUT_DIR = ROOT / "samasacakra" / "top1000" / "data"

COLUMNS = [
    "base",
    "base_variant",
    "role",
    "compound",
    "source",
    "count",
    "already_in_our_examples",
    "type_label",
    "examples",
]

# ---------------------------------------------------------------------------
# Normalisation — a documented subset of sanskrit-util `form_key()` (prior art:
# gasyoun/sanskrit-util py/sanskrit_util/__init__.py).  Kept local so the repo stays
# dependency-free in CI.  It folds anusvāra/homorganic nasals to `n`, strips a word-final
# visarga, and preserves vowel length (ā ≠ a) — the key is for *matching*, never for
# deduplicating lexemes in the published data (surface forms are always emitted).
# ---------------------------------------------------------------------------

_ANUSVARA_VARIANTS = ("\u1e41", "\u1e43", "\u0902")  # ṁ ṃ Devanagari anusvāra (source quirk)
_ACCENTS = {"\u0301", "\u0300", "\u0951", "\u0952"}


def fold(text: str) -> str:
    """Comparison key: length-preserving, nasal-folded, visarga-stripped."""
    s = (text or "").strip().lower()
    for variant in _ANUSVARA_VARIANTS:
        s = s.replace(variant, "\u1e43")  # ṃ
    s = s.replace("\u2019", "'").replace("\u02bc", "'")
    s = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", s)
    s = re.sub("\u1e25$", "", s)                       # final visarga
    s = re.sub("[\u1e43\u1e41]$", "m", s)              # word-final anusvāra is /m/
    s = re.sub("[\u1e43\u1e41](?=[pbm])", "m", s)      # medial anusvāra before a labial
    s = re.sub("[\u1e43\u1e41\u1e45\u00f1\u1e47]", "n", s)  # ṃ ṁ ṅ ñ ṇ -> n
    out = []
    for ch in unicodedata.normalize("NFD", s):
        if ch in _ACCENTS:
            j = len(out) - 1
            while j >= 0 and unicodedata.combining(out[j]):
                j -= 1
            base = unicodedata.normalize("NFC", "".join(out[j:])) if j >= 0 else ""
            if base in set("aāiīuū\u1e5b\u1e5d\u1e37\u1e39eēoō"):
                continue
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


def fold_compound(text: str) -> str:
    """fold() for a compound string: drops the sandhi marker '@' and joins the pieces."""
    return fold(text.replace("@", ""))


# ---------------------------------------------------------------------------
# Base derivation for the 58 canonical examples.
#
# `basis` records where the split comes from:
#   ex      — the morphology of the example compound itself
#   vigraha — the vigraha sentence supplies the two words
#   both    — the example and the vigraha agree
# `variants` lists *citation-form allomorphs* of the same base that the sources spell
# differently (nañ a-/an-, nir niś-/niṣ-, duṣ dur-/duḥ-, pañcan pañca, saha sa-, rājan rāja).
# They are matching expansions only; the emitted ``base`` column keeps the citation form and
# ``base_variant`` records the form that actually matched.
#
# Edit scope note: this table is data about the taxonomy, not the taxonomy itself.
# ---------------------------------------------------------------------------

DERIVATION = {
    "tatpurusa/vibhakti/prathama": ("pūrva", "kāya", "both"),
    "tatpurusa/vibhakti/dvitiya": ("grāma", "gata", "both"),
    "tatpurusa/vibhakti/trtiya": ("vāc", "kalaha", "ex"),
    "tatpurusa/vibhakti/caturthi": ("yūpa", "dāru", "both"),
    "tatpurusa/vibhakti/pancami": ("caura", "bhaya", "both"),
    "tatpurusa/vibhakti/sasthi": ("rājan", "putra", "both"),
    "tatpurusa/vibhakti/saptami": ("vana", "vāsa", "both"),
    "tatpurusa/tp-special/nan-tp": ("na", "brāhmaṇa", "both"),
    "tatpurusa/tp-special/pradi-tp": ("pra", "pitāmaha", "ex"),
    "tatpurusa/tp-special/gati": ("puras", "kāra", "ex"),
    "tatpurusa/tp-special/upapada": ("kumbha", "kāra", "ex"),
    "tatpurusa/tp-special/aluk": ("yudhi", "sthira", "ex"),
    "tatpurusa/tp-special/madhyamapadalopin": ("śāka", "pārthiva", "ex"),
    "tatpurusa/tp-special/mayura": ("vana", "antara", "ex"),
    "tatpurusa/karmadharaya/visesanapurvapada": ("kṛṣṇa", "sarpa", "both"),
    "tatpurusa/karmadharaya/appositional": ("rājan", "ṛṣi", "ex"),
    "tatpurusa/karmadharaya/visesyapurvapada": ("gopāla", "bāla", "ex"),
    "tatpurusa/karmadharaya/ubhayapada": ("śīta", "uṣṇa", "both"),
    "tatpurusa/karmadharaya/upamanapurvapada": ("megha", "śyāma", "both"),
    "tatpurusa/karmadharaya/upamita": ("puruṣa", "vyāghra", "both"),
    "tatpurusa/karmadharaya/rupaka": ("saṃsāra", "arṇava", "both"),
    "tatpurusa/karmadharaya/sambhavana": ("guṇa", "buddhi", "both"),
    "tatpurusa/dvigu/taddhitarthe": ("pañcan", "kapāla", "ex"),
    "tatpurusa/dvigu/uttarapade": ("pañcan", "dhana", "vigraha"),
    "tatpurusa/dvigu/samahare-dvigu": ("tri", "bhuvana", "both"),
    "bahuvrihi/samanadhikarana/dvitiyartha": ("prāpta", "udaka", "both"),
    "bahuvrihi/samanadhikarana/trtiyartha": ("ūḍha", "ratha", "both"),
    "bahuvrihi/samanadhikarana/caturthyartha": ("upahata", "paśu", "both"),
    "bahuvrihi/samanadhikarana/pancamyartha": ("uddhṛta", "odana", "both"),
    "bahuvrihi/samanadhikarana/sasthyartha": ("pīta", "ambara", "both"),
    "bahuvrihi/samanadhikarana/saptamyartha": ("vīra", "puruṣa", "both"),
    "bahuvrihi/vyadhikarana/loc-bv": ("cakra", "pāṇi", "both"),
    "bahuvrihi/vyadhikarana/gen-bv": ("candra", "kānti", "both"),
    "bahuvrihi/bv-special/nan-bv": ("na", "bhāryā", "both"),
    "bahuvrihi/bv-special/pradi-bv": ("pra", "añjali", "ex"),
    "bahuvrihi/bv-special/saha": ("saha", "putra", "both"),
    "bahuvrihi/bv-special/sankhya": ("dvi", "tri", "both"),
    "bahuvrihi/bv-special/dig": ("dakṣiṇa", "pūrva", "both"),
    "bahuvrihi/bv-special/adverbial": ("keśa", "keśa", "both"),
    "bahuvrihi/bv-special/ahitagni": ("āhita", "agni", "both"),
    "bahuvrihi/bv-special/vibhakti-bv": ("bhava", "janman", "ex"),
    "bahuvrihi/bv-special/kim": ("kim", "lakṣaṇa", "both"),
    "bahuvrihi/bv-special/adi": ("rāga", "ādi", "both"),
    "bahuvrihi/bv-special/para": ("dharma", "para", "both"),
    "bahuvrihi/bv-special/matra": ("deha", "mātra", "both"),
    "dvandva/dv/itaretara": ("rāma", "kṛṣṇa", "both"),
    "dvandva/dv/samahara-dv": ("pāṇi", "mukha", "ex"),
    "avyayibhava/av/vibhakti-av": ("adhi", "hari", "ex"),
    "avyayibhava/av/samipa": ("upa", "gaṅgā", "ex"),
    "avyayibhava/av/samrddhi": ("su", "magadha", "ex"),
    "avyayibhava/av/vyrddhi": ("dus", "yavana", "ex"),
    "avyayibhava/av/arthabhava": ("nir", "makṣikā", "ex"),
    "avyayibhava/av/atyaya": ("ati", "hima", "ex"),
    "avyayibhava/av/asamprati": ("ati", "nidrā", "ex"),
    "avyayibhava/av/sabda": ("iti", "hari", "ex"),
    "avyayibhava/av/pascat": ("anu", "ratha", "ex"),
    "avyayibhava/av/yatha": ("yathā", "śakti", "ex"),
    "avyayibhava/av/vipsa": ("prati", "grāma", "ex"),
}

VARIANTS = {
    "na": ["a", "an"],
    "nir": ["niś", "niṣ", "niḥ"],
    "dus": ["duṣ", "dur", "duḥ"],
    "pañcan": ["pañca"],
    "rājan": ["rāja"],
    "kim": ["kiṃ"],
}
# `saha` deliberately has no `sa` variant: in the pair inventory a first member `sa` is the
# demonstrative pronoun inside a sandhi-joined sequence, not the saha allomorph, and folding
# the two would inflate the saha count with pronoun noise (measured 5 893 -> 100 rows).


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_taxonomy() -> list[dict]:
    data = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    rows = []
    for cls in data["classes"]:
        for fam in cls.get("families", []):
            for leaf in fam.get("leaves", []):
                rows.append(
                    {
                        "key": f"{cls['id']}/{fam['id']}/{leaf['id']}",
                        "class": cls["id"],
                        "family": fam["id"],
                        "leaf": leaf["id"],
                        "term": leaf.get("term", ""),
                        "ex": leaf.get("ex", ""),
                        "vigraha": leaf.get("vigraha", ""),
                    }
                )
    return rows


def load_cmps(path: Path):
    """compound -> members plus role indexes over *every* line.

    Returns (compounds, first_index, last_index, pairs).  The indexes are built from all
    401 478 lines, not from the de-duplicated dict: 2 428 compound strings occur more than
    once with a different split, and dropping those would lose legitimate role evidence.
    `compounds` keeps one split per string and is used only for variant attribution.
    """
    pairs: list[tuple[str, list[str]]] = []
    compounds: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ";" not in line:
            continue
        compound, members = line.split(";", 1)
        parts = [p for p in (m.strip() for m in members.split()) if p]
        if not parts:
            continue
        compound = compound.strip()
        pairs.append((compound, parts))
        compounds[compound] = parts
    first_index: dict[str, list[str]] = {}
    last_index: dict[str, list[str]] = {}
    for compound, parts in pairs:
        first_index.setdefault(fold_compound(parts[0]), []).append(compound)
        last_index.setdefault(fold_compound(parts[-1]), []).append(compound)
    return compounds, first_index, last_index, pairs


def load_compounds_txt(path: Path):
    """parent -> (n_children, children).  Child tokens keep their surface form."""
    parents: dict[str, tuple[int, list[str]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        count, parent, children = line.split(":", 2)
        kids = [k.lstrip("+") for k in children.split() if k]
        kids = [k for k in kids if k]
        parents[fold(parent)] = (int(count), kids)
    return parents


def load_type_labels(path: Path | None) -> dict[str, str]:
    """Optional verified-tag table: TSV with `compound` and `type_fine` columns.

    Left empty by default: the only in-repo per-compound label table (`top1000_typed.tsv`)
    is rule-derived and carries no confidence/gold column, so echoing it would present a
    guessed type as an exact tag — forbidden by ADR 0002 and by this handoff's acceptance
    ("type_label empty without an exact tag").  Point `--labels` at a verified table
    (e.g. the Sangram H989 gold export) to fill the column.
    """
    labels: dict[str, str] = {}
    if path is None or not path.exists():
        return labels
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return labels
    header = lines[0].split("\t")
    try:
        i_compound = header.index("compound")
        i_label = header.index("type_fine")
    except ValueError:
        return labels
    for line in lines[1:]:
        fields = line.split("\t")
        if len(fields) <= max(i_compound, i_label):
            continue
        label = fields[i_label].strip()
        if label:
            labels.setdefault(fold_compound(fields[i_compound]), label)
    return labels


def example_key(ex: str) -> str:
    """Fold an example surface form for the `already_in_our_examples` test."""
    cleaned = ex.replace("[", "").replace("]", "").replace("*", "").replace("-", "")
    return fold_compound(cleaned)


def build(cmps_path: Path, compounds_path: Path, labels_path: Path | None = None):
    taxonomy = load_taxonomy()
    missing = [t["key"] for t in taxonomy if t["key"] not in DERIVATION]
    if missing:
        raise SystemExit(f"derivation table misses {len(missing)} leaves: {missing}")

    compounds, first_index, last_index, _pairs = load_cmps(cmps_path)
    parents = load_compounds_txt(compounds_path)
    labels = load_type_labels(labels_path)

    example_keys = {example_key(t["ex"]) for t in taxonomy}

    summary = []
    collected: dict[tuple[str, str, str], dict] = {}
    for item in taxonomy:
        purva, uttara, basis = DERIVATION[item["key"]]
        detail = {}
        for role, base in (("pūrvapada", purva), ("uttarapada", uttara)):
            variants = [base] + VARIANTS.get(base, [])
            cmps_hits: dict[str, str] = {}
            txt_hits: dict[str, str] = {}
            variant_hits: dict[str, int] = {}
            for variant in variants:
                key = fold(variant)
                hit = 0
                if role == "pūrvapada":
                    for compound in first_index.get(key, []):
                        cmps_hits.setdefault(fold_compound(compound), compound)
                        hit += 1
                    if key in parents:
                        _, kids = parents[key]
                        for kid in kids:
                            display = kid.replace("@", "")
                            txt_hits.setdefault(fold_compound(display), display)
                            hit += 1
                else:
                    for compound in last_index.get(key, []):
                        cmps_hits.setdefault(fold_compound(compound), compound)
                        hit += 1
                if hit:
                    variant_hits[variant] = hit
            union = set(cmps_hits) | set(txt_hits)
            count = len(union)
            for key in sorted(union):
                display = cmps_hits.get(key) or txt_hits[key]
                if key in cmps_hits and key in txt_hits:
                    source = "both"
                elif key in cmps_hits:
                    source = "cmps.csv"
                else:
                    source = "compounds.txt"
                variant = ""
                for cand in variants:
                    vkey = fold(cand)
                    if key in cmps_hits:
                        members = compounds.get(cmps_hits[key], [])
                        if members and fold_compound(
                            members[0] if role == "pūrvapada" else members[-1]
                        ) == vkey:
                            variant = cand if cand != base else ""
                            break
                    else:
                        if vkey in parents and any(
                            fold_compound(k.replace("@", "")) == key for k in parents[vkey][1]
                        ):
                            variant = cand if cand != base else ""
                            break
                row_key = (base, role, display)
                if row_key in collected:
                    collected[row_key]["examples"].add(item["key"])
                    continue
                collected[row_key] = {
                    "base": base,
                    "base_variant": variant,
                    "role": role,
                    "compound": display,
                    "source": source,
                    "count": count,
                    "already_in_our_examples": "да"
                    if fold_compound(display) in example_keys
                    else "нет",
                    "type_label": labels.get(fold_compound(display), ""),
                    "examples": {item["key"]},
                }
            detail[role] = {
                "base": base,
                "count": count,
                "count_cmps": len(cmps_hits),
                "count_compounds_txt": len(txt_hits),
                "variants": variant_hits,
            }
        summary.append(
            {
                "key": item["key"],
                "class": item["class"],
                "family": item["family"],
                "leaf": item["leaf"],
                "term": item["term"],
                "ex": item["ex"],
                "vigraha": item["vigraha"],
                "basis": basis,
                "purvapada": detail["pūrvapada"],
                "uttarapada": detail["uttarapada"],
            }
        )

    rows = []
    for row in collected.values():
        row["examples"] = ";".join(sorted(row["examples"]))
        rows.append(row)
    rows.sort(key=lambda r: (-r["count"], r["base"], r["role"], r["compound"]))
    return summary, rows


def write_tsv(path: Path, columns, rows) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(columns) + "\n")
        for row in rows:
            fh.write("\t".join(str(row[c]) for c in columns) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cmps", required=True, type=Path)
    parser.add_argument("--compounds", required=True, type=Path)
    parser.add_argument("--labels", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--date", default="26-11-2026")
    args = parser.parse_args()

    summary, rows = build(args.cmps, args.compounds, args.labels)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    write_tsv(args.out_dir / "base_productivity.tsv", COLUMNS, rows)

    summary_rows = []
    for item in summary:
        summary_rows.append(
            {
                "key": item["key"],
                "class": item["class"],
                "family": item["family"],
                "leaf": item["leaf"],
                "ex": item["ex"],
                "vigraha": item["vigraha"],
                "purvapada": item["purvapada"]["base"],
                "purvapada_count": item["purvapada"]["count"],
                "purvapada_cmps": item["purvapada"]["count_cmps"],
                "purvapada_compounds_txt": item["purvapada"]["count_compounds_txt"],
                "uttarapada": item["uttarapada"]["base"],
                "uttarapada_count": item["uttarapada"]["count"],
                "uttarapada_cmps": item["uttarapada"]["count_cmps"],
                "uttarapada_compounds_txt": item["uttarapada"]["count_compounds_txt"],
                "basis": item["basis"],
            }
        )
    write_tsv(
        args.out_dir / "base_productivity_examples.tsv",
        list(summary_rows[0].keys()),
        summary_rows,
    )

    manifest = {
        "date": args.date,
        "script": "samasacakra/top1000/build_base_productivity.py",
        "inputs": {
            "cmps.csv": {"sha256": sha256(args.cmps), "path": "VisualDCS derived-data/Kompozity/cmps.csv"},
            "compounds.txt": {
                "sha256": sha256(args.compounds),
                "path": "MWderivations compounds/compounds.txt",
            },
        },
        "rows": len(rows),
        "examples": len(summary),
        "bases": len({r["base"] for r in rows}),
        "counts": {
            "pūrvapada": sum(1 for r in rows if r["role"] == "pūrvapada"),
            "uttarapada": sum(1 for r in rows if r["role"] == "uttarapada"),
            "source_cmps.csv": sum(1 for r in rows if r["source"] in ("cmps.csv", "both")),
            "source_compounds.txt": sum(
                1 for r in rows if r["source"] in ("compounds.txt", "both")
            ),
            "labelled": sum(1 for r in rows if r["type_label"]),
            "already_in_our_examples": sum(1 for r in rows if r["already_in_our_examples"] == "да"),
        },
        "license": {
            "cmps.csv": "CC BY 4.0 (Digital Corpus of Sanskrit, Oliver Hellwig)",
            "compounds.txt": "MWderivations derived table from Monier-Williams (public domain)",
            "this_tsv": "derived view; attribute DCS CC BY 4.0",
        },
    }
    (args.out_dir / "base_productivity_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: manifest[k] for k in ("rows", "examples", "bases", "counts")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
