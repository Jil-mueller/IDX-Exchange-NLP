
class SQLGenerator:
    """Build parameterized SQL queries from validated real-estate filters."""

    ALLOWED_COLUMNS = {
        "beds": "beds",
        "beds_min": "beds",
        "beds_max": "beds",
        "baths": "baths",
        "baths_min": "baths",
        "baths_max": "baths",
        "price_min": "price",
        "price_max": "price",
        "city": "city",
    }

    ALLOWED_AMENITIES = {
        "pool": "pool",
        "garage": "garage",
        "garden": "garden",
        "fireplace": "fireplace",
        "basement": "basement",
        "balcony": "balcony",
        "waterfront": "waterfront",
        "patio": "patio",
        "yard": "yard",
        "air_conditioning": "air_conditioning",
    }

    def __init__(self, table_name="listings"):
        # Table names cannot be supplied as SQL parameters.
        # Only permit known, safe SQL identifiers.
        if not table_name.replace("_", "").isalnum():
            raise ValueError("Invalid table name.")
        if not table_name[0].isalpha() and table_name[0] != "_":
            raise ValueError("Invalid table name.")

        self.table_name = table_name

    def to_sql(self, filters):
        """
        Return (query, params) for a validated filter dictionary.

        Uses '?' placeholders, as supported by SQLite and several
        other DB-API drivers. Use the placeholder style required by
        your actual database driver.
        """

        conditions = []
        params = []

        supported_filters = {
            "beds", "beds_min", "beds_max",
            "baths", "baths_min", "baths_max",
            "price_min", "price_max", "city",
            "amenities", "exclude_amenities",
        }

        unsupported_filters = []

        for key, value in filters.items():
            if key in supported_filters:
                continue

            # Ignore empty/default values from the parser.
            if value is None or value == [] or value == "":
                continue
            if isinstance(value, bool) and value is False:
                continue

            unsupported_filters.append(key)

        if unsupported_filters:
            raise ValueError(
                "SQL generation does not yet support these filters: "
                + ", ".join(unsupported_filters)
            )

        # Exact bedroom/bathroom counts.
        for key, column in [
            ("beds", "beds"),
            ("baths", "baths"),
        ]:
            value = filters.get(key)
            if value is not None:
                conditions.append(f"{column} = ?")
                params.append(value)

        # Minimum and maximum room counts.
        for key, operator in [
            ("beds_min", ">="),
            ("beds_max", "<="),
            ("baths_min", ">="),
            ("baths_max", "<="),
        ]:
            value = filters.get(key)
            if value is not None:
                column = "beds" if key.startswith("beds") else "baths"
                conditions.append(f"{column} {operator} ?")
                params.append(value)

        # Price boundaries.
        if filters.get("price_min") is not None:
            conditions.append("price >= ?")
            params.append(filters["price_min"])

        if filters.get("price_max") is not None:
            conditions.append("price <= ?")
            params.append(filters["price_max"])

        # City equality.
        if filters.get("city"):
            conditions.append("city = ?")
            params.append(filters["city"])

        # Positive and negative amenities.
        for field, operator in [
            ("amenities", "="),
            ("exclude_amenities", "!="),
        ]:
            for amenity in filters.get(field, []):
                column = self.ALLOWED_AMENITIES.get(amenity)
                if column is None:
                    raise ValueError(f"Unsupported amenity: {amenity}")

                conditions.append(f"{column} {operator} ?")
                params.append(True if operator == "=" else False)

        query = f"SELECT * FROM {self.table_name}"

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        return query, tuple(params)
