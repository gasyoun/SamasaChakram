# Хаб знаний по samaсам — указатель активов поместья

_Создан: 25-11-2026 · Статус: указатель, не копия данных_

Этот документ отвечает на вопрос «где у нас всё по самасам?». **SamasaChakram —
педагогическое ядро** (таксономия, метод чтения, тренажёры, конспект Лейтана), а не
агрегатор всех репозиториев: кёльнские словари, корпус частот и литература живут в
своих репо. Ссылки ниже — на канонические файлы; при расхождениях главный источник
всегда конспект Лейтана ([ADR 0001](adr/0001-leitan-source-and-editorial-differences.md)).

## 1. Педагогическое ядро (этот репозиторий)

| Актив | Где |
|---|---|
| Таксономия: 4 класса / 9 семейств / 58 подтипов | [`samasacakra/samasacakra-taxonomy.json`](../samasacakra/samasacakra-taxonomy.json) |
| Колесо + встроенный квиз + Pages | [`samasacakra/build_samasacakra.py`](../samasacakra/build_samasacakra.py) → [`samasacakra-wheel.html`](../samasacakra/samasacakra-wheel.html), [`docs/index.html`](index.html) |
| Метод чтения справа налево, все решения MG | [`sanskrit-right-to-left-reading.md`](../sanskrit-right-to-left-reading.md) |
| Кроссуок с конспектом, голосования D1–D6 | [`KLAMMERDIAGRAMM_LEITAN_SAMASA_COMPARISON.md`](../KLAMMERDIAGRAMM_LEITAN_SAMASA_COMPARISON.md) |
| Галерея Klammerdiagramm (20 пластин) | [`klammerdiagramm-worked-examples.md`](../klammerdiagramm-worked-examples.md), [`klammerdiagramm/`](../klammerdiagramm) |
| Дерево решений Drumam + тренажёр | [`drumam/`](../drumam), [/drumam/](drumam/index.html), [тренажёр](drumam/samasa_trainer.html) |
| Пять уроков, указатель 67 §§ | [/uroki/](uroki/index.html), [/paragrafy/](paragrafy/index.html) |
| Конспект Лейтана и приложения | [`leitan/`](../leitan), [`docs/SAMASA_Leitan_COMPLETE.docx`](SAMASA_Leitan_COMPLETE.docx), [`docs/samasa_additions.docx`](samasa_additions.docx), [`docs/samasa_checklists.docx`](samasa_checklists.docx), [`docs/samasa_formal_features.docx`](samasa_formal_features.docx) |
| Приёмка | [`check_pilot.py`](../samasacakra/check_pilot.py), [`check_quiz.py`](../samasacakra/check_quiz.py), [`check_example_pack.py`](../scripts/check_example_pack.py) |
| Глоссарий | [`CONTEXT.md`](../CONTEXT.md) |

Приложения DOCX содержат дополнительную литературу: Ruppel (2017), Зализняк
(§§ 192–194), Kulkarni & Kumar (2013), Krishna et al. (2016), MW-статистика
(funderburkjim). **Они пока файлами, не подключены к колесу/квизу** — это честный разрыв.

## 2. Практика и тренажёры в других репо

- **kosha** — разбор самас (identify + split, 3 865 упражнений, Anki):
  https://gasyoun.github.io/kosha/reading/samasa/drills/ · генератор
  [`scripts/build_samasa_trainer.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_samasa_trainer.py),
  данные `data/samasa/`.
- **csl-guides** — квиз по 15 вопросов (Wikner, karmadhāraya и lookup):
  https://sanskrit-lexicon.github.io/csl-guides/docs/users/samasa-quiz ·
  [`src/data/samasa-quiz.json`](https://github.com/sanskrit-lexicon/csl-guides/blob/main/src/data/samasa-quiz.json).

## 3. Корпус, частоты и кёльнские словари

- **VisualDCS / Digital Corpus of Sanskrit** (Oliver Hellwig, CC BY):
  `derived-data/Kompozity/cmps.csv` — 401 478 пар «композит → члены» с частотами;
  `uttarapada_dict_vs_corpus.tsv` — MW ↔ корпус по конечным членам;
  `non-derived/Zalizniak/Vyskazyvaniya/Kompozity/` — Зализняк по типам.
- **kosha** — частотный рейтинг и drills: `data/samasa/samasa_curriculum.tsv`
  (759 золотых из Гиты), `reference.tsv`, `samasa_drills.json`, `drill_weights.json`.
- **MWderivations** `issue15/compounds_reverse_classified.tsv` — 19 435 конечных членов из MW
  (колонка `class` — это `UTTARAPADA` / `KRT_STEM_MEMBER` / `TADDHITA_SUFFIX`, **не тип самасы**).
- **csl-orig** — `v02/vcp/vcp.txt`, `v02/wil/wil_etymology.tsv` (compound-строки).
- **csl-guides** — [`docs/dictionaries/corpus-attestation.mdx`](https://github.com/sanskrit-lexicon/csl-guides/blob/main/docs/dictionaries/corpus-attestation.mdx).
- **SanskritLexicography** — `FINDINGS.md` §449: меток типа самасы в DCS нет;
  из 58 канонических примеров в корпусе встречаются 8 (макс. частота 147).

## 4. Золото с меткой типа (что уже размечено)

| Набор | Объём | Метки | Где |
|---|---|---|---|
| Gita morphology gold | 815 слов, из них **759 однозначных** | 458 tatpuruṣa · 298 bahuvrīhi · 2 dvandva · 1 karmadhāraya + 56 двойных (`DV/TP`, `DV/BV` и др.) | `kosha/data/gita/gita_morphology_gold.tsv`, колонка `compound` |
| Sangram P4 (H989) | **120 DCS-композитов** | coarse 4 класса + fine подтипы татпуруши; два слепых прохода, кодбук Лейтан/Пāṇini; κ = 0,93 (117/120) coarse, 0,72 (73/93) fine | `SanskritGrammar/sangram/articles/tatpurusha/data/`: `validation_sample.tsv`, `annotations_full.tsv`, `validation_verdicts.tsv`, `kappa_result.json` |
| Bahuvrīhi exemplars | набор примеров с виграхами | неявный тип = bahuvrīhi (по статьи) | `SanskritGrammar/sangram/articles/bahuvrihi/data/bahuvrihi_exemplars.tsv` |

**В кёльнских словарях структурированной метки типа нет.** В MW/AP90 тип упоминается
в тексте статьи (`<s1>Tatpuruṣa</s1> compound`, `either Tatpuruṣa or Bahuvrīhi`) — это
полезная слабая разметка для подсказок, но не поле `type` у отдельной лексемы. По решению
MG 25-11-2026 слабая разметка лучше ничего: она пригодна как weak supervision для
классификатора, но не как gold.

**P. M. Scharf, «Rāmopākhyāna» (Sanskrit Library, 2023)** — дробная разметка самас:
classification + labeling, vigraha-vākya, dvandva, karmadhāraya, dvigu, dvitīyā–saptamī /
upapada / nañ / gati / prādi-tatpuruṣa, bahuvrīhi и явно помеченные неоднозначности
(§ II.D.2.h, II.D.3.c). Издание строится из семи файлов анализа данных, доступных через
веб-ридер; **в поместье их нет**, наличие machine-readable выгрузки и лицензия не
проверены — перед импортом нужна проверка прав. Аналогично
`csl-orig` [`COMPOUND_MARKER_TYPOGRAPHY_CENSUS_CDSL_2026.md`](https://github.com/gasyoun/SanskritLexicography/blob/master/docs/COMPOUND_MARKER_TYPOGRAPHY_CENSUS_CDSL_2026.md)
описывает типографику составных слов, не их класс. `MWderivations/issue15` размечает
**природу правого члена**, а не тип самасы. Внешние наборы, упомянутые в FINDINGS §449 —
Krishna et al. (2016, 4 класса) и идентификатор Kulkarni SCL — в поместье не лежат.

## 5. Ограничения, которые важно помнить

1. В DCS **нет аннотации типа самасы** (841 052 члена композитов, 396 571 предложение).
   любой «тип» в частотном списке — результат классификатора, не ground truth (FINDINGS §449).
2. Пять измеренных долей на колесе — из Kulkarni & Kumar (2013), выборка ≈ 64 000
   двучленных композитов, и покрывают только 5 меток, не 58 подтипов. ADR 0002
   запрещает приписывать долю по неточному совпадению метки.
3. 58 канонических примеров колеса — педагогический артефакт, не корпусная выборка;
   частотный слой по ним был бы нечестным (FINDINGS §449).
4. Списка «1000 частотных самас по Хельвигу» в поместье **нет**; ближайшее —
   `cmps.csv` (частотные композиты без типа) и kosha drills.
