#!/usr/bin/env python3
"""Build TD1 references and cross-check them against the distributed CSV files.

The primary result is produced by explicit SQLite SELECT statements.  A second,
independent implementation loads the CSV files and applies the same conventions
with Python's datetime module.  The script refuses to write reference-td1.csv if
the two implementations disagree.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATABASE = DATA / "boutique.sqlite"
QUESTIONS = ROOT / "questions-td1.json"
OUTPUT = ROOT / "reference-td1.csv"
CHECK_OUTPUT = ROOT / "reference-cross-check.json"


BASE_SELECT = """SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM orders AS o
JOIN product AS p ON p.product_id = o.product_id"""


QUERIES: dict[str, str] = {
    "C01": BASE_SELECT + "\nWHERE o.date >= '2026-03-01 00:00:00' AND o.date < '2026-06-01 00:00:00';",
    "C02": BASE_SELECT + "\nJOIN customers AS c ON c.customer_id = o.customer_id\nWHERE c.birth_date > date('2026-09-25', '-26 years') AND c.birth_date <= date('2026-09-25', '-25 years');",
    "C03": BASE_SELECT + "\nWHERE o.product_id IN ('a', 'b', 'c') AND o.date >= '2026-01-01 00:00:00' AND o.date < '2026-07-01 00:00:00';",
    "C04": BASE_SELECT + "\nWHERE o.date >= '2026-01-01 00:00:00' AND o.date < '2026-10-01 00:00:00';",
    "C05": BASE_SELECT + "\nWHERE o.date >= '2026-06-01 00:00:00' AND o.date < '2026-06-02 00:00:00';",
    "C06": BASE_SELECT + "\nWHERE o.date >= '2025-01-01 00:00:00' AND o.date < '2026-01-01 00:00:00';",
    "C07": BASE_SELECT + "\nWHERE o.date >= '2026-05-31 00:00:00' AND o.date < '2026-06-01 00:00:00';",
    "C08": BASE_SELECT + "\nJOIN customers AS c ON c.customer_id = o.customer_id\nWHERE c.birth_date > date('2026-09-24', '-26 years') AND c.birth_date <= date('2026-09-24', '-25 years');",
    "C09": BASE_SELECT + "\nJOIN customers AS c ON c.customer_id = o.customer_id\nWHERE c.birth_date > date('2026-09-26', '-26 years') AND c.birth_date <= date('2026-09-26', '-25 years');",
    "C10": BASE_SELECT + "\nJOIN customers AS c ON c.customer_id = o.customer_id\nWHERE c.birth_date > date(o.date, '-26 years') AND c.birth_date <= date(o.date, '-25 years');",
    "C11": BASE_SELECT + "\nJOIN customers AS c ON c.customer_id = o.customer_id\nWHERE c.birth_date > date('2026-12-01', '-26 years') AND c.birth_date <= date('2026-12-01', '-25 years');",
    "C12": BASE_SELECT + "\nWHERE o.product_id IN ('a', 'b', 'c');",
    "C13": BASE_SELECT + "\nWHERE o.product_id IN ('a', 'c') AND o.date >= '2026-04-01 00:00:00' AND o.date < '2026-05-01 00:00:00';",
    "C14": BASE_SELECT + "\nWHERE o.product_id IN ('a', 'b', 'c') AND o.date >= '2026-10-01 00:00:00' AND o.date < '2026-12-01 00:00:00';",
    "C15": BASE_SELECT + "\nJOIN customers AS c ON c.customer_id = o.customer_id\nWHERE o.date >= '2026-03-01 00:00:00' AND o.date < '2026-06-01 00:00:00' AND c.birth_date > date('2026-09-25', '-26 years') AND c.birth_date <= date('2026-09-25', '-25 years');",
    "C16": BASE_SELECT + "\nJOIN customers AS c ON c.customer_id = o.customer_id\nWHERE o.product_id IN ('a', 'b', 'c') AND c.birth_date > date('2026-09-25', '-26 years') AND c.birth_date <= date('2026-09-25', '-25 years');",
    "C17": BASE_SELECT + "\nJOIN customers AS c ON c.customer_id = o.customer_id\nWHERE o.product_id IN ('a', 'b', 'c') AND o.date >= '2026-01-01 00:00:00' AND o.date < '2026-07-01 00:00:00' AND c.birth_date > date('2026-09-25', '-26 years') AND c.birth_date <= date('2026-09-25', '-25 years');",
    "C18": BASE_SELECT + "\nJOIN customers AS c ON c.customer_id = o.customer_id\nWHERE o.date >= '2026-05-01 00:00:00' AND o.date < '2026-06-01 00:00:00' AND c.birth_date > date(o.date, '-26 years') AND c.birth_date <= date(o.date, '-25 years');",
    "C19": BASE_SELECT + "\nJOIN customers AS c ON c.customer_id = o.customer_id\nWHERE o.product_id = 'd' AND o.date >= '2026-09-01 00:00:00' AND o.date < '2026-10-01 00:00:00' AND c.birth_date > date('2026-09-25', '-26 years') AND c.birth_date <= date('2026-09-25', '-25 years');",
    "C20": BASE_SELECT + "\nWHERE o.date >= '2026-06-01 00:00:00' AND o.date < '2026-09-01 00:00:00';",
}


def load_csv_data() -> tuple[dict[str, int], dict[str, date], list[dict[str, object]]]:
    with (DATA / "product.csv").open(encoding="utf-8", newline="") as stream:
        prices = {row["product_id"]: int(row["price"]) for row in csv.DictReader(stream)}
    with (DATA / "customers.csv").open(encoding="utf-8", newline="") as stream:
        births = {row["customer_id"]: date.fromisoformat(row["birth_date"]) for row in csv.DictReader(stream)}
    with (DATA / "orders.csv").open(encoding="utf-8", newline="") as stream:
        orders = []
        for row in csv.DictReader(stream):
            orders.append(
                {
                    "date": datetime.strptime(row["date"], "%Y-%m-%d %H:%M:%S"),
                    "customer_id": row["customer_id"],
                    "product_id": row["product_id"],
                    "quantity": int(row["quantity_product"]),
                }
            )
    return prices, births, orders


def completed_age(birth: date, reference: date) -> int:
    return reference.year - birth.year - ((reference.month, reference.day) < (birth.month, birth.day))


def csv_reference(case_id: str, prices: dict[str, int], births: dict[str, date], orders: list[dict[str, object]]) -> int:
    specs = {
        "C01": ("2026-03-01 00:00:00", "2026-06-01 00:00:00", None, None, False),
        "C02": (None, None, None, "2026-09-25", False),
        "C03": ("2026-01-01 00:00:00", "2026-07-01 00:00:00", {"a", "b", "c"}, None, False),
        "C04": ("2026-01-01 00:00:00", "2026-10-01 00:00:00", None, None, False),
        "C05": ("2026-06-01 00:00:00", "2026-06-02 00:00:00", None, None, False),
        "C06": ("2025-01-01 00:00:00", "2026-01-01 00:00:00", None, None, False),
        "C07": ("2026-05-31 00:00:00", "2026-06-01 00:00:00", None, None, False),
        "C08": (None, None, None, "2026-09-24", False),
        "C09": (None, None, None, "2026-09-26", False),
        "C10": (None, None, None, None, True),
        "C11": (None, None, None, "2026-12-01", False),
        "C12": (None, None, {"a", "b", "c"}, None, False),
        "C13": ("2026-04-01 00:00:00", "2026-05-01 00:00:00", {"a", "c"}, None, False),
        "C14": ("2026-10-01 00:00:00", "2026-12-01 00:00:00", {"a", "b", "c"}, None, False),
        "C15": ("2026-03-01 00:00:00", "2026-06-01 00:00:00", None, "2026-09-25", False),
        "C16": (None, None, {"a", "b", "c"}, "2026-09-25", False),
        "C17": ("2026-01-01 00:00:00", "2026-07-01 00:00:00", {"a", "b", "c"}, "2026-09-25", False),
        "C18": ("2026-05-01 00:00:00", "2026-06-01 00:00:00", None, None, True),
        "C19": ("2026-09-01 00:00:00", "2026-10-01 00:00:00", {"d"}, "2026-09-25", False),
        "C20": ("2026-06-01 00:00:00", "2026-09-01 00:00:00", None, None, False),
    }
    start_text, end_text, products, reference_text, age_at_order = specs[case_id]
    start = datetime.strptime(start_text, "%Y-%m-%d %H:%M:%S") if start_text else None
    end = datetime.strptime(end_text, "%Y-%m-%d %H:%M:%S") if end_text else None
    reference = date.fromisoformat(reference_text) if reference_text else None
    total = 0
    for order in orders:
        order_date = order["date"]
        product_id = str(order["product_id"])
        birth = births[str(order["customer_id"])]
        if start is not None and order_date < start:
            continue
        if end is not None and order_date >= end:
            continue
        if products is not None and product_id not in products:
            continue
        if reference is not None and completed_age(birth, reference) != 25:
            continue
        if age_at_order and completed_age(birth, order_date.date()) != 25:
            continue
        total += int(order["quantity"]) * prices[product_id]
    return total


def main() -> int:
    question_ids = [item["id"] for item in json.loads(QUESTIONS.read_text(encoding="utf-8"))["questions"]]
    if question_ids != list(QUERIES):
        raise RuntimeError("The explicit SQL set does not match the distributed question order")

    prices, births, orders = load_csv_data()
    checks: list[dict[str, object]] = []
    rows: list[dict[str, object]] = []
    connection = sqlite3.connect(DATABASE.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        for case_id in question_ids:
            sql_value = int(connection.execute(QUERIES[case_id]).fetchone()[0])
            independent_value = csv_reference(case_id, prices, births, orders)
            ok = sql_value == independent_value
            checks.append(
                {
                    "case_id": case_id,
                    "sqlite_revenue_cents": sql_value,
                    "csv_python_revenue_cents": independent_value,
                    "ok": ok,
                }
            )
            rows.append({"case_id": case_id, "sql": QUERIES[case_id], "revenue_cents": sql_value})
    finally:
        connection.close()

    CHECK_OUTPUT.write_text(json.dumps({"checks": checks, "ok": all(row["ok"] for row in checks)}, indent=2) + "\n", encoding="utf-8")
    if not all(row["ok"] for row in checks):
        raise RuntimeError(f"Independent reference mismatch; inspect {CHECK_OUTPUT}")

    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("case_id", "sql", "revenue_cents"))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} independently matched references to {OUTPUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

