
from pathlib import Path
import pandas as pd
from scripts.entity_extractor import EntityExtractor
import re

project_dir = Path(__file__).resolve().parents[1]

input_path = (
    project_dir / "data" / "processed" / "listing_sample_cleaned.csv"
)
output_path = (
    project_dir / "data" / "processed" / "entity_extraction_errors.csv"
)

df = pd.read_csv(input_path)
extractor = EntityExtractor()

issues = []

for _, row in df.iterrows():
    text = row.get("remarks", "")

    if not isinstance(text, str):
        text = ""

    predictions = extractor.extract_all(text)
    lower_text = text.lower()

    # Flag lot measurements that might be confused with home area.
    if predictions["sqft"] is not None:
        sqft_pattern = (
            r'\b([\d,]+)\s*'
            r'(?:square feet|sq\.?\s*ft\.?|sqft|square-foot|square footage)\b'
        )

        for match in re.finditer(sqft_pattern, text, re.IGNORECASE):
            number = int(match.group(1).replace(",", ""))

            if number != predictions["sqft"]:
                continue

            before = text[max(0, match.start() - 100):match.start()].lower()
            after = text[match.end():match.end() + 60].lower()

            # Flag only when the matching number appears to describe a lot.
            lot_context = re.search(
                r'\b(?:lot|lot size|lot is|lot measuring)\b',
                before
            )

            living_context = re.search(
                r'\b(?:home|house|living space|living area|'
                r'floor plan|residence|property features)\b',
                before
            )

            if lot_context and not living_context:
                issues.append({
                    "listing_id": row.get("L_ListingID", ""),
                    "field": "sqft",
                    "possible_issue": "Square footage may refer to lot size",
                    "predicted": predictions["sqft"],
                    "remarks": text
                })

            break
    # Flag prices written in common formats that the extractor may miss.
    if predictions["price"] is None:
        price_pattern = (
            r"\$\s*\d[\d,]*(?:\.\d+)?\s*[km]?"
            r"|\b(?:priced at|asking price|price of)\s+\$?\d"
        )

        if pd.notna(text) and __import__("re").search(
            price_pattern, text, __import__("re").IGNORECASE
        ):
            issues.append({
                "listing_id": row.get("L_ListingID", ""),
                "field": "price",
                "possible_issue": "Possible price mention was not extracted",
                "predicted": None,
                "remarks": text
            })

    # Flag hyphenated or extended bedroom/bathroom phrases for review.
    patterns_to_check = {
        "bedrooms": r"\b\d+\s*-\s*bedroom\b",
        "bathrooms": r"\b\d+\s+full\s+bathrooms?\b"
    }

    for field, pattern in patterns_to_check.items():
        if __import__("re").search(pattern, text, __import__("re").IGNORECASE):
            if predictions[field] is None:
                issues.append({
                    "listing_id": row.get("L_ListingID", ""),
                    "field": field,
                    "possible_issue": f"Possible missed {field} mention",
                    "predicted": None,
                    "remarks": text
                })

pd.DataFrame(issues).to_csv(output_path, index=False)

print(f"Listings analyzed: {len(df)}")
print(f"Potential issues flagged: {len(issues)}")
print(f"Saved report to: {output_path}")