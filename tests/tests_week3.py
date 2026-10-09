from pathlib import Path
import pandas as pd
from scripts.entity_extractor import EntityExtractor


project_dir = Path(__file__).resolve().parents[1]

input_path = project_dir / "data" / "processed" / "listing_sample_cleaned.csv"
output_path = project_dir / "data" / "processed" / "entity_labels.csv"

df = pd.read_csv(input_path)

project_dir = Path(__file__).resolve().parents[1]

labels_path = project_dir / "data" / "processed" / "entity_labels.csv"
errors_path = project_dir / "data" / "processed" / "entity_extraction_errors.csv"

df = pd.read_csv(labels_path)
extractor = EntityExtractor()

scalar_fields = ["bedrooms", "bathrooms", "price", "sqft"]

# Track true positives, false positives, and false negatives
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


for _, row in df.iterrows():
    text = row["remarks"]
    predictions = extractor.extract_all(
        text if isinstance(text, str) else ""
    )

    # Evaluate bedrooms, bathrooms, price, and sqft
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

    # Evaluate amenities as sets of individual entities
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


# Calculate and print precision, recall, and F1
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


# Save errors so they can be reviewed
pd.DataFrame(errors).to_csv(errors_path, index=False)
print(f"\nSaved error analysis to: {errors_path}")


import unittest
from scripts.entity_extractor import EntityExtractor


class TestEntityExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = EntityExtractor()

    def test_hyphenated_bedroom_and_bathroom(self):
        text = "A 3-bedroom, 1-bath home"
        self.assertEqual(self.extractor.extract_bedrooms(text), 3)
        self.assertEqual(self.extractor.extract_bathrooms(text), 1.0)

    def test_full_bathrooms(self):
        text = "2 bedrooms and 2 full bathrooms"
        self.assertEqual(self.extractor.extract_bedrooms(text), 2)
        self.assertEqual(self.extractor.extract_bathrooms(text), 2.0)

    def test_living_area_not_lot_area(self):
        text = "Home with 1,092 square feet on a 6,642-square-foot lot"
        self.assertEqual(self.extractor.extract_sqft(text), 1092)

    def test_lot_area_only(self):
        text = "13,486 Sq Ft Lot"
        self.assertIsNone(self.extractor.extract_sqft(text))


    def test_price_with_commas(self):
        text = "Beautiful home priced at $450,000"
        self.assertEqual(self.extractor.extract_price(text), 450000)

    def test_price_with_k_suffix(self):
        text = "Asking price $450k"
        self.assertEqual(self.extractor.extract_price(text), 450000)

    def test_swimming_pool_amenity(self):
        text = "The property offers multiple swimming pools."
        amenities = self.extractor.extract_amenities(text)
        self.assertTrue(
            any("pool" in amenity for amenity in amenities)
        )

    def test_multiple_amenities(self):
        text = "Features include a garage, fireplace, and patio."
        amenities = self.extractor.extract_amenities(text)
        self.assertIn("garage", amenities)
        self.assertIn("fireplace", amenities)
        self.assertIn("patio", amenities)


if __name__ == "__main__":
    unittest.main()