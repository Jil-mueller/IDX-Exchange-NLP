

from pathlib import Path
import pandas as pd


from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

print("Project root:", PROJECT_ROOT)
print("\nMatching CSV files:")

for file_path in PROJECT_ROOT.rglob("*.csv"):
    if "rets" in file_path.name.lower() or "property" in file_path.name.lower():
        print(file_path)


if file_path.exists():
    try:
        df = pd.read_csv(file_path, low_memory=False)

        print("\n=== DATASET OVERVIEW ===")
        print("Rows:", len(df))
        print("Columns:", len(df.columns))
        print("Column names:")
        print(df.columns.tolist())

        print("\n=== FIRST 5 ROWS ===")
        print(df.head().to_string())

        print("\n=== POTENTIAL LISTING FIELDS ===")
        for col in df.columns:
            if any(term in col.lower() for term in
                   ["listingid", "listing_id", "remarks", "description",
                    "address", "price", "bed", "bath"]):
                print(f"\n{col}:")
                print(df[col].head(3).to_list())

    except Exception as e:
        print("Could not read this as a CSV:", repr(e))

