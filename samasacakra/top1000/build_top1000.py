from pathlib import Path


def rank_compounds(cmps: Path, names: Path, cap: int = 1000) -> list:
    freq = {}
    with Path(names).open(encoding="utf-8") as fh:
        for line in fh:
            p = line.rstrip("\n").split(";")
            if len(p) < 4:
                continue
            try:
                freq[p[0].strip()] = int(p[3])
            except ValueError:
                continue
    ranked = []
    with Path(cmps).open(encoding="utf-8") as fh:
        for line in fh:
            p = line.rstrip("\n").split(";", 1)
            if len(p) < 2:
                continue
            surface, members = p[0].strip(), p[1].split()
            if surface in freq and freq[surface] > 0 and len(members) >= 2:
                ranked.append({"compound": surface, "members": members, "freq": freq[surface]})
    ranked.sort(key=lambda r: (-r["freq"], r["compound"]))
    return [dict(rank=i + 1, **r) for i, r in enumerate(ranked[:cap])]


# H1398 (kosha/data/samasa/drill_weights.json): corpus heads are polluted by
# particles, pronoun stems, bare roots and taddhita suffixes. Ranked surfaces
# must pass this filter or the "top-1000" is a list of function words.
STOP = {"ca", "eva", "vā", "tu", "hi", "api", "iva", "idam", "tad", "etad",
        "yad", "kim", "adas", "sva", "kṛ", "as", "bhū", "gam", "i", "dā",
        "dhā", "sthā", "han", "nī", "pā", "yā", "tva", "tā"}


def rank_from_wordfreq(cmps, freq_path, cap=1000, extra_stop=()):
    """Rank cmps.csv surfaces by DCS token frequency (SLP1 word-frequency file).

    `names.csv` is not published in VisualDCS, so the surface frequency comes
    from csl-apidev/simple-search/wf0/word_frequency_norm.txt (SLP1). Surfaces
    are transliterated IAST -> SLP1 before lookup.
    """
    from indic_transliteration import sanscript
    freq = {}
    with Path(freq_path).open(encoding="utf-8-sig") as fh:
        for line in fh:
            p = line.split()
            if len(p) >= 2:
                try:
                    freq[p[0]] = int(p[1])
                except ValueError:
                    continue
    ranked = []
    with Path(cmps).open(encoding="utf-8") as fh:
        for line in fh:
            p = line.rstrip("\n").split(";", 1)
            if len(p) < 2:
                continue
            surface, members = p[0].strip(), p[1].split()
            stop = STOP | set(extra_stop)
            if len(surface) < 6 or len(members) < 2 or surface in stop:
                continue
            if sum(1 for m in members if len(m) >= 3 and m not in stop) < 2:
                continue
            key = sanscript.transliterate(surface, sanscript.IAST, sanscript.SLP1)
            if key in freq and freq[key] > 0:
                ranked.append({"compound": surface, "members": members, "freq": freq[key]})
    ranked.sort(key=lambda r: (-r["freq"], r["compound"]))
    return [dict(rank=i + 1, **r) for i, r in enumerate(ranked[:cap])]


def rank_from_lemma_proxy(cmps, lemma_tsv, cap=1000, extra_stop=()):
    """Fallback ranking: min DCS lemma frequency of the two members.

    Unlike rank_from_wordfreq this is NOT an attested compound frequency —
    it is a member-frequency proxy used only to fill the ranked list to 1000
    after the measured compound surfaces run out (351). The report says so.
    """
    from indic_transliteration import sanscript
    counts = {}
    with Path(lemma_tsv).open(encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 2:
                try:
                    counts[p[0]] = int(p[1])
                except ValueError:
                    continue
    stop = STOP | set(extra_stop)
    ranked = []
    seen = set()
    with Path(cmps).open(encoding="utf-8") as fh:
        for line in fh:
            p = line.rstrip("\n").split(";", 1)
            if len(p) < 2:
                continue
            surface, members = p[0].strip(), p[1].split()
            if (surface in seen or len(surface) < 6 or len(members) < 2 or surface in stop
                    or sum(1 for m in members if len(m) >= 3 and m not in stop) < 2):
                continue
            keys = [sanscript.transliterate(m, sanscript.IAST, sanscript.SLP1) for m in members]
            vals = [counts[k] for k in keys if k in counts]
            if len(vals) < 2:
                continue
            seen.add(surface)
            ranked.append({"compound": surface, "members": members, "freq": min(vals),
                           "basis": "lemma_proxy"})
    ranked.sort(key=lambda r: (-r["freq"], r["compound"]))
    return [dict(rank=i + 1, **r) for i, r in enumerate(ranked[:cap])]


def combine_rankings(measured, proxy, cap=1000):
    out, seen = [], set()
    for r in list(measured) + list(proxy):
        if r["compound"] in seen:
            continue
        seen.add(r["compound"])
        item = dict(r)
        item.setdefault("basis", "measured")
        out.append(item)
        if len(out) >= cap:
            break
    return [dict(r, rank=i + 1) for i, r in enumerate(out)]


def write_ranked(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("rank\tcompound\tmembers\tfreq\n")
        for r in rows:
            fh.write(f'{r["rank"]}\t{r["compound"]}\t{" ".join(r["members"])}\t{r["freq"]}\n')
    return path


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmps", required=True)
    ap.add_argument("--names", required=True)
    ap.add_argument("--out", default=str(Path(__file__).with_name("data") / "top1000_ranked.tsv"))
    ap.add_argument("--cap", type=int, default=1000)
    args = ap.parse_args()
    rows = rank_compounds(Path(args.cmps), Path(args.names), cap=args.cap)
    print("wrote", write_ranked(rows, args.out), len(rows), "rows")
