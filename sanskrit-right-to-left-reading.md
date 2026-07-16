_Created: 12-07-2026 · Last updated: 15-07-2026_

# Reading a Sanskrit sentence right-to-left — the case-question method

The canonical procedure shared by [`/sanskrit-parse`](https://github.com/gasyoun/claude-config/blob/main/commands/sanskrit-parse.md) (which
applies it to a sentence for comprehension), [`/klammeruebersetzung`](https://github.com/gasyoun/claude-config/blob/main/commands/klammeruebersetzung.md)
(which applies it and additionally weaves the bracket translation), and
[`/klammerdiagramm`](https://github.com/gasyoun/claude-config/blob/main/commands/klammerdiagramm.md) (which draws it as the publication-grade
SVG plate). Kept in one place so the skills cannot drift apart.

**Core claim.** A Sanskrit sentence is not read left-to-right. Its syntactic head — a Nom.
noun or a finite verb — comes **last**, and every other word hangs off it as an answer to a
grammatical question. So you find the head first and glue elements on **leftwards**, each new
word answering a specific **case-question**. *If you cannot phrase the question a word answers,
you have not yet found what it attaches to* — that is the diagnostic that you are not done.

## The algorithm

**Step 0 — Find the anchor (ядро).** Look for the Nom. noun or the finite/absolute verb form.
That is the centre of the whole construction. → *what?* (что?)

**Step 1 — Nearest agreeing modifier.** Moving left: a participle, adjective, or numeral that
agrees with the anchor. → *which? / what kind?* (какая / какой / какое?)

**Step 2 — Adverbials of the action (gerund / absolutive).** A form in `-tvā` / `-ya` /
`-(t)ya` (e.g. `adhikṛtya`, `kṛtvā`, `gatvā`). → *how? by what means? under what condition?*
(как? каким образом?)

**Step 3 — The object of that action.** Ask the gerund/verb for its complement. → *whom? what?*
(кого? что?) — watch the number (dual `te`, etc.).

**Step 4 — Unpack that object.** A clarifying form (often Nom./Acc. dual, sometimes a proper
name) specifying who the object is. → *which ones exactly?* (каких именно?)

**Step 5 — Resolve a name marked by `iti`.** If `iti` (often hidden in sandhi, `cety = ca +
iti`) quotes a preceding name, unfold it. → *what does that name mean?* (что это значит?)

Continue leftwards, reusing Steps 1–5 as the grammar demands, until every word has answered a
question and none is left dangling.

## The universal question schema

```
1. Что?              — the anchor (Nom. noun / finite verb)
2. Какая/какой/какое? — agreeing modifier (participle / adj. / numeral)
3. Как? каким образом? — gerund / adverbial
4. Кого? что?         — object of the action
5. Кто/что именно?    — clarification of the object
6. Что это значит?    — name resolution (if iti)
```

Universal shape (glue leftwards under the anchor):

```
[anchor]
 ← какое?
   ← как?
     ← кого / что?
       ← каких именно?
         ← что это значит?
```

## Discipline (the load-bearing rules)

- **Split sandhi before you count steps** — a swallowed `cety = ca + iti` or `sadhikṛtya = sa +
  adhikṛtya` hides a whole rung.
- **Let morphology settle the case where it can.** A gerund like `adhikṛtya` governs the
  **accusative**; a dual in `-e` (`te`, `abhijñānaśākuntale`) is Nom./Acc., not locative (the
  locative dual would be `tayoḥ` / `…layoḥ`). Read the *sense* the gerund delivers ("concerning
  these two") but label the *case* correctly (Acc. dual). Only park a word as genuinely
  ambiguous when its form truly allows more than one parse.
- **No question, not done.** If a word answers no question yet, its attachment is still unknown —
  keep going; do not translate it in isolation.

## Worked mini-example — `abhijñānaśākuntalam`

`abhijñānaṃ ca śākuntalā cety abhijñānaśākuntale te sadhikṛtya kṛtaṃ nāṭakam`

```
что?              → nāṭakam (драма)
какая?            → kṛtam (созданная)
как?              → adhikṛtya (сделав предметом)
кого?             → te (этих двух)
каких?            → abhijñānaśākuntale («Абхиджняна-Шакунтала»)
что значит? (iti) → abhijñānam ca śākuntalā ca (узнавание и Шакунтала)
```

The full worked bracket translation of this example lives in
[`/klammeruebersetzung`](https://github.com/gasyoun/claude-config/blob/main/commands/klammeruebersetzung.md).

## Optional rendering — the descending staircase / tree

The same parse can be *drawn* (a view, not a new analysis). **The head is always at the top-right
and never on the left** — it is the last (rightmost) word of the sentence, so every layout must
put it rightmost; a head-left, children-indent-right file-tree layout inverts the structure and
teaches the wrong reading. Every modifier hangs below-and-left of its head and connects up-right
to it; the eye finds the head on the right and walks left.

**1. Descending staircase — with questions** — head at top-right, each modifier one step
down-and-left (the leftward drift mirrors right→left peeling), the driving case-question on the
right of each rung, dvandva members forking at the base:

```
                          nāṭakam            ← что?  (ядро — всегда справа)
                      ┌──────┘
                   kṛtam                      ← какая?
               ┌──────┘
            sa-adhikṛtya                      ← как?
        ┌──────┘
      te                                      ← кого?  (дв. ч.)
  ┌──────┘
abhijñānaśākuntale                            ← каких?  (= iti)
  ├───────────┐
abhijñānam   śākuntalā                        ← что значит?  (dvandva)
```

**2. Compact staircase — without questions** — the same head-right spine, questions stripped but
glosses kept, at a comfortable width (~2–3× the cramped form): each modifier hangs down-left of
its head and rises up-right by `──┘`; the dvandva pair branches downward off its node (a coordinate
pair has no head, so `head-right` does not apply to the two members — they are simply listed):

```
                                    nāṭakam (драма)
                            kṛtam ──┘
                adhikṛtya ──┘
           te ──┘
abhijñānaśākuntale ──┘
    │
    ├─ abhijñānam (узнавание)
    └─ śākuntalā (Шакунтала)       [iti]
```

**3. Ultra-compact — bare** — no questions, no glosses, minimal width: words + connectors only,
head still rightmost, the dvandva forking horizontally at the base. The tersest structural glance:

```
                  nāṭakam
             kṛtam ┘
         adhikṛtya ┘
                te ┘
abhijñānaśākuntale ┘
      ┌─────┴─────┐
 abhijñānam   śākuntalā
```

Render rules for the ASCII forms: **head always rightmost — never flip it left** (a head-left
file-tree layout is wrong in all three); fixed-width font only (say so if the target may reflow).
Pick by need: **1** with questions = the teaching form; **2** glossed, no questions = the readable
structural view; **3** bare = the tersest glance. The fork belongs at the dvandva, and `[iti]`
marks the naming node.

## Publication-grade form — the Klammerdiagramm (SVG)

For a long compound — long in **members (lemmas combined), never in letters**: a two-lemma
title is short however many letters it spans — the classic German-Indological rendering is the
**Klammerdiagramm**: the compound printed left→right, hatched vertical brackets (arrow-topped)
under each member, and a descending staircase of labelled binary nodes showing the nesting. It is
**right-branching**: the rightmost pair is the deepest node, and each member to the left accretes
onto the accumulated right group — the same right-to-left binding this whole method reads. This is
ASCII's ceiling; produce it as **SVG**, not text.

Worked example (committed asset; the printed reference plate itself is
[`assets/klammerdiagramm-target-plate.png`](klammerdiagramm/klammerdiagramm-target-plate.png) —
recovered 14-07-2026 from the H814 session transcript, MG's 12-07 upload):
[`assets/klammerdiagramm-uddama-example.svg`](klammerdiagramm/klammerdiagramm-uddama-example.svg),
generated by [`assets/build_klammerdiagramm.py`](assets/build_klammerdiagramm.py) —
`uddāma-ajñāna-rūpa-prabalatama-tamaḥ-stoma-soma-svabhāvā-…`, node **A** = `soma+svabhāvā`
(deepest, right), building leftward to **G** = the whole compound, split into `I часть / II часть`.

SVG render rules — **plate-fidelity mode** (H814, 12-07-2026, traced 1:1 from the printed
reference plate; supersedes the earlier "no arrows" note): use `currentColor` (theme-safe) with a
diagonal `<pattern>` hatch; every bar carries **two up-arrows**, one per vertical edge, tips just
under the compound line; each node is an **L-shaped hatched bracket** — the left member's bar turns
at node depth into a horizontal hatched band running right, and the **node label sits at the band's
end**; a **thin elbow connector** runs from the label rightward then up to the next-deeper node;
the deepest node is a **∪** (both bars into one bottom band, label in a white gap near the right
bar); the `I часть / II часть` captions sit **inline** with their dashed rules, which dip toward
the part-split hyphen as mirrored ogee curves meeting in a cusp; the compound carries a trailing
hyphen; `role="img"` + `<title>`/`<desc>`. To draw another compound, edit the `tokens`, `cx`, and
`nodes` tables in the generator — the binary `nodes` list encodes the right-branching analysis, and
each node's `label_x` is a **plate parameter** (measured off the plate being reproduced, not
derivable). **Direction is a law, with one exception (MG ruling, 15-07-2026): every samāsa
binds right-to-left — the head is last and everything accretes onto the accumulated right
group — while the dvandva alone is coordinate, "different in every regard": it has no
internal head, so its members are never chained like modifiers; in the diagram a dvandva
block renders FLAT — all member bars dropping into one shared band with a single node
label — and coordinations may themselves be coordinated: sibling blocks share a rung,
their bands joined one rung lower (a dvandva of dvandvas, e.g. BG 2.14
śīta-uṣṇa-sukha-duḥkha-dāḥ). The law covers the avyayībhāva too (MG, 15-07-2026):
pūrvapada-pradhāna in the tradition, but its bracket binds right-to-left like every
samāsa — the avyaya's governing role is semantics, like the bahuvrīhi's exocentricity;
dvandva remains the sole exception.**

**Six sub-rulings from the Leitan conspectus crosswalk (MG votes, 15-07-2026 — H982 /
H997).** These settle every remaining annotation question against the same
structure-is-geometry / class-is-semantics separation: **(D1) dvigu** = an ordinary
right-to-left directed pair, numeral member first (his three Pāṇinian conditions —
taddhitārthe / uttarapade / samāhāre — are classification, not structure); this closes the
last taxonomy gap in the drawing grammar. **(D2) samāhāra-dvandva** (pāṇipādamukham,
collective neuter singular) draws with the same flat band as itaretara-dvandva — no visual
mark; name the collective subtype in the analysis line only. **(D3) first-part-dominant
idioms** — ekadeśin / prathamā-tatpuruṣa (pūrvakāya, rājadanta) and mayūravyaṃsakādi /
X-antara (vanāntaram = «другой лес») — keep the bracket exceptionless (binds right-to-left);
their «перевёрнутое доминирование» is a semantics footnote, never a structural mark (same
precedent as bahuvrīhi exocentricity and avyayībhāva prominence). **(D4) madhyamapadalopin**
(śākapārthiva = śāka-⟨priya⟩-pārthiva): the vote was **reject** — «одной только сноски
недостаточно» — so the elided middle member is **restored in the word line in editorial
brackets** (`śāka-[priya]-pārthivaḥ`, the generator's `"ghosts"` config key): measured
into the run, but no bar, no arrows, no node index. Worked example: gallery §11. **(D6) śītoṣṇa-type**
(viśeṣaṇobhayapada-karmadhāraya): draw as a directed pair — the class (karmadhāraya) wins
over the dvandva-like *śītaṃ ca tad uṣṇaṃ ca* vigraha, which is the analysis idiom, not
coordination of the compound itself — with a note. (D5, the uddāma constituency, is a
gallery decision — MG voted Leitan's braced reading canonical; see the worked-examples doc.)
The dedicated skill for this form is
[`/klammerdiagramm`](https://github.com/gasyoun/claude-config/blob/main/commands/klammerdiagramm.md); [`/sanskrit-parse`](https://github.com/gasyoun/claude-config/blob/main/commands/sanskrit-parse.md)
and [`/klammeruebersetzung`](https://github.com/gasyoun/claude-config/blob/main/commands/klammeruebersetzung.md) may also emit it on request.
The generator is config-driven (`--config <json>` with `tokens`/`nodes`/`II_START`,
H792 14-07-2026) and, since the 15-07-2026 tight-run refit, sets the compound as **one
flush-hyphenated run** with every x derived from real Charis advance widths — matching the
plate's setting exactly (explicit `cx` in the config switches back to the legacy spaced
layout). It emits, next to the bare SVG, a **self-contained HTML** that
base64-embeds a WOFF2 subset of Charis 7.000 (`assets/charis-klammer-subset.woff2`, family
renamed "Klammer Serif" per the OFL Reserved-Font-Name rules — licence bundled as
[`assets/OFL-Charis.txt`](klammerdiagramm/OFL-Charis.txt), provenance
[`assets/make_charis_subset.py`](klammerdiagramm/make_charis_subset.py)) — 1:1 rendering with no
installed font required.

_Dr. Mārcis Gasūns_
