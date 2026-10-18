class SchemaValidator:
    """Validate parsed real-estate filters before SQL generation."""

    def __init__(
        self,
        allowed_cities=None,
        min_price=0,
        max_price=100_000_000,
        max_beds=20,
        max_baths=20,
    ):
        self.allowed_cities = (
            {city.strip().casefold() for city in allowed_cities}
            if allowed_cities is not None
            else None
        )
        self.min_price = min_price
        self.max_price = max_price
        self.max_beds = max_beds
        self.max_baths = max_baths

    def validate(self, filters):
        """
        Return (is_valid, errors).

        If is_valid is False, errors explains what needs to be fixed.
        """
        errors = []

        # Validate price filters.
        price_min = filters.get("price_min")
        price_max = filters.get("price_max")

        for field, value in [
            ("price_min", price_min),
            ("price_max", price_max),
        ]:
            if value is not None:
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or value < self.min_price
                    or value > self.max_price
                ):
                    errors.append(
                        f"{field} must be between "
                        f"{self.min_price} and {self.max_price}."
                    )

        if (
            isinstance(price_min, (int, float))
            and not isinstance(price_min, bool)
            and isinstance(price_max, (int, float))
            and not isinstance(price_max, bool)
            and price_min > price_max
        ):
            errors.append("Minimum price cannot exceed maximum price.")

        # Validate exact, minimum, and maximum room counts.
        for field, maximum in [
            ("beds", self.max_beds),
            ("beds_min", self.max_beds),
            ("beds_max", self.max_beds),
            ("baths", self.max_baths),
            ("baths_min", self.max_baths),
            ("baths_max", self.max_baths),
        ]:
            value = filters.get(field)

            if value is not None:
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or value < 0
                    or value > maximum
                ):
                    errors.append(
                        f"{field} must be between 0 and {maximum}."
                    )

        # Check for contradictory room ranges.
        for room in ["beds", "baths"]:
            minimum = filters.get(room + "_min")
            maximum = filters.get(room + "_max")
            exact = filters.get(room)

            if (
                minimum is not None
                and maximum is not None
                and minimum > maximum
            ):
                errors.append(
                    f"{room} minimum cannot exceed its maximum."
                )

            if exact is not None:
                if minimum is not None and exact < minimum:
                    errors.append(
                        f"{room} exact count is below its minimum."
                    )
                if maximum is not None and exact > maximum:
                    errors.append(
                        f"{room} exact count exceeds its maximum."
                    )

        # Validate city against the configured city list.
        city = filters.get("city")

        if city and self.allowed_cities is not None:
            if city.strip().casefold() not in self.allowed_cities:
                errors.append(f"Unsupported city: {city}")

        # Validate amenity names.
        allowed_amenities = {
            "pool",
            "garage",
            "garden",
            "fireplace",
            "basement",
            "balcony",
            "waterfront",
            "patio",
            "yard",
            "air_conditioning",
        }

        for field in ["amenities", "exclude_amenities"]:
            values = filters.get(field, [])

            if not isinstance(values, list):
                errors.append(f"{field} must be a list.")
                continue

            for amenity in values:
                if amenity not in allowed_amenities:
                    errors.append(
                        f"Unsupported amenity in {field}: {amenity}"
                    )


        # Validate square footage.
        for field in ["sqft_min", "sqft_max"]:
            value = filters.get(field)

            if value is not None:
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or value < 0
                ):
                    errors.append(
                        f"{field} must be a non-negative number."
                    )

        sqft_min = filters.get("sqft_min")
        sqft_max = filters.get("sqft_max")

        if (
            isinstance(sqft_min, (int, float))
            and not isinstance(sqft_min, bool)
            and isinstance(sqft_max, (int, float))
            and not isinstance(sqft_max, bool)
            and sqft_min > sqft_max
        ):
            errors.append(
                "Minimum square footage cannot exceed maximum square footage."
            )

        # Validate garage spaces.
        garage_spaces = filters.get("garage_spaces")

        if garage_spaces is not None:
            if (
                isinstance(garage_spaces, bool)
                or not isinstance(garage_spaces, int)
                or garage_spaces < 0
                or garage_spaces > 20
            ):
                errors.append(
                    "garage_spaces must be an integer between 0 and 20."
                )


        return len(errors) == 0, errors
