from pathlib import Path
import pandas as pd

from scripts.entity_extractor import EntityExtractor


# Find the project folder
project_dir = Path(__file__).resolve().parents[1]

input_path = (
    project_dir
    / "data"
    / "processed"
    / "listing_sample_cleaned.csv"
)

output_path = (
    project_dir
    / "data"
    / "processed"
    / "entity_labels.csv"
)

# Load the cleaned listings
df = pd.read_csv(input_path)

# Select listings that have remarks
sample = df[["L_ListingID", "remarks"]].dropna(
    subset=["remarks"]
)

# Randomly select up to 250 listings
sample = sample.sample(
    n=min(250, len(sample)),
    random_state=42
).copy()

# Rename the ID column
sample = sample.rename(
    columns={"L_ListingID": "listing_id"}
)

# Create the extractor
extractor = EntityExtractor()

# Extract entities from each listing's remarks
predictions = []

for text in sample["remarks"]:
    result = extractor.extract_all(text)

    predictions.append({
        "bedrooms": result["bedrooms"],
        "bathrooms": result["bathrooms"],
        "price": result["price"],
        "sqft": result["sqft"],
        "amenities": ";".join(result["amenities"])
    })

# Convert predictions into a DataFrame
predictions_df = pd.DataFrame(
    predictions,
    index=sample.index
)

# Add predictions to the listing data
sample = pd.concat(
    [sample, predictions_df],
    axis=1
)

# Save the populated CSV
sample.to_csv(output_path, index=False)

print(f"Created populated file: {output_path}")
print(f"Number of listings: {len(sample)}")
print("\nFirst five rows:")
print(sample.head().to_string(index=False))

print("\nNon-empty extracted values:")
print(
    sample[
        ["bedrooms", "bathrooms", "price", "sqft", "amenities"]
    ].notna().sum()
)
