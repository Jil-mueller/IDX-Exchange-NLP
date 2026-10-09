
from pathlib import Path
import pandas as pd

from scripts.entity_extractor import EntityExtractor


# Find the project folder and input/output files
project_dir = Path(__file__).resolve().parents[1]

labels_path = project_dir / "data" / "processed" / "entity_labels.csv"
errors_path = project_dir / "data" / "processed" / "entity_extraction_errors.csv"

# Load your manually labeled data
df = pd.read_csv(labels_path)
print("Labels file:", labels_path)
print("\nFirst 5 manually labeled values:")
print(df[["listing_id", "bedrooms", "bathrooms", "price", "sqft", "amenities"]].head())

print("\nNumber of labeled values:")
for column in ["bedrooms", "bathrooms", "price", "sqft", "amenities"]:
    nonblank = df[column].notna() & (df[column].astype(str).str.strip() != "")
    print(f"{column}: {nonblank.sum()} / {len(df)}")
extractor = EntityExtractor()

scalar_fields = ["bedrooms", "bathrooms", "price", "sqft"]

# Count correct predictions, incorrect predictions, and missed entities
counts = {
    field: {"TP": 0, "FP": 0, "FN": 0}
    for field in scalar_fields + ["amenities"]
}

errors = []


def to_number(value):
    """Convert a labeled number to a number, or None if blank."""
    if pd.isna(value) or str(value).strip() == "":
        return None

    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def to_amenities(value):
    """Convert 'pool;garage' into {'pool', 'garage'}."""
    if pd.isna(value) or str(value).strip() == "":
        return set()

    return {
        item.strip().lower()
        for item in str(value).split(";")
        if item.strip()
    }


# Compare the extractor's predictions with your manual labels
for _, row in df.iterrows():
    text = row["remarks"]
    predictions = extractor.extract_all(
        text if isinstance(text, str) else ""
    )

    # Evaluate numeric fields
    for field in scalar_fields:
        actual = to_number(row[field])
        predicted = to_number(predictions[field])

        if actual == predicted:
            if actual is not None:
                counts[field]["TP"] += 1
        else:
            if predicted is not None:
                counts[field]["FP"] += 1
            if actual is not None:
                counts[field]["FN"] += 1

            errors.append({
                "listing_id": row["listing_id"],
                "field": field,
                "remarks": text,
                "expected": actual,
                "predicted": predicted
            })

    # Evaluate amenities individually
    actual_amenities = to_amenities(row["amenities"])
    predicted_amenities = {
        item.lower() for item in predictions["amenities"]
    }

    counts["amenities"]["TP"] += len(
        actual_amenities & predicted_amenities
    )
    counts["amenities"]["FP"] += len(
        predicted_amenities - actual_amenities
    )
    counts["amenities"]["FN"] += len(
        actual_amenities - predicted_amenities
    )

    if actual_amenities != predicted_amenities:
        errors.append({
            "listing_id": row["listing_id"],
            "field": "amenities",
            "remarks": text,
            "expected": ";".join(sorted(actual_amenities)),
            "predicted": ";".join(sorted(predicted_amenities))
        })




print("\n--- Diagnostic: Comparing labels and predictions ---")

for field in ["bedrooms", "bathrooms", "price", "sqft"]:
    mismatches = 0

    for _, row in df.iterrows():
        text = row["remarks"] if isinstance(row["remarks"], str) else ""
        prediction = extractor.extract_all(text)[field]

        actual = to_number(row[field])
        predicted = to_number(prediction)

        if actual != predicted:
            mismatches += 1

    print(f"{field}: {mismatches} mismatches out of {len(df)} listings")

# Calculate and display precision, recall, and F1
for field, values in counts.items():
    tp = values["TP"]
    fp = values["FP"]
    fn = values["FN"]

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0
    )

    print(f"\n{field.upper()}")
    print(f"TP: {tp}, FP: {fp}, FN: {fn}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall:    {recall:.2%}")
    print(f"F1:        {f1:.2%}")


# Save mistakes for error analysis
pd.DataFrame(errors).to_csv(errors_path, index=False)

print(f"\nSaved error analysis to: {errors_path}")