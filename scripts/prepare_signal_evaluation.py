import pandas as pd
from pathlib import Path

# Locate project folders
PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "listing_sample.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "signal_evaluation.csv"

# Load existing listing data
df = pd.read_csv(INPUT_FILE)

# Check required columns
required_columns = ["L_ListingID", "remarks"]

for column in required_columns:
    if column not in df.columns:
        raise ValueError(
            f"Missing column: {column}. Available columns: {list(df.columns)}"
        )

# Remove listings without remarks
df = df.dropna(subset=["remarks"])
df = df[df["remarks"].astype(str).str.strip() != ""]

# Select 50 random listings
sample_size = min(50, len(df))

sample = df.sample(
    n=sample_size,
    random_state=42
).copy()

# Create manual labeling columns
label_columns = [
    "expected_bedrooms",
    "expected_bathrooms",
    "expected_price",
    "expected_sqft",
    "expected_amenities",
    "expected_condition",
    "expected_financing",
    "expected_location",
    "expected_keywords"
]

# Create blank labeling columns
for column in label_columns:
    sample[column] = ""

# Rename listing ID for consistency
sample = sample.rename(columns={
    "L_ListingID": "listing_id"
})

# Select evaluation columns
evaluation_df = sample[
    ["listing_id", "remarks"] + label_columns
]

# Save evaluation dataset
evaluation_df.to_csv(OUTPUT_FILE, index=False)

print(f"Created evaluation dataset: {OUTPUT_FILE}")
print(f"Number of listings: {len(evaluation_df)}")
print("\nColumns:")
print(evaluation_df.columns.tolist())