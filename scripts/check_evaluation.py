
import pandas as pd
import os

from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"

results_path = DATA_DIR / "relevance_judgments.csv"
summary_path = DATA_DIR / "search_evaluation_summary.csv"

print("Project root:", PROJECT_ROOT)
print("Results file:", results_path)
print("Results file exists:", results_path.exists())
print("Summary file exists:", summary_path.exists())

results = pd.read_csv(results_path)
summary = pd.read_csv(summary_path)

print("=== DATASET CHECK ===")
print("Result rows:", len(results))
print("Unique queries:", results["query"].nunique())
print("Methods:", results["method"].unique())
print("Missing remarks:", results["remarks"].isna().sum())

print("\n=== RELEVANCE LABELS ===")
print(
    results.groupby("method")["estimated_relevant"]
    .value_counts(normalize=True)
    .unstack(fill_value=0)
    .round(3)
)

print("\n=== PERFORMANCE SUMMARY ===")
print(summary.round(3).to_string(index=False))

print("\n=== SAMPLE RESULTS ===")
print(
    results[
        ["query", "method", "rank", "estimated_relevant", "remarks"]
    ].head(10).to_string(index=False)
)
