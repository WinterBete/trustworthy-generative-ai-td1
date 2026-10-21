#!/usr/bin/env python3
"""Merge real operator traces and build the two required TD1 summaries."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "modeles-autorises.json"
QUESTIONS = ROOT / "questions-td1.json"

COMPARISON_FIELDS = (
    "case_id",
    "model_id",
    "trace_file",
    "cell_id",
    "nature",
    "status",
    "value_cents",
    "reference_cents",
    "explanation",
)

SUMMARY_FIELDS = (
    "provider",
    "model_id",
    "public_index",
    "index_date",
    "index_source",
    "paid_route_same_model",
    "input_usd_per_million",
    "output_usd_per_million",
    "price_date",
    "price_source",
    "access_used",
    "period_results",
    "age_results",
    "product_results",
    "combined_results",
    "trace_files",
    "limits",
)

MODEL_METADATA = {
    "openai/gpt-oss-120b": {
        "public_index": "11.6",
        "paid_route_same_model": "openrouter:openai/gpt-oss-120b",
        "input_usd_per_million": "0.15",
        "output_usd_per_million": "0.60",
    },
    "openai/gpt-oss-20b": {
        "public_index": "9.0",
        "paid_route_same_model": "N/A — no paid route for the exact model documented in the supplied portfolio",
        "input_usd_per_million": "N/A",
        "output_usd_per_million": "N/A",
    },
    "cohere/north-mini-code:free": {
        "public_index": "N/A — model absent from the supplied portfolio snapshot",
        "paid_route_same_model": "N/A — exact paid route not documented in the supplied portfolio",
        "input_usd_per_million": "N/A",
        "output_usd_per_million": "N/A",
    },
    "qwen/qwen3.8-27b": {
        "public_index": "33.7",
        "paid_route_same_model": "N/A — exact paid route not documented in the supplied portfolio",
        "input_usd_per_million": "N/A",
        "output_usd_per_million": "N/A",
    },
    "dots-studio/dots-3-note-preview:free": {
        "public_index": "N/A — model absent from the supplied portfolio snapshot",
        "paid_route_same_model": "N/A — exact paid route not documented in the supplied portfolio",
        "input_usd_per_million": "N/A",
        "output_usd_per_million": "N/A",
    },
}


def explanation(row: dict[str, str]) -> str:
    status = row.get("verdict", "")
    detail = row.get("verdict_detail", "").strip()
    error = row.get("error", "").strip()
    http_status = row.get("http_status", "").strip()
    if status == "correct":
        return "Returned SQL produced the independently checked reference value."
    parts = []
    if detail:
        parts.append(detail)
    if http_status and http_status != "200":
        parts.append(f"HTTP {http_status}")
    if error:
        parts.append(error)
    if row.get("sql", "").strip():
        parts.append("See returned SQL in the referenced raw trace cell.")
    return "; ".join(parts) or "No usable final result; inspect the referenced raw trace."


def family(question_type: str) -> str:
    if "+" in question_type:
        return "combined_results"
    if question_type.startswith("period"):
        return "period_results"
    if question_type.startswith("age"):
        return "age_results"
    return "product_results"


def format_family(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "0/0"
    counts = Counter(row["status"] for row in rows)
    correct = counts.pop("correct", 0)
    suffix = ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))
    return f"{correct}/{len(rows)} correct" + (f"; {suffix}" if suffix else "")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace_csv", nargs="*", type=Path, help="operator trace CSV files; defaults to traces-[A-E].csv")
    args = parser.parse_args()
    trace_paths = args.trace_csv or sorted(ROOT.glob("traces-[A-E].csv"))
    if not trace_paths:
        raise SystemExit("No real operator traces found. Pass trace CSV paths or create traces-A.csv through traces-E.csv.")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    models = [(item["gate"], item["identifiant_exact"]) for item in config["modeles"] if not item.get("optionnel")]
    question_items = json.loads(QUESTIONS.read_text(encoding="utf-8"))["questions"]
    question_types = {item["id"]: item["type"] for item in question_items}

    raw_rows: list[dict[str, str]] = []
    source_by_cell: dict[tuple[str, str, str], str] = {}
    fieldnames: list[str] | None = None
    for path in trace_paths:
        full_path = path if path.is_absolute() else ROOT / path
        with full_path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None:
                raise RuntimeError(f"Missing header in {full_path}")
            if fieldnames is None:
                fieldnames = reader.fieldnames
            elif reader.fieldnames != fieldnames:
                raise RuntimeError(f"Trace header mismatch in {full_path}")
            for row in reader:
                if row.get("nature") != "real":
                    raise RuntimeError(f"Non-real row found in measured input {full_path}: {row.get('nature')}")
                raw_rows.append(row)
                key = (row["provider"], row["model_requested"], row["case_id"])
                source_by_cell[key] = full_path.name

    if fieldnames is None:
        raise RuntimeError("No trace rows loaded")
    merged_csv = ROOT / "traces-td1.csv"
    with merged_csv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(raw_rows)

    latest: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in raw_rows:
        key = (row["provider"], row["model_requested"], row["case_id"])
        current = latest.get(key)
        if current is None or int(row.get("attempts") or 0) >= int(current.get("attempts") or 0):
            latest[key] = row

    comparison: list[dict[str, str]] = []
    for provider, model_id in models:
        for question in question_items:
            case_id = question["id"]
            key = (provider, model_id, case_id)
            row = latest.get(key)
            if row is None:
                comparison.append(
                    {
                        "case_id": case_id,
                        "model_id": f"{provider}:{model_id}",
                        "trace_file": "",
                        "cell_id": f"{provider}:{model_id}:{case_id}",
                        "nature": "real",
                        "status": "not_executed",
                        "value_cents": "",
                        "reference_cents": "",
                        "explanation": "No real trace row supplied for this required cell.",
                    }
                )
                continue
            comparison.append(
                {
                    "case_id": case_id,
                    "model_id": f"{provider}:{model_id}",
                    "trace_file": source_by_cell[key],
                    "cell_id": row["cell_id"],
                    "nature": row["nature"],
                    "status": row["verdict"],
                    "value_cents": row.get("value", ""),
                    "reference_cents": row.get("reference", ""),
                    "explanation": explanation(row),
                }
            )

    comparison_path = ROOT / "model-question-comparison-en.csv"
    with comparison_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COMPARISON_FIELDS)
        writer.writeheader()
        writer.writerows(comparison)

    summary: list[dict[str, str]] = []
    for provider, model_id in models:
        model_rows = [row for row in comparison if row["model_id"] == f"{provider}:{model_id}"]
        buckets: dict[str, list[dict[str, str]]] = {name: [] for name in ("period_results", "age_results", "product_results", "combined_results")}
        for row in model_rows:
            buckets[family(question_types[row["case_id"]])].append(row)
        metadata = MODEL_METADATA.get(model_id, {})
        files = sorted({row["trace_file"] for row in model_rows if row["trace_file"]})
        summary.append(
            {
                "provider": provider,
                "model_id": model_id,
                "public_index": metadata.get("public_index", "N/A — not documented"),
                "index_date": "2026-09-28",
                "index_source": "portefeuille-modeles-2026-09-28.csv",
                "paid_route_same_model": metadata.get("paid_route_same_model", "N/A — not documented"),
                "input_usd_per_million": metadata.get("input_usd_per_million", "N/A"),
                "output_usd_per_million": metadata.get("output_usd_per_million", "N/A"),
                "price_date": "2026-09-28",
                "price_source": "portefeuille-modeles-2026-09-28.csv",
                "access_used": f"{provider} free",
                "period_results": format_family(buckets["period_results"]),
                "age_results": format_family(buckets["age_results"]),
                "product_results": format_family(buckets["product_results"]),
                "combined_results": format_family(buckets["combined_results"]),
                "trace_files": "; ".join(files),
                "limits": "Twenty-question local batch; not a general ranking. Missing measurements remain empty.",
            }
        )

    summary_path = ROOT / "five-model-summary-en.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(summary)

    print(f"Merged {len(raw_rows)} real attempts into {merged_csv.name}")
    print(f"Wrote {len(comparison)} required final cells and {len(summary)} model summaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

