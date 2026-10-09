
import re


class EntityExtractor:

    def __init__(self):
        # Keep these aligned with the amenities in your Week 1 taxonomy.
        self.amenities_list = [
            "swimming pool", "swimming pools", "pool", "pools",
            "garage", "fireplace", "laundry", "hardwood floors",
            "balcony", "patio", "garden", "fenced yard",
            "waterfront", "gym", "community clubhouse",
            "walk-in closet"
        ]

    def extract_bedrooms(self, text):
        patterns = [
            r'\b(\d+)\s*[- ]?\s*(?:bedrooms?|beds?|bdrm|br|bd)\b'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def extract_bathrooms(self, text):
        patterns = [
            r'\b(\d+(?:\.\d+)?)\s*[- ]?\s*'
            r'(?:(?:full|half|three-quarter)\s+)?'
            r'(?:bathrooms?|baths?|ba|bth)\b'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))

        return None

    def extract_price(self, text):
        # First look for prices with a dollar sign, such as $450,000 or $450k.
        patterns = [
            r'\$\s*(\d[\d,]*(?:\.\d+)?)\s*([km])?\b',
            r'\b(?:priced at|price of|asking price)\s+\$?'
            r'(\d[\d,]*(?:\.\d+)?)\s*([km])?\b'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                number = float(match.group(1).replace(",", ""))
                suffix = (match.group(2) or "").lower()

                if suffix == "k":
                    number *= 1_000
                elif suffix == "m":
                    number *= 1_000_000

                return int(number)

        return None

    def extract_sqft(self, text):
        pattern = (
            r'\b([\d,]+)\s*'
            r'(?:square feet|sq\.?\s*ft\.?|sqft|square-foot|square footage)\b'
        )

        for match in re.finditer(pattern, text, re.IGNORECASE):
            number = match.group(1).replace(",", "")

            # Skip a match if it does not contain a valid number.
            if not number.isdigit():
                continue

            after = text[match.end():match.end() + 25]
            if re.match(r'\s*[-,]?\s*lot\b', after, re.IGNORECASE):
                continue

            before = text[max(0, match.start() - 30):match.start()]
            if re.search(
                    r'\b(?:lot size|lot is|lot measuring)\s*:?\s*$',
                    before,
                    re.IGNORECASE
            ):
                continue

            return int(number)

        return None

    def extract_amenities(self, text):
        found = []

        for amenity in self.amenities_list:
            # Match whole terms, allowing a plural ending where appropriate.
            pattern = r'(?<!\w)' + re.escape(amenity) + r'(?!\w)'

            if re.search(pattern, text, re.IGNORECASE):
                found.append(amenity)

        # Avoid returning both "pool" and "swimming pool" for the same phrase.
        if re.search(r'\bswimming pools?\b', text, re.IGNORECASE):
            found = [
                item for item in found
                if item not in ("pool", "pools", "swimming pool", "swimming pools")
            ]
            found.append(
                "swimming pools"
                if re.search(r'\bswimming pools\b', text, re.IGNORECASE)
                else "swimming pool"
            )

        return found

    def extract_all(self, text):
        if not isinstance(text, str):
            text = ""

        return {
            "bedrooms": self.extract_bedrooms(text),
            "bathrooms": self.extract_bathrooms(text),
            "price": self.extract_price(text),
            "sqft": self.extract_sqft(text),
            "amenities": self.extract_amenities(text)
        }


if __name__ == "__main__":
    extractor = EntityExtractor()

    examples = [
        "Beautiful 3 bedroom, 2 bathroom home with 2,000 square feet, priced at $450,000.",
        "A 3-bedroom, 1-bath home with 1,092 square feet and a 6,642-square-foot lot.",
        "This home has 2 bedrooms and 2 full bathrooms.",
        "A property with a 13,486 Sq Ft Lot!",
        "A home priced at $450k with a swimming pool and garage."
    ]

    for example in examples:
        print(example)
        print(extractor.extract_all(example))
        print()