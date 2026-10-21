# Trustworthy Generative AI — TD1

ESILV, Data & AI major, year 4. Pack `2026-10-18-students-1`.

This repository records the TD1 comparison of five free language models on
twenty natural-language-to-SQL questions. Every model receives the same prompt,
returns one SQLite `SELECT`, and is evaluated against independently computed
references on the distributed read-only database.

## Subgroup

Seven members:

- WinterBete — full name and contribution to complete;
- Mathias — contribution to complete;
- Arman — contribution to complete;
- Emma — contribution to complete;
- Fakhar — contribution to complete;
- Nour — contribution to complete;
- Sfaxi — contribution to complete.

No phone number, API key, password or private account information belongs in
this public repository.

## Current status

- Environment and database integrity: checked.
- Access preparation: five required models passed on 21 October 2026.
- References: 20/20 produced by SQLite and independently matched from CSV.
- Instructor answer-key validation: pending.
- Real 100-cell model batch: pending.
- Comparison and five-model summary: pending measured traces.

## Reproduce the local evidence

Python 3.10 or later is required. The reference builder only uses the standard
library.

```powershell
python verify-data.py
python scripts/build_references.py
python skeleton-multi-llm-en.py --demo
```

`scripts/build_references.py` writes `reference-td1.csv` only when the SQLite
values equal a separate Python computation over the distributed CSV files. See
`reference-cross-check.json` for the twenty comparisons.

## Run a real allocated batch

Set `GROQ_API_KEY` or `OPENROUTER_API_KEY` in the current terminal without
putting it in a file. Run only the model assigned to the operator, after the
corresponding references have been validated. Example:

```powershell
python skeleton-multi-llm-en.py --run `
  --models groq:openai/gpt-oss-120b `
  --cases C01,C02,C03 `
  --state state-A.jsonl `
  --out traces-A.csv
```

Keep separate state and trace files for every operator, retain every attempt,
respect the three-second pause and allow at most one retry per cell. The two
OpenRouter batches must be run by two different members' accounts. Never rerun
the five-model access probe merely to recreate proof because it consumes five
additional calls.

## Required TD1 artefacts

- `reference-td1.csv`: explicit SQL and reference value for C01–C20;
- `traces-td1.csv` and `traces-td1.jsonl`: every real call and attempt;
- `model-question-comparison-en.csv`: one final row per model/question;
- `five-model-summary-en.csv`: index, price/access documentation and results;
- `prompts-en.md`: exact shared system and user prompts;
- `modeles-autorises.json`: exact routes and parameters used;
- `reports/td1.md`: work, evidence, failures, limits and contributions.

The empty or work-in-progress files are intentional until real session evidence
exists. Synthetic demo output must never be presented as a real model batch.

## Conventions

- Revenue is `SUM(quantity_product * price)` in euro cents excluding VAT.
- Time intervals are closed on the left and open on the right.
- Age means completed years, including month and day.
- Empty selections return integer zero, not `NULL`.
- The supplied database is never modified.

## AI assistance

Codex assisted with repository preparation, SQL authoring, the independent CSV
cross-check and documentation. The subgroup must review and be able to explain
every query and trace. Reference values come from local execution and an
independent check, never from adopting an LLM's numerical answer.

