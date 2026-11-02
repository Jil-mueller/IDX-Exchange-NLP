
import re
import json
from pathlib import Path

from entity_extractor import EntityExtractor


class SignalExtractor:

    def __init__(self, taxonomy, entity_extractor):
        self.taxonomy = taxonomy
        self.extractor = entity_extractor

        self.condition_terms = [
            "updated", "renovated", "remodeled",
            "new construction", "newly built",
            "move-in ready", "fixer-upper",
            "well maintained", "needs renovation"
        ]

        self.financing_terms = [
            "seller financing", "owner financing",
            "assumable mortgage", "cash only",
            "fha approved", "va approved"
        ]

        self.location_terms = [
            "waterfront", "water view", "lakefront",
            "oceanfront", "gated community",
            "golf course community", "cul-de-sac",
            "near parks", "near schools"
        ]

        self.keyword_terms = [
            "open floor plan", "natural light",
            "stainless steel appliances",
            "granite countertops", "quartz countertops",
            "walk-in closet", "high ceilings",
            "hardwood floors", "large backyard"
        ]

    def _find_terms(self, text, terms, prefer_longest=False):
        found = []

        negation_words = [
            "no", "not", "without", "never",
            "doesn't have", "does not have",
            "lacks", "lack of"
        ]

        if prefer_longest:
            terms = sorted(terms, key=len, reverse=True)

        matched_positions = []

        for term in terms:
            pattern = r'(?<!\w)' + re.escape(term) + r'(?!\w)'

            for match in re.finditer(pattern, text, re.IGNORECASE):
                overlaps = False

                if prefer_longest:
                    for start, end in matched_positions:
                        if match.start() < end and match.end() > start:
                            overlaps = True
                            break

                if overlaps:
                    continue

                preceding_text = text[
                    max(0, match.start() - 50):match.start()
                ].lower()

                is_negated = False

                for negation in negation_words:
                    negation_pattern = (
                        r'\b' + re.escape(negation)
                        + r'\b(?:\s+\w+){0,3}\s*$'
                    )

                    if re.search(negation_pattern, preceding_text):
                        is_negated = True
                        break

                if not is_negated:
                    found.append(term)

                    if prefer_longest:
                        matched_positions.append(
                            (match.start(), match.end())
                        )

                    break

        return found

    def _get_terms(self, category, fallback):
        if isinstance(self.taxonomy, dict):
            terms = self.taxonomy.get(category)

            if isinstance(terms, list):
                return terms

        return fallback

    def _match_amenities(self, remarks):
        terms = self._get_terms(
            "amenities", self.extractor.amenities_list
        )

        found = self._find_terms(
            remarks, terms, prefer_longest=True
        )

        aliases = {
            "swimming pool": "pool",
            "swimming pools": "pool",
            "pools": "pool",
            "community pool": "pool",
            "community pools": "pool",
            "swimming pool access": "pool",
            "garages": "garage",
            "fireplaces": "fireplace",
            "balconies": "balcony",
            "patios": "patio",
            "decks": "deck",
            "walk-in closets": "walk-in closet",
            "tennis courts": "tennis court",
            "playgrounds": "playground",
            "fire pit": "firepit",
            "walk-in showers": "walk-in shower",
        }

        normalized = []

        for amenity in found:
            standard_name = aliases.get(amenity, amenity)

            if standard_name not in normalized:
                normalized.append(standard_name)

        return normalized

    def _extract_condition(self, remarks):
        terms = self._get_terms("condition", self.condition_terms)
        return self._find_terms(remarks, terms, prefer_longest=True)

    def _extract_financing(self, remarks):
        terms = self._get_terms("financing", self.financing_terms)
        return self._find_terms(remarks, terms, prefer_longest=True)

    def _extract_location(self, remarks):
        terms = self._get_terms("location", self.location_terms)
        return self._find_terms(remarks, terms, prefer_longest=True)

    def _extract_keywords(self, remarks):
        terms = self._get_terms("keywords", self.keyword_terms)
        return self._find_terms(remarks, terms, prefer_longest=True)

    def extract_signals(self, listing_record):
        remarks = listing_record.get("L_Remarks", "")

        if not isinstance(remarks, str):
            remarks = ""

        entities = self.extractor.extract_all(remarks)
        entities.pop("amenities", None)

        return {
            "listing_id": listing_record.get("L_ListingID"),
            "entities": entities,
            "amenities": self._match_amenities(remarks),
            "condition_keywords": self._extract_condition(remarks),
            "financing_terms": self._extract_financing(remarks),
            "location_features": self._extract_location(remarks),
            "keywords": self._extract_keywords(remarks)
        }


# ---------------------------------------------------------
# SQL DUMP READING
# ---------------------------------------------------------

def decode_sql_value(value):
    """Convert a SQL value into a Python value."""

    value = value.strip()

    if value.upper() == "NULL":
        return None

    if len(value) >= 2 and value[0] in ("'", '"'):
        quote = value[0]
        value = value[1:-1]

        # Decode common MySQL/MariaDB escaped characters.
        replacements = {
            "0": "\0",
            "b": "\b",
            "n": "\n",
            "r": "\r",
            "t": "\t",
            "Z": "\x1a",
            "'": "'",
            '"': '"',
            "\\": "\\"
        }

        value = re.sub(
            r"\\(.)",
            lambda match: replacements.get(
                match.group(1), match.group(1)
            ),
            value
        )

        # Handle SQL's doubled quote convention.
        value = value.replace(quote + quote, quote)

        return value

    return value


def parse_sql_row(sql, position):
    """
    Parse one SQL row beginning at an opening parenthesis.
    Returns the row values and the next character position.
    """

    values = []
    current_value = []
    quote = None
    i = position + 1

    while i < len(sql):
        char = sql[i]

        if quote is not None:

            current_value.append(char)

            if char == "\\" and i + 1 < len(sql):
                i += 1
                current_value.append(sql[i])

            elif char == quote:
                # SQL can represent a quote by doubling it.
                if i + 1 < len(sql) and sql[i + 1] == quote:
                    i += 1
                    current_value.append(sql[i])
                else:
                    quote = None

        else:
            if char in ("'", '"'):
                quote = char
                current_value.append(char)

            elif char == ",":
                values.append(
                    decode_sql_value("".join(current_value))
                )
                current_value = []

            elif char == ")":
                values.append(
                    decode_sql_value("".join(current_value))
                )
                return values, i + 1

            else:
                current_value.append(char)

        i += 1

    raise ValueError("SQL row ended unexpectedly.")


def iter_listing_records(sql_path):
    """
    Read INSERT statements for rets_property and yield only
    L_ListingID and L_Remarks.

    Supports INSERT statements containing one or multiple rows.
    """

    insert_pattern = re.compile(
        r"INSERT\s+INTO\s+`?rets_property`?\s*"
        r"\((.*?)\)\s*VALUES\s*",
        re.IGNORECASE | re.DOTALL
    )

    with open(sql_path, "r", encoding="utf-8", errors="replace") as file:
        sql = file.read()

    statement_count = 0
    extracted_count = 0

    for statement in insert_pattern.finditer(sql):
        statement_count += 1

        columns = re.findall(
            r"`([^`]+)`",
            statement.group(1)
        )

        if "L_ListingID" not in columns or "L_Remarks" not in columns:
            continue

        listing_index = columns.index("L_ListingID")
        remarks_index = columns.index("L_Remarks")

        position = statement.end()

        while position < len(sql):

            # Skip whitespace and commas between rows.
            while position < len(sql) and (
                sql[position].isspace() or sql[position] == ","
            ):
                position += 1

            if position >= len(sql) or sql[position] != "(":
                break

            values, position = parse_sql_row(sql, position)

            if max(listing_index, remarks_index) >= len(values):
                raise ValueError(
                    "SQL row has fewer values than expected."
                )

            listing_id = values[listing_index]
            remarks = values[remarks_index]

            if listing_id is not None:
                extracted_count += 1

                yield {
                    "L_ListingID": listing_id,
                    "L_Remarks": remarks
                }

    if statement_count == 0:
        raise ValueError(
            "No INSERT statements for rets_property were found. "
            "Check the SQL dump format."
        )


# ---------------------------------------------------------
# COMPLETE EXTRACTION WORKFLOW
# ---------------------------------------------------------

def main():

    project_root = Path(__file__).resolve().parents[1]

    sql_path = project_root / "data" / "raw" / "rets_property.sql"

    taxonomy_path = (
        project_root / "data" / "processed" / "signal_taxonomy.json"
    )

    output_path = (
        project_root / "data" / "processed" / "listing_signals.json"
    )

    if not sql_path.exists():
        raise FileNotFoundError(
            f"SQL file not found: {sql_path}"
        )

    if not taxonomy_path.exists():
        raise FileNotFoundError(
            f"Taxonomy file not found: {taxonomy_path}"
        )

    print("Loading taxonomy...")

    with open(taxonomy_path, "r", encoding="utf-8") as file:
        taxonomy = json.load(file)

    entity_extractor = EntityExtractor()

    signal_extractor = SignalExtractor(
        taxonomy,
        entity_extractor
    )

    print("Reading SQL dump and extracting listing signals...")

    processed_count = 0

    with open(output_path, "w", encoding="utf-8") as output_file:

        output_file.write("[\n")

        first_record = True

        for listing in iter_listing_records(sql_path):

            result = signal_extractor.extract_signals(listing)

            if not first_record:
                output_file.write(",\n")

            json.dump(
                result,
                output_file,
                ensure_ascii=False
            )

            first_record = False
            processed_count += 1

            if processed_count % 1000 == 0:
                print(
                    f"Processed {processed_count:,} listings..."
                )

        output_file.write("\n]\n")

    print("\nExtraction complete.")
    print(f"Listings processed: {processed_count:,}")
    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()
