# Design: top-1000 частотных композитов с меткой samaса-типа

_Создан: 25-11-2026 · Статус: spec, ждёт ревью MG · Владелец: SamasaChakram (дерево Drumam)_

## 1. Контекст и цель

В DCS/Hellwig частотные данные есть, меток типа нет ([FINDINGS §449](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md#449-samāsa-type-frequency-does-not-exist-in-any-org-corpus-and-the-grammarians-canonical-examples-are-corpus-ghosts-858-attested-max-freq-147)):
841 052 члена композитов, 396 571 предложение, `feat_case='Cpd'`, но ни одного type-тега.
Задача: построить **топ-1000 частотных композитов DCS с присвоенным типом самасы**,
применив наш собственный тест — дерево решений Drumam — и **одновременно проверить сам тест**
на имеющемся золоте.

Результат — не «частотность типов» (такого вывода данные не поддерживают), а ранжированный
список *композитов* с полем `type` = выход классификатора, плюс отчёт о его точности.

## 2. Non-goals

- Не редактировать `cmps.csv` в VisualDCS и не переименовывать «категорию» Kompozity в тип.
- Не делать заявлений о частоте типов/подтипов (FINDINGS §449 запрещает такой вывод).
- Не расширять таксономию 58 подтипов и не менять колесо/квиз.
- Не импортировать Scharf/Rāmopākhyāna в этом PR (нужна проверка machine-readable выгрузки и прав).

## 3. Источники

| Роль | Источник | Что даёт |
|---|---|---|
| Ранжирование | `VisualDCS/derived-data/Kompozity/cmps.csv` + `names.csv` | поверхность, члены, частота (как в kosha `build_samasa_trainer.py`) |
| Правила | `drumam/archive/samasa_decision_tree.html` → `NODES`, `RESULTS`, `AVYAYA_WORDS`, `PREVERB_LIST`, `CANONICAL_DB` | узлы дерева, формулировки вопросов, списки preverb/avyaya |
| Gold (DCS) | `SanskritGrammar/sangram/articles/tatpurusha/data/{validation_sample.tsv,annotations_full.tsv,validation_verdicts.tsv}` (H989) | 120 DCS-композитов, coarse 4 класса + fine, два слепых прохода, κ 0,93/0,72; виграхи в `annotations_full.tsv` |
| Gold (внекорпусный) | `kosha/data/gita/gita_morphology_gold.tsv`, колонка `compound` | 759 однозначных, 4 класса (перекос: 458 TP / 298 BV) |
| Weak supervision | MW/AP90 definitional mentions; `MWderivations/issue15` (природа правого члена, НЕ тип) | подсказки на этапе формулировки вопроса к LLM |

Лицензия: DCS CC BY 4.0 → атрибуция в выходном TSV и отчёте; в репозиторий попадают только
производные таблицы, не сырые базы.

## 4. Архитектура

Новый каталог `samasacakra/top1000/` в SamasaChakram (владелец дерева Drumam; kosha остаётся
потребителем через отдельный edge в `PROJECT_INTERLINKS.md`):

1. **`drumam_rules.py`** — загружает JS-объекты (`NODES`, `RESULTS`, `AVYAYA_WORDS`,
   `PREVERB_LIST`) прямо из HTML-дерева (регулярные выражения + `json`-совместимые фрагменты,
   без ручного копирования правил). Даёт граф переходов `yes/no → next node` и список
   семантических вопросов. Форм-ветки (`detectPrefix`, acc.sg.nt., состав члена) отвечаются
   детерминированно; семантические помечаются `needs_llm`.
2. **`build_top1000.py`** — читает `cmps.csv`/`names.csv` по тому же контракту, что kosha,
   берёт top-1000 по corpus frequency, пишет `rank / compound / members / freq`.
3. **`semantic_jev.py`** — переиспользует `Uprava/tools/jev_probe.py` через `importlib`
   (как `samasa_subtype_jev_choice_probe.py`), вопрос типа `choice` с criteria `{yes, no}`;
   в `state`: композит, члены, виграха (если есть) и **60 few-shot примеров из 120 золотых**
   H989; dry-run по умолчанию, live только `--run`. Ключ из `~/.secrets/typesafe.env`.
4. **`validate.py`** — оценка на 60 holdout из H989 (seed 20260715) и на 759 Gita-gold
   (только однозначные). Метрики: coverage, accuracy coarse, accuracy fine, confusion matrix,
   long-run unknown rate, сравнение с κ=0,93/0,72 как референсом двух людей.
5. Выходы: `data/top1000_typed.tsv` (rank, compound, members, freq, type_coarse, type_fine,
   confidence, decision_path, source=`drumam+jev`, gold_agree, license), `reports/TOP1000_TYPED_REPORT.md`,
   `data/top1000_manifest.json` (hash, row count, provenance, cost).

## 5. Валидация и гейты

- **Kill-gate:** если coarse accuracy на DCS-holdout < 0.70 (порог C5/H989), таблица не
  публикуется как typed — только отчёт с диагнозом. Порог зафиксирован до прогона.
- Недоступные/неуверенные ответы → `type=unknown`, **никогда не угадываем**.
- Dry-run является default; `--run` требует `--max-cost USD` (оценка: ~2.5M input tokens
  ≈ $0.11 при $0.042/1M; JEV output free).
- Приёмка: `python samasacakra/top1000/check_top1000.py` — fail-closed проверка схемы,
  1000 строк, уникальных поверхностей, валидных type-меток, согласованности manifest/hash.

## 6. Риски и честный остаток

- У топ-1000 из `cmps.csv` нет виграх — семантические вопросы LLM отвечает по поверхности
  и членам; точность может быть ниже, чем на 120 золотых с виграхами. Это измеряется и
  публикуется, а не скрывается.
- 120 DCS-gold смещены в tatpuruṣa (design P4); Gita-gold смещён в TP/BV. Оба — частичные
  эталоны, не репрезентативная выборка по 4 классам.
- Двойные метки Gita (56) исключаются из validate, но учитываются в отчёте.
- Scharf/Rāmopākhyāna может дать более тонкое золото; без проверки прав в этот PR не входит.

## 7. Acceptance

- Отчёт с метриками и kill-gate вердиктом; TSV с 1000 строками и честным `unknown`-остатком;
  манифест с происхождением и атрибуцией; PR в SamasaChakram, запись в changelog_queue;
  отдельная строка cross-repo edge в Uprava `PROJECT_INTERLINKS.md` (kosha → consuming).
