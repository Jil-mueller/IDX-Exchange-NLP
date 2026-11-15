import re
import nltk
import pandas as pd

class ListingSummarizer:

    def __init__(self, taxonomy=None):
        self.taxonomy = taxonomy or {}

    def extractive_summary(self, remarks, entities=None, num_sentences=2):
        """
        Select the most informative sentences from listing remarks.
        """

        if not remarks or not isinstance(remarks, str):
            return ""

        entities = entities or {}

        # Split remarks into sentences
        sentences = nltk.sent_tokenize(remarks)

        if not sentences:
            return ""

        # Collect important property features
        features = []

        for category, terms in self.taxonomy.items():
            if isinstance(terms, list):
                features.extend(terms)

        # Score each sentence
        scored_sentences = []

        for i, sentence in enumerate(sentences):
            score = 0
            sentence_lower = sentence.lower()

            # Give the first sentence a bonus
            if i == 0:
                score += 2

            # Reward mentions of structured entities
            for key, value in entities.items():
                if value is not None and str(value).lower() in sentence_lower:
                    score += 1

            # Reward mentions of property features
            for feature in features:
                if feature.lower() in sentence_lower:
                    score += 2

            scored_sentences.append((score, i, sentence))

        # Select the highest-scoring sentences
        top_sentences = sorted(
            scored_sentences,
            key=lambda x: (-x[0], x[1])
        )[:num_sentences]

        # Restore original sentence order
        top_sentences.sort(key=lambda x: x[1])

        return " ".join(sentence for score, i, sentence in top_sentences)

    def generate_listing_summary(self, listing):
        """
        Generate a complete listing summary using structured listing
        information and important sentences from the remarks.
        """

        # Get structured listing information
        beds = listing.get("beds")
        baths = listing.get("baths")
        price = listing.get("price")
        address = listing.get("L_Address")
        city = listing.get("L_City")
        remarks = listing.get("remarks", "")

        # Format numbers without unnecessary decimal places
        def format_number(value):
            if value is None or pd.isna(value):
                return None

            if float(value).is_integer():
                return str(int(value))

            return str(value)

        # Build the basic property description
        details = []

        if beds is not None and not pd.isna(beds):
            details.append(f"{format_number(beds)}-bedroom")

        if baths is not None and not pd.isna(baths):
            details.append(f"{format_number(baths)}-bath")

        if address and city:
            location = f"{address}, {city}"
        else:
            location = city or address

        if location:
            details.append(f"located at {location}")

        if price is not None and not pd.isna(price):
            details.append(f"listed at ${float(price):,.0f}")

        summary_parts = []

        if details:
            bedroom_detail = None
            bathroom_detail = None

            if beds is not None and not pd.isna(beds):
                bedroom_detail = f"{format_number(beds)} bedrooms"

            if baths is not None and not pd.isna(baths):
                bathroom_detail = f"{format_number(baths)} bathrooms"

            property_details = []

            if bedroom_detail:
                property_details.append(bedroom_detail)

            if bathroom_detail:
                property_details.append(bathroom_detail)

            if address and city:
                property_location = f"{address}, {city}"
            else:
                property_location = city or address

            opening = "This property"

            if property_details:
                opening += " features " + " and ".join(property_details)

            if property_location:
                opening += f" and is located at {property_location}"

            if price is not None and not pd.isna(price):
                opening += f". It is listed at ${float(price):,.0f}"
            else:
                opening += "."

            summary_parts.append(opening + ".")

        # Find and rank property features mentioned in the remarks
        remarks_lower = remarks.lower() if isinstance(remarks, str) else ""

        feature_scores = {}

        for category, terms in self.taxonomy.items():

            if category not in ["amenities", "condition", "location", "keywords"]:
                continue

            if not isinstance(terms, list):
                continue

            for feature in terms:

                feature_lower = feature.lower()

                # Look for the feature as a complete phrase
                pattern = r"\b" + re.escape(feature_lower) + r"\b"

                matches = re.findall(pattern, remarks_lower)

                if matches:
                    # Reward features mentioned multiple times
                    score = len(matches) * 2

                    # Give more weight to specific features
                    score += len(feature_lower) / 20

                    feature_scores[feature_lower] = score

        # Sort by feature importance
        ranked_features = sorted(
            feature_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top_features = [feature for feature, score in ranked_features[:2]]

        if top_features:
            feature_text = "Highlights include " + " and ".join(top_features) + "."
            summary_parts.append(feature_text)

        # Select an informative sentence that adds new information
        sentences = nltk.sent_tokenize(remarks) if isinstance(remarks, str) else []

        best_sentence = ""
        best_score = -1

        for sentence in sentences:

            sentence_lower = sentence.lower()
            score = 0

            # Reward sentences that mention useful property features
            for feature in top_features:
                if feature in sentence_lower:
                    score += 2

            # Reward sentences that mention additional amenities
            for category in ["amenities", "condition", "location", "keywords"]:
                terms = self.taxonomy.get(category, [])

                if isinstance(terms, list):
                    for term in terms:
                        if term.lower() in sentence_lower:
                            score += 1

            # Penalize sentences that repeat structured information
            if beds is not None and not pd.isna(beds):
                if re.search(r"\b" + re.escape(str(int(beds))) + r"\s*[- ]?bed", sentence_lower):
                    score -= 3

            if baths is not None and not pd.isna(baths):
                if re.search(r"\b" + re.escape(str(int(baths))) + r"\s*[- ]?bath", sentence_lower):
                    score -= 3

            # Penalize sentences that repeat the selected feature highlights
            if any(feature in sentence_lower for feature in top_features):
                score -= 1

            # Prefer sentences that provide meaningful additional detail
            if len(sentence.split()) < 8:
                score -= 2

            if score > best_score:
                best_score = score
                best_sentence = sentence

        if best_sentence:
            # Clean up formatting artifacts
            best_sentence = re.sub(r"\s+", " ", best_sentence).strip()
            best_sentence = best_sentence.lstrip("~ -")

            summary_parts.append(best_sentence)

        return " ".join(summary_parts)


import json
from pathlib import Path


import json
import pandas as pd
from pathlib import Path


if __name__ == "__main__":

    # Load taxonomy
    project_root = Path(__file__).resolve().parents[1]
    taxonomy_path = project_root / "data" / "processed" / "signal_taxonomy.json"

    with open(taxonomy_path, "r", encoding="utf-8") as file:
        taxonomy = json.load(file)

    # Load actual listing data
    data_path = project_root / "data" / "processed" / "listing_sample.csv"
    df = pd.read_csv(data_path)

    # Initialize summarizer
    summarizer = ListingSummarizer(taxonomy)

    # Generate a summary for every listing
    df["generated_summary"] = df.apply(
        lambda listing: summarizer.generate_listing_summary(listing),
        axis=1
    )

    # Save results
    output_path = project_root / "data" / "processed" / "listing_summaries.csv"
    df.to_csv(output_path, index=False)

    print("SUMMARY GENERATION COMPLETE")
    print("Listings processed:", len(df))
    print("Output saved to:", output_path)

    print("\nEXAMPLE SUMMARIES")

    for index, row in df.head(5).iterrows():
        print("\nListing:", row["L_ListingID"])
        print(row["generated_summary"])