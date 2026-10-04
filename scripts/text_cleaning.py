from __future__ import annotations
import re
import unicodedata
import pandas as pd
from collections import Counter
from html import unescape
from pathlib import Path


class TextCleaner:

    def __init__(self):
        self.abbrev_map = {
            'br': 'bedroom',
            'ba': 'bathroom',
            'sqft': 'square feet',
            'w/': 'with',
            'w/o': 'without',
            'mbr': 'master bedroom',
            'bd': 'bedroom',
            'bdrm': 'bedroom',
            'bth': 'bathroom',
            'baths': 'bathrooms',
            'beds': 'bedrooms',
            'gar': 'garage',
            'garages': 'garages',
            'yr': 'year',
            'yrs': 'years',
            'apt': 'apartment',
            'blvd': 'boulevard',
            'dr': 'drive',
            'hwy': 'highway',
            'ln': 'lane',
            'rd': 'road',
            'st': 'street',
            'ave': 'avenue',
            'ct': 'court',
            'condo': 'condominium',
            'hoa': 'homeowners association',
            'fp': 'fireplace',
            'frpl': 'fireplace',
            'laundry': 'laundry',
            'lvl': 'level',
            'wtr': 'water',
            'util': 'utilities',
            'rm': 'room',
            'rms': 'rooms',
            'approx': 'approximately'
        }

    def clean_text(self, text):
        if not isinstance(text, str):
            return ""

        text = self.normalize_unicode(text)
        text = self.remove_html(text)
        text = self.normalize_prices(text)
        text = self.normalize_measurements(text)
        text = self.expand_abbreviations(text)
        text = self.normalize_whitespace(text)

        return text.strip()

    def normalize_unicode(self, text):
        return unicodedata.normalize("NFKC", text)

    def remove_html(self, text):
        return re.sub(r'<[^>]+>', '', text)

    def normalize_prices(self, text):
        # 450k -> 450000
        text = re.sub(
            r'(\d+(?:\.\d+)?)\s*k\b',
            lambda m: str(int(float(m.group(1)) * 1000)),
            text,
            flags=re.IGNORECASE
        )

        # 1.2m -> 1200000
        text = re.sub(
            r'(\d+(?:\.\d+)?)\s*m\b',
            lambda m: str(int(float(m.group(1)) * 1000000)),
            text,
            flags=re.IGNORECASE
        )

        return text

    def normalize_measurements(self, text):
        # 2,000 sqft -> 2000 square feet
        text = re.sub(
            r'(\d[\d,]*)\s*sqft\b',
            lambda m: m.group(1).replace(',', '') + ' square feet',
            text,
            flags=re.IGNORECASE
        )

        # 2,000 sq ft -> 2000 square feet
        text = re.sub(
            r'(\d[\d,]*)\s*sq\s*ft\b',
            lambda m: m.group(1).replace(',', '') + ' square feet',
            text,
            flags=re.IGNORECASE
        )

        return text

    def expand_abbreviations(self, text):
        # Handle things such as 3br -> 3 bedroom
        for abbreviation, replacement in self.abbrev_map.items():

            if abbreviation in ['br', 'ba', 'bd', 'bdrm']:
                text = re.sub(
                    rf'(\d+)\s*{re.escape(abbreviation)}\b',
                    rf'\1 {replacement}',
                    text,
                    flags=re.IGNORECASE
                )

            else:
                text = re.sub(
                    rf'(?<!\w){re.escape(abbreviation)}(?!\w)',
                    replacement,
                    text,
                    flags=re.IGNORECASE
                )

        return text

    def normalize_whitespace(self, text):
        return re.sub(r'\s+', ' ', text)


    def _extract_top_ngrams(self, texts, n=10):
        words = []

        for text in texts.dropna():
            words.extend(re.findall(r'\b[a-zA-Z]+\b', text.lower()))

        counts = {}

        for word in words:
            counts[word] = counts.get(word, 0) + 1

        return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]

    def _detect_abbreviations(self, texts):
        counts = {}

        for abbreviation in self.abbrev_map:
            if abbreviation in ['br', 'ba', 'bd', 'bdrm']:
                pattern = rf'\d+\s*{re.escape(abbreviation)}\b'
            else:
                pattern = rf'(?<!\w){re.escape(abbreviation)}(?!\w)'

            count = texts.fillna("").str.contains(
                pattern,
                case=False,
                regex=True
            ).sum()

            if count > 0:
                counts[abbreviation] = int(count)

        return counts

    def profile_column(self, df, column_name):
        texts = df[column_name]

        return {
            "null_rate": texts.isnull().mean(),
            "avg_length": texts.dropna().str.len().mean(),
            "common_terms": self._extract_top_ngrams(texts),
            "price_mentions": texts.fillna("").str.contains(
                r'\$\d|\d+\s*[km]\b',
                case=False,
                regex=True
            ).sum(),
            "has_html": texts.fillna("").str.contains(
                r'<[^>]+>',
                regex=True
            ).sum(),
            "common_abbreviations": self._detect_abbreviations(texts)
        }


if __name__ == "__main__":
    cleaner = TextCleaner()

    # Load dataset
    df = pd.read_csv("../data/processed/listing_sample.csv")

    print("Number of listings:", len(df))
    print("Columns:")
    print(df.columns.tolist())

    print("\nFirst 5 remarks:")
    print(df["remarks"].head().to_string())

    examples = [
        "Beautiful 3br home",
        "2,000 sqft property",
        "Priced at 450k",
        "<b>Beautiful home</b>",
        "Home w/ large yard",
        "4ba home w/ 1.2m price"
    ]

    print("\n--- CLEANING EXAMPLES ---")

    for example in examples:
        print("\nBEFORE:", example)
        print("AFTER: ", cleaner.clean_text(example))

    # Print the data profile

    print("\n--- DATA PROFILE ---")

    profile = cleaner.profile_column(df, "remarks")

    print("Null rate:", profile["null_rate"])
    print("Average length:", profile["avg_length"])
    print("Price mentions:", profile["price_mentions"])
    print("HTML occurrences:", profile["has_html"])
    print("Common terms:", profile["common_terms"])
    print("Common abbreviations:", profile["common_abbreviations"])

    # Clean the dataset

    df["cleaned_remarks"] = df["remarks"].apply(cleaner.clean_text)

    print("\n--- FIRST 5 BEFORE / AFTER ---")

    for i in range(5):
        print("\nBEFORE:")
        print(df.loc[i, "remarks"])

        print("\nAFTER:")
        print(df.loc[i, "cleaned_remarks"])

    # Saved clean datset

    df.to_csv(
        "../data/processed/listing_sample_cleaned.csv",
        index=False
    )

    print("\nCleaned dataset saved successfully.")
