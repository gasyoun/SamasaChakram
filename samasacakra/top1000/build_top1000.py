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
