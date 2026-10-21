# TD1 report — model comparison

Status: **work in progress**. Pack: `2026-10-18-students-1`.

## Subgroup

Seven members: WinterBete (full name to complete), Mathias, Arman, Emma,
Fakhar, Nour and Sfaxi. The actual contribution of each member must be filled
in after the session; no contribution is inferred from group membership.

## Work completed

- Environment checked with Python 3.14 and the distributed database hash.
- Five required model accesses passed the preparation probe.
- Twenty SQLite reference queries were generated and executed read-only.
- Every reference value was independently recomputed from the three CSV files
  by `scripts/build_references.py`; all twenty implementations agree.

## Work still required in the session

- Have another subgroup member inspect each allocated query and record the
  human cross-check.
- Show the twenty references to the instructor and correct any value identified
  as different from the answer key before running the affected model cells.
- Run the five allocated 20-question batches and retain every raw attempt.
- Complete the comparison and five-model summary from the measured traces.
- Record observed failures, their evidence and the final member contributions.

## Method and evidence

The SQLite queries use the required half-open periods (`date >= start` and
`date < end`), revenue in euro cents excluding VAT, completed age based on
month and day, and `COALESCE(..., 0)` for empty selections. The database is
opened read-only. The independent check loads `product.csv`, `customers.csv`
and `orders.csv` and applies the same business rules with Python dates rather
than SQLite date functions.

Evidence:

- [`reference-td1.csv`](../reference-td1.csv)
- [`reference-cross-check.json`](../reference-cross-check.json)
- [`scripts/build_references.py`](../scripts/build_references.py)
- [`data/manifest.json`](../data/manifest.json)

## AI assistance and limits

Codex prepared repository files, explicit SQL and the independent CSV check.
This assistance must be disclosed and verified. A model answer was never used
as a reference amount. The instructor answer key is not available in the kit,
so instructor validation remains pending. No member contribution is claimed
until confirmed by the subgroup.

## Next steps

Run the real batches only after reference validation, then update this report
with successes, failures, trace links, limitations, contributions and the next
action for TD2.

