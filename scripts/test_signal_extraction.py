import json

from entity_extractor import EntityExtractor
from signal_extraction import SignalExtractor

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = PROJECT_ROOT / "data" / "processed" / "signal_taxonomy.json"

with open(TAXONOMY_PATH, "r") as file:
    taxonomy = json.load(file)

entity_extractor = EntityExtractor()

signal_extractor = SignalExtractor(
    taxonomy=taxonomy,
    entity_extractor=entity_extractor
)

test_remarks = [
    "Beautiful home with a swimming pool and garage.",
    "This property has no pool and no garage.",
    "Recently renovated home with hardwood floors.",
    "This home is not recently renovated.",
    "Waterfront property with a fireplace.",
    "Property without a fireplace."
]

for remarks in test_remarks:
    listing = {
        "L_ListingID": "TEST",
        "L_Remarks": remarks
    }

    print("\nRemarks:", remarks)
    print(signal_extractor.extract_signals(listing))