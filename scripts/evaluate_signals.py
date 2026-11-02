import json
import re
from pathlib import Path

import pandas as pd

from entity_extractor import EntityExtractor
from signal_extraction import SignalExtractor



# File paths


PROJECT_ROOT = Path(__file__).resolve().parent.parent

TAXONOMY_PATH = PROJECT_ROOT / "data" / "processed" / "signal_taxonomy.json"
EVALUATION_PATH = PROJECT_ROOT / "data" / "processed" / "signal_evaluation_labeled_draft.csv"

# Load taxonomy and initialize extractor

with open(TAXONOMY_PATH, "r") as file:
    taxonomy = json.load(file)

entity_extractor = EntityExtractor()

signal_extractor = SignalExtractor(
    taxonomy=taxonomy,
    entity_extractor=entity_extractor
)


# Normalization helpers

ALIASES = {
    # Amenities
    "swimming pool": "pool",
    "swimming pools": "pool",
    "pools": "pool",

    # Flooring
    "new floors": "new flooring",
    "new floor": "new flooring",

    # Countertops
    "granite counters": "granite countertops",
    "quartz counters": "quartz countertops",

    # Condition
    "updated kitchen": "updated",
    "updated bath": "updated",
    "updated bathroom": "updated",
    "updated bathrooms": "updated",
    "remodeled kitchen": "remodeled",
    "remodeled bath": "remodeled",
    "remodeled bathroom": "remodeled",
    "newly renovated": "renovated",
    "recently renovated": "renovated",
    "well-maintained": "well maintained",
    "new paint": "fresh paint",
    "freshly painted": "fresh paint",

    # Location
    "mountain view": "mountain views",
    "valley view": "valley views",
    "panoramic view": "panoramic views",
    "ocean view": "ocean views",
    "lake view": "lake views",

    # Financing
    "fha": "fha financing",
    "fha approved": "fha financing",
    "va": "va financing",
    "va approved": "va financing",
    "va loan": "va financing",
    "fha loan": "fha financing",
}


def normalize_label(value):
    value = str(value).strip().lower()
    value = re.sub(r"\s+", " ", value)
    return ALIASES.get(value, value)


def parse_labels(value):
    """Convert a pipe-separated cell into a set of labels."""

    if pd.isna(value):
        return set()

    value = str(value).strip()

    if value.upper() in ("", "NONE"):
        return set()

    return {
        normalize_label(item)
        for item in value.split("|")
        if item.strip()
    }


def normalize_scalar(value):
    """Standardize scalar values such as bedrooms and square footage."""

    if pd.isna(value):
        return None

    value = str(value).strip()

    if value.upper() in ("", "NONE", "NAN"):
        return None

    # Remove commas, dollar signs, and surrounding whitespace.
    value = value.replace(",", "").replace("$", "").strip()

    # Treat equivalent numeric formats as equal (e.g. 3 and 3.0).
    try:
        number = float(value)

        if number.is_integer():
            return str(int(number))

        return str(number)

    except ValueError:
        return value.lower()


# Evaluation metrics

def calculate_multilabel_metrics(expected_values, predicted_values):

    true_positives = 0
    false_positives = 0
    false_negatives = 0

    for expected, predicted in zip(expected_values, predicted_values):

        true_positives += len(expected & predicted)
        false_positives += len(predicted - expected)
        false_negatives += len(expected - predicted)

    if true_positives + false_positives == 0:
        precision = 0
    else:
        precision = true_positives / (
            true_positives + false_positives
        )

    if true_positives + false_negatives == 0:
        recall = 0
    else:
        recall = true_positives / (
            true_positives + false_negatives
        )

    if precision + recall == 0:
        f1 = 0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    return precision, recall, f1


# Load evaluation dataset

df = pd.read_csv(EVALUATION_PATH)

if df.empty:
    raise ValueError("The evaluation dataset is empty.")

required_columns = [
    "listing_id",
    "remarks",
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

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

# Empty labels mean the listing has not been reviewed.
label_columns = required_columns[2:]

if df[label_columns].isna().any().any():
    raise ValueError(
        "Some expected-label cells are blank. "
        "Review every field and enter NONE when nothing is present."
    )



# Run extractor on all listings
category_mapping = {
    "amenities": "amenities",
    "condition": "condition_keywords",
    "financing": "financing_terms",
    "location": "location_features",
    "keywords": "keywords"
}

predictions = []

for _, row in df.iterrows():

    listing_record = {
        "L_ListingID": row["listing_id"],
        "L_Remarks": row["remarks"]
    }

    result = signal_extractor.extract_signals(listing_record)

    predictions.append(result)


# --------------------------------------------------
# Generate detailed error report
# --------------------------------------------------

ERROR_PATH = PROJECT_ROOT / "data" / "processed" / "signal_evaluation_errors.csv"

error_rows = []

for index, prediction in enumerate(predictions):

    row = df.iloc[index]

    # Check scalar entity predictions
    for field in ["bedrooms", "bathrooms", "price", "sqft"]:

        expected = normalize_scalar(row[f"expected_{field}"])
        predicted = normalize_scalar(
            prediction["entities"].get(field)
        )

        if expected != predicted:
            error_rows.append({
                "listing_id": row["listing_id"],
                "category": field,
                "remarks": row["remarks"],
                "expected": expected,
                "predicted": predicted,
                "missed": "",
                "extra": ""
            })

    # Check multi-label predictions
    for category, prediction_key in category_mapping.items():

        expected = parse_labels(row[f"expected_{category}"])

        predicted = {
            normalize_label(item)
            for item in prediction[prediction_key]
        }

        missed = expected - predicted
        extra = predicted - expected

        if missed or extra:
            error_rows.append({
                "listing_id": row["listing_id"],
                "category": category,
                "remarks": row["remarks"],
                "expected": " | ".join(sorted(expected)),
                "predicted": " | ".join(sorted(predicted)),
                "missed": " | ".join(sorted(missed)),
                "extra": " | ".join(sorted(extra))
            })

error_df = pd.DataFrame(error_rows)

error_df.to_csv(ERROR_PATH, index=False)

print("\n========== ERROR REPORT ==========")
print(f"Listings/categories with errors: {len(error_df)}")
print(f"Saved error report to: {ERROR_PATH}")

# Compare scalar fields

scalar_fields = {
    "bedrooms": "bedrooms",
    "bathrooms": "bathrooms",
    "price": "price",
    "sqft": "sqft"
}

print("\n========== SCALAR ENTITY RESULTS ==========")

for expected_column, prediction_key in scalar_fields.items():

    correct = 0

    for index, prediction in enumerate(predictions):

        expected = normalize_scalar(
            df.iloc[index][f"expected_{expected_column}"]
        )

        predicted = normalize_scalar(
            prediction["entities"].get(prediction_key)
        )

        if expected == predicted:
            correct += 1

    accuracy = correct / len(df)

    print(
        f"{expected_column}: "
        f"{accuracy:.1%} exact-match accuracy "
        f"({correct}/{len(df)})"
    )


# Compare multi-label fields

print("\n========== FREE-TEXT SIGNAL RESULTS ==========")

for expected_category, prediction_key in category_mapping.items():

    expected_values = []
    predicted_values = []

    for index, prediction in enumerate(predictions):

        expected = parse_labels(
            df.iloc[index][f"expected_{expected_category}"]
        )

        predicted = {
            normalize_label(item)
            for item in prediction[prediction_key]
        }

        expected_values.append(expected)
        predicted_values.append(predicted)

    precision, recall, f1 = calculate_multilabel_metrics(
        expected_values,
        predicted_values
    )

    print(f"\n{expected_category.upper()}")
    print(f"Precision: {precision:.1%}")
    print(f"Recall:    {recall:.1%}")
    print(f"F1 Score:  {f1:.1%}")


print("\nEvaluation complete.")
print(f"Listings evaluated: {len(df)}")
