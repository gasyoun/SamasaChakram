#!/usr/bin/env python3
"""samasa_subtype_jev_choice_probe.py — H5278 Choice probe over the
samāsa-cakra leaf subtypes (samasacakra-taxonomy.json) on the gold gallery
klammerdiagramm compounds.

Per compound: state = compound + member glosses + context (vigraha/source/
translation — deliberately LEAK-FREE: no structural terms like "dvandva",
"tatpuruṣa", "bahuvrīhi" appear in the state). One `choice` question over ALL
58 taxonomy leaf subtypes (58 ≤ 255 live limit). Answer scored against the
curator gold = the taxonomy leaf whose `diagram` field embeds that compound's
example SVG. Output: results JSON (per-compound prediction + confidence +
cost) for the dated report generator.

Transport: reuses Uprava/tools/jev_probe.py (H5275) — TypeSafe Jev «System
One» API. Sibling-clone dependency is intentional (prior-art reuse, no
rebuild). Dry-run by default; --run goes live (retry ×3 with backoff).

Usage:
  python3 samasa_subtype_jev_choice_probe.py --taxonomy ../samasacakra/samasacakra-taxonomy.json --dry-run
  python3 samasa_subtype_jev_choice_probe.py --taxonomy ../samasacakra/samasacakra-taxonomy.json --run --out results.json
  python3 samasa_subtype_jev_choice_probe.py --run --limit 1        # smoke
Stdlib only; Python >= 3.9.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
DEFAULT_UPRAVA_TOOLS = HERE.parent.parent / "Uprava" / "tools"

QUESTION_ID = "samasa_subtype"

# ---------------------------------------------------------------------------
# Gold gallery: compound stem -> curator gold leaf id.
# Gold = the taxonomy leaf whose `diagram` field embeds this compound's
# example SVG (curator wiring, samasacakra-taxonomy.json).
# uddama: leaf sasthyartha points at klammerdiagramm-uddama-example.svg — the
# canonical Leitan render (MG vote D5, H997); the superseded plate-historical
# render is the same compound and is NOT a second item.
# yatpadambhojasevarucisucimanasam: no taxonomy leaf links it — not gold.
# ---------------------------------------------------------------------------
GOLD = {
    "sankhabherinadahastyasvaghosapurnanagaram": "sasthi",
    "sitosnasukhaduhkhadah": "upapada",
    "sakapriyaparthivah": "madhyamapadalopin",
    "abhijnanasakuntalam": "madhyamapadalopin",
    "rajadanta": "ekadesin",
    "vanantara": "mayura",
    "rajarsivamsah": "appositional",
    "sitosna": "ubhayapada",
    "sankhacakragadapanicaranakamalaseva": "upamita",
    "yathavidhigandhapuspanilakanthapadapadmapujaphalam": "rupaka",
    "pancagavadhana": "uttarapade",
    "tribhuvana": "samahare-dvigu",
    "cakrapanicaranakamalasevaphalam": "loc-bv",
    "janmarogamaranadi": "adi",
    "hastyasvarathaghosah": "itaretara",
    "panipadamukha": "samahara-dv",
    "yathasaktidattannapanadanapunyaphalabhagi": "yatha",
    "uddama-leitan": "sasthyartha",
}

# ---------------------------------------------------------------------------
# Leak-free probe states: glosses are plain lexical glosses; context carries
# source + overall translation + (where tradition gives one) the vigraha.
# NO structural terms (class/subtype names) anywhere in these strings.
# ---------------------------------------------------------------------------
STATES: Dict[str, Dict[str, Any]] = {
    "sankhabherinadahastyasvaghosapurnanagaram": {
        "members": [
            ("śaṅkha", "conch-shell"), ("bherī", "kettledrum"),
            ("nāda", "sound, roar"), ("hasti", "elephant"),
            ("aśva", "horse"), ("ghoṣa", "din, clamour"),
            ("pūrṇa", "filled"), ("nagaram", "city (n. sg.)"),
        ],
        "translation": "«the city filled with the sound of conches and "
                       "kettledrums and the din of elephants and horses»",
        "context": "Epic-style scene epithet; accusative neuter singular.",
    },
    "sitosnasukhaduhkhadah": {
        "members": [
            ("śīta", "cold"), ("uṣṇa", "heat"), ("sukha", "pleasure"),
            ("duḥkha", "pain"), ("dāḥ", "giving, producing"),
        ],
        "translation": "«giving cold-and-heat, pleasure-and-pain»",
        "context": "Bhagavadgītā 2.14 — mātrā-sparśās tu kaunteya "
                   "śītoṣṇa-sukha-duḥkha-dāḥ.",
    },
    "sakapriyaparthivah": {
        "members": [
            ("śāka", "vegetable, pot-herb"), ("priya", "fond of (elided "
            "middle member, restored by the vigraha)"),
            ("pārthivaḥ", "king, sovereign"),
        ],
        "translation": "«the king fond of vegetables»",
        "context": "Leitan's textbook example; surface word śākapārthivaḥ; "
                   "traditional vigraha: śākapriyaḥ pārthivaḥ.",
    },
    "abhijnanasakuntalam": {
        "members": [
            ("abhijñāna", "recognition, token"), ("śākuntalam", "Śakuntalā "
            "(fem. name, acc./nom.)"),
        ],
        "translation": "«Śakuntalā [recognised] by the token» — Kālidāsa's "
                       "drama title",
        "context": "Kālidāsa's title compound; gallery vigraha reads the "
                   "first member as the coordinated pair abhijñānam ca "
                   "śākuntalā ca.",
    },
    "rajadanta": {
        "members": [
            ("rāja", "king, royal"), ("danta", "tooth, tusk"),
        ],
        "translation": "«royal tusk» — a word for the elephant",
        "context": "Lexicalised zoonym; one member names only a part of the "
                   "animal, the whole word names the animal.",
    },
    "vanantara": {
        "members": [
            ("vana", "forest"), ("antara", "interior; other, different"),
        ],
        "translation": "«another forest; the interior of the forest»",
        "context": "Common epic adverb-forming pattern (vanam antara / "
                   "vanāntaraḥ).",
    },
    "rajarsivamsah": {
        "members": [
            ("rāja", "king, royal"), ("ṛṣi", "seer, sage"),
            ("vaṃśaḥ", "lineage, dynasty"),
        ],
        "translation": "«the lineage of royal sages» (rājarṣi = king-sage)",
        "context": "Left-nested example; the fused first pair rājarṣi is "
                   "attested.",
    },
    "sitosna": {
        "members": [
            ("śīta", "cold"), ("uṣṇa", "hot, heat"),
        ],
        "translation": "«cold and heat»",
        "context": "Two opposite qualities of the same kind combined into "
                   "one noun.",
    },
    "sankhacakragadapanicaranakamalaseva": {
        "members": [
            ("śaṅkha", "conch"), ("cakra", "discus"), ("gadā", "mace"),
            ("pāṇi", "hand"), ("caraṇa", "foot"), ("kamala", "lotus"),
            ("sevā", "service"),
        ],
        "translation": "«service to the lotus-feet of the Conch-Discus-"
                       "Mace-Handed (Viṣṇu)»",
        "context": "Bhakti-idiom chain on the attested Viṣṇu epithet "
                   "śaṅkhacakragadāpāṇiḥ; caraṇa-kamala = the foot as it "
                   "were a lotus.",
    },
    "yathavidhigandhapuspanilakanthapadapadmapujaphalam": {
        "members": [
            ("yathā", "according to, as"), ("vidhi", "rule, prescription"),
            ("gandha", "incense, fragrance"), ("puṣpa", "flower"),
            ("nīla", "blue"), ("kaṇṭha", "throat"),
            ("pāda", "foot"), ("padma", "lotus"), ("pūjā", "worship"),
            ("phalam", "fruit (n. sg.)"),
        ],
        "translation": "«the fruit of the worship, performed according to "
                       "rule with incense-and-flowers, of the lotus-feet of "
                       "the Blue-Throated (Śiva)»",
        "context": "Ritual dedication formula; ten members.",
    },
    "pancagavadhana": {
        "members": [
            ("pañca", "five"), ("gava", "cow (old form)"),
            ("dhana", "wealth, treasure"),
        ],
        "translation": "«wealth consisting of five cows»",
        "context": "Numeral-first quantity word of a measurement/accounting "
                   "type.",
    },
    "tribhuvana": {
        "members": [
            ("tri", "three"), ("bhuvana", "world, world-realm"),
        ],
        "translation": "«the three worlds (heaven, air, earth)»",
        "context": "Set cosmological term; the members name one ordered "
                   "group, not a split pair.",
    },
    "cakrapanicaranakamalasevaphalam": {
        "members": [
            ("cakra", "discus"), ("pāṇi", "hand"), ("caraṇa", "foot"),
            ("kamala", "lotus"), ("sevā", "service"),
            ("phalam", "fruit (n. sg.)"),
        ],
        "translation": "«the fruit of service to the lotus-feet of the "
                       "Discus-Handed (Viṣṇu)»",
        "context": "Bhakti-idiom chain; cakra-pāṇi describes a person by "
                   "what he holds («whose hand is the discus»).",
    },
    "janmarogamaranadi": {
        "members": [
            ("janma", "birth"), ("roga", "disease"),
            ("maraṇa", "death"), ("ādi", "beginning with, and so on"),
        ],
        "translation": "«birth, disease, death and the rest»",
        "context": "Enumeration closed by a 'and-so-on' final member.",
    },
    "hastyasvarathaghosah": {
        "members": [
            ("hasti", "elephant"), ("aśva", "horse"), ("ratha", "chariot"),
            ("ghoṣaḥ", "din, clamour (m. sg.)"),
        ],
        "translation": "«the din of elephants, horses and chariots»",
        "context": "Three co-equal items of an army scene, then their "
                   "noise.",
    },
    "panipadamukha": {
        "members": [
            ("pāṇi", "hand"), ("pāda", "foot"), ("mukha", "face, mouth"),
        ],
        "translation": "«hands, feet and faces» — the company as a mass of "
                       "limbs",
        "context": "Body-part list naming many people's parts together.",
    },
    "yathasaktidattannapanadanapunyaphalabhagi": {
        "members": [
            ("yathā", "according to, as"), ("śakti", "ability, power"),
            ("datta", "given"), ("anna", "food"), ("pāna", "drink"),
            ("dāna", "gift"), ("puṇya", "merit"), ("phala", "fruit, result"),
            ("bhāgī", "sharer, partaker"),
        ],
        "translation": "«sharing in the merit-fruit of the gift of food and "
                       "drink given according to one's ability»",
        "context": "Donation-formula word; nine members.",
    },
    "uddama-leitan": {
        "members": [
            ("uddāma", "boundless, vast"), ("ajñāna", "ignorance"),
            ("rūpa", "form"), ("prabalatama", "mightiest"),
            ("tamaḥ", "darkness"), ("stoma", "mass; raising"),
            ("soma", "moon"), ("svabhāvā", "own nature (fem.)"),
        ],
        "translation": "«whose form is boundless ignorance — whose nature "
                       "[is] the moon [raising] the mass of the mightiest "
                       "darkness»",
        "context": "Leitan's textbook example; eight members; ultimate head "
                   "svabhāvā; canonical reading per MG vote D5 (H997).",
    },
}

QUESTION_TEXT = (
    "Which single subtype from the given samāsa (Sanskrit compound) "
    "taxonomy best classifies THIS compound as a WHOLE — its top-level "
    "classification? Answer with exactly one option id."
)


# ---------------------------------------------------------------------------

def load_jev_module(uprava_tools: Path):
    """Import the H5275 client from the sibling Uprava clone."""
    path = uprava_tools / "jev_probe.py"
    if not path.exists():
        sys.exit(f"jev_probe.py not found at {path} — clone gasyoun/Uprava "
                 "beside this repo or pass --uprava-tools")
    spec = importlib.util.spec_from_file_location("jev_probe", path)
    if spec is None or spec.loader is None:
        sys.exit(f"cannot import jev_probe from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_leaves(taxonomy_path: Path) -> List[Dict[str, Any]]:
    """Flat list of the 58 leaf subtypes with class/family provenance."""
    tax = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    leaves: List[Dict[str, Any]] = []
    for cls in tax["classes"]:
        for fam in cls.get("families", []):
            for lf in fam.get("leaves", []):
                leaves.append({
                    "id": lf["id"],
                    "term": lf.get("term", lf["id"]),
                    "class": cls["name"],
                    "class_id": cls["id"],
                    "family": fam["name"],
                    "ex": lf.get("ex", ""),
                    "vigraha": lf.get("vigraha", ""),
                    "ru": lf.get("ru", ""),
                })
    ids = [l["id"] for l in leaves]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        sys.exit(f"leaf ids not unique: {sorted(dupes)} — prefix before use")
    return leaves


def build_criteria(leaves: List[Dict[str, Any]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for l in leaves:
        bits = [f"{l['class']} / {l['family']}: {l['term']}"]
        if l["ru"]:
            bits.append(l["ru"])
        if l["ex"]:
            ex = f"ex. {l['ex']}"
            if l["vigraha"]:
                ex += f" = {l['vigraha']}"
            bits.append(ex)
        out[l["id"]] = " — ".join(bits)
    return out


def build_state(stem: str) -> str:
    s = STATES[stem]
    words = ", ".join(f"{w} «{g}»" for w, g in s["members"])
    lines = [
        f"Compound: {stem} (segmented members, left to right)",
        f"Members and glosses: {words}",
        f"Overall meaning: {s['translation']}",
        f"Context: {s['context']}",
    ]
    return "\n".join(lines)


def call_with_retry(jev, req: Dict[str, Any], api_key: str, endpoint: str,
                    attempts: int = 3, backoff_s: float = 5.0):
    """Live call with ×3 retry + linear backoff on transport/5xx."""
    last = (0, {"error": "no attempt"})
    for i in range(1, attempts + 1):
        status, body = jev.call_jev(req, api_key, endpoint,
                                    timeout_s=jev.REQUEST_TIMEOUT_S)
        if status == 200 and isinstance(body.get("answers"), dict):
            return status, body
        last = (status, body)
        if i < attempts:
            print(f"  attempt {i} failed (status={status}), "
                  f"retrying in {backoff_s * i:.0f}s …", file=sys.stderr)
            time.sleep(backoff_s * i)
    return last


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--taxonomy", type=Path, required=True)
    ap.add_argument("--uprava-tools", type=Path, default=DEFAULT_UPRAVA_TOOLS)
    ap.add_argument("--out", type=Path, default=None,
                    help="results JSON path (--run)")
    ap.add_argument("--limit", type=int, default=0,
                    help="only first N gold compounds (smoke)")
    ap.add_argument("--run", action="store_true",
                    help="LIVE: call the API (default is dry-run)")
    ap.add_argument("--env-file", type=Path, default=None)
    args = ap.parse_args()

    jev = load_jev_module(args.uprava_tools)
    leaves = load_leaves(args.taxonomy)
    criteria = build_criteria(leaves)
    stems = [s for s in GOLD if s in STATES]
    missing = sorted(set(GOLD) - set(STATES))
    if missing:
        sys.exit(f"state missing for gold compounds: {missing}")
    if args.limit:
        stems = stems[: args.limit]

    results: List[Dict[str, Any]] = []
    for n, stem in enumerate(stems, 1):
        state = build_state(stem)
        req = {
            "state": state,
            "model": jev.DEFAULT_MODEL,
            "questions": {QUESTION_ID: {
                "type": "choice",
                "question": QUESTION_TEXT,
                "criteria": criteria,
            }},
        }
        ok, why = jev.validate_request(req)
        if not ok:
            sys.exit(f"validation failed for {stem}: {why}")
        if not args.run:
            blob = json.dumps(req, ensure_ascii=False)
            print(f"[dry-run {n}/{len(stems)}] {stem}: valid request, "
                  f"{len(blob)} chars, gold={GOLD[stem]}")
            results.append({"stem": stem, "gold": GOLD[stem],
                            "dry_run": True, "request_chars": len(blob)})
            continue

        env_file = args.env_file if args.env_file else jev.DEFAULT_ENV_FILE
        api_key, model, endpoint = jev.resolve_config(
            type("A", (), {"env_file": str(env_file)})())
        if not api_key:
            sys.exit(f"TYPESAFE_API_KEY not found in {env_file}")
        req["model"] = model
        status, body = call_with_retry(jev, req, api_key, endpoint)
        cls = jev.classify_result(status, body)
        if cls != "OK":
            body_s = json.dumps(body, ensure_ascii=False)[:300]
            print(f"[{n}/{len(stems)}] {stem}: {cls} — {body_s}",
                  file=sys.stderr)
            results.append({"stem": stem, "gold": GOLD[stem], "status": cls})
            continue
        ans = body["answers"][QUESTION_ID]
        cost = jev.cost_usd(body.get("usage"))
        results.append({
            "stem": stem,
            "gold": GOLD[stem],
            "predicted": ans.get("choice"),
            "confidence": ans.get("confidence"),
            "probabilities": ans.get("probabilities", {}),
            "usage": body.get("usage", {}),
            "cost_usd": cost,
            "model": body.get("model", model),
        })
        cost_s = f" cost=${cost:.6f}" if cost is not None else ""
        choice = ans.get("choice")
        conf = ans.get("confidence")
        print(f"[{n}/{len(stems)}] {stem}: predicted={choice!r} "
              f"gold={GOLD[stem]!r} conf={conf}{cost_s}")

    if args.out:
        args.out.write_text(json.dumps({
            "probe": "H5278 samasa-subtype choice",
            "model": results[0].get("model") if results else None,
            "n_options": len(criteria),
            "items": results,
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
