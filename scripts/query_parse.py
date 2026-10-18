
import re


class QueryParser:
    """Convert natural-language real-estate queries into structured filters."""

    AMENITIES = {
        "pool": ["pool", "swimming pool"],
        "garage": ["garage", "garage parking"],
        "garden": ["garden"],
        "fireplace": ["fireplace", "fire place"],
        "basement": ["basement"],
        "balcony": ["balcony"],
        "waterfront": ["waterfront", "water front"],
        "patio": ["patio"],
        "yard": ["yard", "backyard"],
        "air_conditioning": ["air conditioning", "central air", "a/c", "ac"],
    }

    def parse(self, query):
        """Parse a natural-language query into structured filters."""
        if not isinstance(query, str):
            raise TypeError("Query must be a string.")

        text = query.lower().strip()
        filters = {
            "beds": None,
            "beds_min": None,
            "beds_max": None,
            "baths": None,
            "baths_min": None,
            "baths_max": None,
            "price_min": None,
            "price_max": None,
            "city": None,
            "amenities": [],
            "exclude_amenities": [],
            "property_type": None,
            "sqft_min": None,
            "sqft_max": None,
            "garage_spaces": None,
            "nearby_places": [],
            "features": [],
            "condition": [],
            "view": [],
            "hoa_max": None,
            "no_hoa": False,
            "investment_property": False,
            "rental_income": False,
            "price_reduced": False,
        }

        # Convert shorthand prices: 700k -> 700000, 1.2m -> 1200000.
        def price_value(number, suffix=None):
            number = float(number.replace(",", "").replace("$", ""))

            if suffix is None:
                suffix = ""

            suffix = suffix.lower().strip()

            if suffix == "k":
                number *= 1_000
            elif suffix in ("m", "million", "millions"):
                number *= 1_000_000
            elif suffix in ("b", "billion", "billions"):
                number *= 1_000_000_000

            return int(number)

        # Find price ranges such as "$400k-$700k".
        price_range = re.search(
            r"(?:between\s+)?\$?([\d,.]+)\s*(millions?|billions?|[kmb])?\s*"
            r"(?:-|to|and)\s*"
            r"\$?([\d,.]+)\s*(millions?|billions?|[kmb])?",
            text,
        )

        if price_range:
            low = price_value(
                price_range.group(1), price_range.group(2)
            )
            high = price_value(
                price_range.group(3), price_range.group(4)
            )
            filters["price_min"] = low
            filters["price_max"] = high
        else:
            # Only interpret a number as a price when the query
            # uses explicit price language or currency notation.
            upper_price = re.search(
                r"(?:under|below|less than|max(?:imum)?"
                r"(?:\s+price)?|no more than|up to)"
                r"\s+\$?([\d,.]+)\s*(millions?|billions?|[kmb])?"
                r"(?=\s|$)",
                text,
            )

            if upper_price:
                filters["price_max"] = price_value(
                    upper_price.group(1), upper_price.group(2)
                )

            lower_price = re.search(
                r"(?:over|above|more than|min(?:imum)?"
                r"(?:\s+price)?|at least)"
                r"\s+\$?([\d,.]+)\s*(millions?|billions?|[kmb])?"
                r"(?=\s|$)",
                text,
            )

            # Don't interpret room counts or square footage as prices.
            if lower_price:
                number_end = lower_price.end()
                following_text = text[number_end:].lstrip()

                if not re.match(
                        r"(?:bedrooms?|beds?|bathrooms?|baths?|"
                        r"square feet|sq\.?\s*ft|sqft)\b",
                        following_text,
                ):
                    filters["price_min"] = price_value(
                        lower_price.group(1), lower_price.group(2)
                    )

        # Bedroom and bathroom counts.
        self._parse_room_count(text, filters, "beds", r"(?:beds?|bedrooms?)")
        self._parse_room_count(text, filters, "baths", r"(?:baths?|bathrooms?)")

        # City: capture text after "in", not "near".
        # "Near" describes proximity rather than a city.
        city_match = re.search(
            r"\bin\s+"
            r"([a-z][a-z .'-]*?)"
            r"(?=\s+(?:with|without|under|below|over|above|"
            r"less than|more than|at least|no more than|"
            r"between|and|for|that have|that has)\b|$)",
            text,
        )

        if city_match:
            candidate = city_match.group(1).strip(" ,.")

            # Avoid interpreting common non-city phrases as cities.
            invalid_locations = {
                "gated communities",
                "communities",
                "good schools",
                "shopping",
                "shopping centers",
                "parks",
                "the beach",
                "a clubhouse",
                "closets",
                "ready homes",
                "downtown",
            }

            if candidate not in invalid_locations:
                filters["city"] = candidate

        # Amenities and their negations.
        for amenity, phrases in self.AMENITIES.items():
            for phrase in phrases:
                escaped = re.escape(phrase)

                # "without a pool", "no pool", "not having a pool".
                negative_pattern = (
                    r"\b(?:without|no|not having|excluding|exclude)\s+"
                    r"(?:a|an|the)?\s*" + escaped + r"\b"
                )
                if re.search(negative_pattern, text):
                    if amenity not in filters["exclude_amenities"]:
                        filters["exclude_amenities"].append(amenity)
                    continue

                # "with a pool", "has a pool", or just "pool".
                positive_pattern = (
                    r"\b(?:with|has|have|featuring)?\s*"
                    r"(?:a|an|the)?\s*" + escaped + r"\b"
                )
                if re.search(positive_pattern, text):
                    if amenity not in filters["amenities"]:
                        filters["amenities"].append(amenity)


        # Extract additional property filters.
        self._parse_additional_filters(text, filters)

        # Do not require both positive and negative versions of an amenity.
        filters["amenities"] = [
            a for a in filters["amenities"]
            if a not in filters["exclude_amenities"]
        ]

        return filters

    @staticmethod
    def _parse_room_count(text, filters, key, room_pattern):
        """Extract exact, minimum, and maximum room counts."""
        # "at least 3 bedrooms", "3+ beds", "minimum 2 baths".
        minimum = re.search(
            r"(?:at least|minimum|min)\s+(\d+(?:\.\d+)?)\s+"
            + room_pattern
            + r"|(\d+(?:\.\d+)?)\s*\+\s*"
            + room_pattern,
            text,
        )

        # "no more than 4 beds", "maximum 3 bathrooms".
        maximum = re.search(
            r"(?:no more than|at most|maximum|max)\s+"
            r"(\d+(?:\.\d+)?)\s+" + room_pattern,
            text,
        )

        # "3 bedrooms or fewer", "4 beds or less".
        if not maximum:
            maximum = re.search(
                r"(\d+(?:\.\d+)?)\s+" + room_pattern
                + r"\s+(?:or fewer|or less|or below)",
                text,
            )

        # "3 bedrooms", "2 baths" (exact count).
        exact = re.search(
            r"(\d+(?:\.\d+)?)\s+" + room_pattern + r"\b",
            text,
        )

        if minimum:
            number = minimum.group(1) or minimum.group(2)
            filters[key + "_min"] = float(number)
        elif maximum:
            filters[key + "_max"] = float(maximum.group(1))
        elif exact:
            filters[key] = float(exact.group(1))

        # Remove unnecessary .0 from whole-number room counts.
        for field in [key, key + "_min", key + "_max"]:
            value = filters[field]
            if isinstance(value, float) and value.is_integer():
                filters[field] = int(value)


    @staticmethod
    def _parse_additional_filters(text, filters):
        # Property types
        property_types = {
            "condo": ["condos", "condo"],
            "townhouse": ["townhouses", "townhome", "townhomes"],
            "single_family": [
                "single family homes",
                "single family houses",
                "single family",
            ],
        }

        for property_type, phrases in property_types.items():
            if any(phrase in text for phrase in phrases):
                filters["property_type"] = property_type
                break

        # Square footage
        sqft = re.search(
            r"(?:more than|over|larger than|greater than|at least)"
            r"\s+([\d,]+)\s*(?:square feet|sq\.?\s*ft|sqft)",
            text,
        )
        if sqft:
            filters["sqft_min"] = int(sqft.group(1).replace(",", ""))

        # Garage spaces
        garage = re.search(r"(\d+)\s*car garages?", text)
        if garage:
            filters["garage_spaces"] = int(garage.group(1))

        # Additional amenities and community facilities
        amenity_phrases = {
            "spa": ["spa"],
            "gated_community": ["gated communities", "gated community"],
            "clubhouse": ["clubhouse"],
            "tennis_court": ["tennis courts", "tennis court"],
            "fitness_center": ["fitness center", "fitness centres", "fitness centre"],
            "playground": ["playground"],
            "dog_park": ["dog park"],
            "walking_trails": ["walking trails", "walking trail"],
        }

        for name, phrases in amenity_phrases.items():
            if any(phrase in text for phrase in phrases):
                if name not in filters["amenities"]:
                    filters["amenities"].append(name)

        # Nearby places
        nearby_phrases = [
            "beach",
            "shopping and dining",
            "good schools",
            "downtown",
            "freeway",
            "restaurants",
            "parks",
            "shopping centers",
            "shopping centre",
        ]
        for phrase in nearby_phrases:
            if phrase in text and phrase not in filters["nearby_places"]:
                filters["nearby_places"].append(phrase)

        # Property features
        feature_phrases = [
            "granite countertops",
            "stainless steel appliances",
            "walk-in closets",
            "home office",
            "open floor plan",
            "hardwood floors",
            "recessed lighting",
            "laundry room",
            "family room",
            "kitchen island",
        ]
        for phrase in feature_phrases:
            if phrase in text and phrase not in filters["features"]:
                filters["features"].append(phrase)

        # Property condition
        condition_phrases = [
            "remodeled",
            "renovated",
            "move-in ready",
            "newly updated",
            "well maintained",
            "recently upgraded",
            "turnkey",
        ]
        for phrase in condition_phrases:
            if phrase in text:
                value = phrase.replace(" ", "_").replace("-", "_")
                if value not in filters["condition"]:
                    filters["condition"].append(value)

        # Property views
        view_phrases = [
            "ocean",
            "mountain",
            "city",
            "panoramic",
            "golf course",
        ]
        if "view" in text or "views" in text or "overlooking" in text:
            for phrase in view_phrases:
                if phrase in text:
                    value = phrase.replace(" ", "_")
                    if value not in filters["view"]:
                        filters["view"].append(value)

        # Financial requirements
        if re.search(r"\bno\s+hoa\b|\bwithout\s+hoa\b", text):
            filters["no_hoa"] = True

        if "investment propert" in text:
            filters["investment_property"] = True

        if "rental income" in text:
            filters["rental_income"] = True

        if "price reduction" in text:
            filters["price_reduced"] = True

        if "hoa" in text and re.search(r"\blow\b", text):
            filters["features"].append("low_hoa_fees")
