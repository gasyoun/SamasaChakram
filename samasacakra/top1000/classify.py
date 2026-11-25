def classify(surface, members, answers, rules):
    nodes, results = rules["nodes"], rules["results"]
    cur, path, unanswered = "start", [], []
    seen = set()
    while cur in nodes and cur not in seen:
        seen.add(cur)
        node = nodes[cur]
        path.append(cur)
        options = node.get("options") or []
        if options:
            if cur not in answers:
                unanswered.append(cur)
                break
            choice = answers[cur]
            nxt = next((o["next"] for o in options
                        if choice == o["next"] or choice == o["label"]), None)
            if nxt is None:
                unanswered.append(cur)
                break
            cur = nxt
            continue
        if node["kind"] == "form":
            form = "start"
            if cur.startswith("ask_tp_numeral"):
                form = "numeral"
            elif cur.startswith("ask_tp_prefix"):
                form = "prefix"
            if form == "start":
                ans = any(m in rules.get("avyaya_words", []) for m in members)
            elif form == "numeral":
                ans = members[0] in rules.get("numerals", ["eka", "dvi", "tri", "catur"])
            else:
                ans = members[0] in rules.get("preverbs", [])
        else:
            if cur not in answers:
                unanswered.append(cur)
                break
            ans = bool(answers[cur])
        cur = node["yes"] if ans else node["no"]
    terminal = results.get(cur, {})
    return {"type": terminal.get("type", "unknown"), "fine": terminal.get("fine", ""),
            "path": path, "unanswered": unanswered}
