
from scripts.query_parse import QueryParser
from scripts.schema_validation import SchemaValidator
from scripts.sql_generation import SQLGenerator
from scripts.integrated_pipepline_query import QueryPipeline

# Tests for query_parse

def test_basic_query():
    parser = QueryParser()
    result = parser.parse("3 bed under 700k in Irvine")

    assert result["beds"] == 3
    assert result["price_max"] == 700000
    assert result["city"] == "irvine"


def test_price_range():
    parser = QueryParser()
    result = parser.parse("homes between $400k and $700k")

    assert result["price_min"] == 400000
    assert result["price_max"] == 700000


def test_bedroom_minimum():
    parser = QueryParser()
    result = parser.parse("at least 3 bedrooms")

    assert result["beds_min"] == 3


def test_bathroom_count():
    parser = QueryParser()
    result = parser.parse("2 bathrooms")

    assert result["baths"] == 2


def test_amenity():
    parser = QueryParser()
    result = parser.parse("homes with a pool")

    assert "pool" in result["amenities"]


def test_amenity_negation():
    parser = QueryParser()
    result = parser.parse("homes without a pool")

    assert "pool" in result["exclude_amenities"]
    assert "pool" not in result["amenities"]


def test_invalid_input_type():
    parser = QueryParser()

    try:
        parser.parse(None)
        assert False, "Expected TypeError"
    except TypeError:
        pass

def test_price_limits():
    parser = QueryParser()

    assert parser.parse("under 500k")["price_max"] == 500000
    assert parser.parse("below $450,000")["price_max"] == 450000
    assert parser.parse("over 300k")["price_min"] == 300000
    assert parser.parse("at least 250k")["price_min"] == 250000


def test_price_range_variations():
    parser = QueryParser()

    result = parser.parse("400k to 700k")
    assert result["price_min"] == 400000
    assert result["price_max"] == 700000

    result = parser.parse("$400k-$700k")
    assert result["price_min"] == 400000
    assert result["price_max"] == 700000


def test_bedroom_variations():
    parser = QueryParser()

    assert parser.parse("3 bed")["beds"] == 3
    assert parser.parse("2 beds")["beds"] == 2
    assert parser.parse("4 bedrooms")["beds"] == 4
    assert parser.parse("at least 3 bedrooms")["beds_min"] == 3


def test_bathroom_variations():
    parser = QueryParser()

    assert parser.parse("2 baths")["baths"] == 2
    assert parser.parse("3 bathrooms")["baths"] == 3
    assert parser.parse("at least 2 bathrooms")["baths_min"] == 2


def test_city_extraction():
    parser = QueryParser()

    assert parser.parse("homes in Irvine")["city"] == "irvine"
    assert parser.parse("homes in San Diego")["city"] == "san diego"


def test_amenity_variations():
    parser = QueryParser()

    assert "pool" in parser.parse("homes with a pool")["amenities"]
    assert "garage" in parser.parse("homes with a garage")["amenities"]
    assert "fireplace" in parser.parse("homes with a fireplace")["amenities"]


def test_amenity_negation_variations():
    parser = QueryParser()

    result = parser.parse("homes without a pool")
    assert "pool" in result["exclude_amenities"]
    assert "pool" not in result["amenities"]

    result = parser.parse("homes with no garage")
    assert "garage" in result["exclude_amenities"]


def test_price_in_millions():
    parser = QueryParser()

    assert parser.parse("under 1.2m")["price_max"] == 1200000
    assert parser.parse("over 1m")["price_min"] == 1000000

# Tests for schema_validation

def test_valid_schema():
    validator = SchemaValidator(
        allowed_cities=["Irvine", "San Diego"]
    )
    parser = QueryParser()
    filters = parser.parse("3 bed under 700k in Irvine")

    is_valid, errors = validator.validate(filters)

    assert is_valid is True
    assert errors == []


def test_invalid_city():
    validator = SchemaValidator(
        allowed_cities=["Irvine", "San Diego"]
    )
    parser = QueryParser()
    filters = parser.parse("3 bed in Atlantis")

    is_valid, errors = validator.validate(filters)

    assert is_valid is False
    assert any("Unsupported city" in error for error in errors)


def test_invalid_bedroom_count():
    validator = SchemaValidator()
    filters = {
        "beds": 50,
        "price_min": None,
        "price_max": None,
    }

    is_valid, errors = validator.validate(filters)

    assert is_valid is False
    assert any("beds" in error for error in errors)


def test_reversed_price_range():
    validator = SchemaValidator()
    filters = {
        "price_min": 800000,
        "price_max": 400000,
    }

    is_valid, errors = validator.validate(filters)

    assert is_valid is False
    assert any("Minimum price" in error for error in errors)


def test_negative_price():
    validator = SchemaValidator()
    filters = {
        "price_min": -500000,
        "price_max": None,
    }

    is_valid, errors = validator.validate(filters)

    assert is_valid is False
    assert any("price_min" in error for error in errors)


def test_invalid_amenity():
    validator = SchemaValidator()
    filters = {
        "amenities": ["pool", "spaceship"],
        "exclude_amenities": [],
    }

    is_valid, errors = validator.validate(filters)

    assert is_valid is False
    assert any("spaceship" in error for error in errors)

def test_square_footage_validation():
    validator = SchemaValidator()

    # A valid square-footage range should pass.
    valid, errors = validator.validate({
        "sqft_min": 1000,
        "sqft_max": 2500
    })
    assert valid, errors

    # Negative square footage should fail.
    valid, errors = validator.validate({
        "sqft_min": -100
    })
    assert not valid

    # The minimum cannot exceed the maximum.
    valid, errors = validator.validate({
        "sqft_min": 3000,
        "sqft_max": 2000
    })
    assert not valid


def test_garage_spaces_validation():
    validator = SchemaValidator()

    # A whole-number garage space count should pass.
    valid, errors = validator.validate({
        "garage_spaces": 2
    })
    assert valid, errors

    # Fractional, negative, and excessively large values should fail.
    for value in [2.5, -1, 21, True]:
        valid, errors = validator.validate({
            "garage_spaces": value
        })
        assert not valid, f"Expected garage_spaces={value!r} to fail"

# SQL generator tests

def test_sql_basic_query():
    parser = QueryParser()
    generator = SQLGenerator()

    filters = parser.parse("3 bed under 700k in Irvine")
    query, params = generator.to_sql(filters)

    assert "beds = ?" in query
    assert "price <= ?" in query
    assert "city = ?" in query
    assert params == (3, 700000, "irvine")


def test_sql_price_range():
    generator = SQLGenerator()

    filters = {
        "price_min": 400000,
        "price_max": 700000,
    }
    query, params = generator.to_sql(filters)

    assert "price >= ?" in query
    assert "price <= ?" in query
    assert params == (400000, 700000)


def test_sql_room_ranges():
    generator = SQLGenerator()

    filters = {
        "beds_min": 2,
        "beds_max": 4,
        "baths_min": 1,
    }
    query, params = generator.to_sql(filters)

    assert "beds >= ?" in query
    assert "beds <= ?" in query
    assert "baths >= ?" in query
    assert params == (2, 4, 1)


def test_sql_amenities():
    generator = SQLGenerator()

    filters = {
        "amenities": ["pool", "garage"],
        "exclude_amenities": ["basement"],
    }
    query, params = generator.to_sql(filters)

    assert "pool = ?" in query
    assert "garage = ?" in query
    assert "basement != ?" in query
    assert params == (True, True, False)


def test_sql_injection_is_parameterized():
    generator = SQLGenerator()

    malicious_city = "Irvine' OR 1=1 --"
    filters = {"city": malicious_city}

    query, params = generator.to_sql(filters)

    assert malicious_city not in query
    assert "city = ?" in query
    assert params == (malicious_city,)


def test_sql_empty_filters():
    generator = SQLGenerator()

    query, params = generator.to_sql({})

    assert query == "SELECT * FROM listings"
    assert params == ()


def test_sql_rejects_unsafe_table_name():
    try:
        SQLGenerator("listings; DROP TABLE listings")
        assert False, "Expected ValueError"
    except ValueError:
        pass

# Query pipline tests

def test_full_pipeline():
    pipeline = QueryPipeline()

    result = pipeline.process(
        "Find homes with 3 bedrooms under $700k in Irvine"
    )

    assert result["success"], result.get("errors")
    assert result["filters"]["beds"] == 3
    assert result["filters"]["price_max"] == 700000
    assert result["filters"]["city"].casefold() == "irvine"

    sql = result["sql"]
    params = result["params"]

    assert "beds = ?" in sql
    assert "price <= ?" in sql
    assert "city = ?" in sql
    assert 3 in params
    assert 700000 in params
    assert "irvine" in [p.casefold() for p in params if isinstance(p, str)]

def test_pipeline_rejects_invalid_city():
    pipeline = QueryPipeline(
        allowed_cities=["Irvine", "San Diego"]
    )

    result = pipeline.process("3 bed in Atlantis")

    assert result["success"] is False
    assert result["sql"] is None
    assert any(
        "Unsupported city" in error
        for error in result["errors"]
    )



def test_pipeline_preserves_parameterization():
    generator = SQLGenerator()

    malicious_city = "Irvine' OR 1=1 --"
    filters = {"city": malicious_city}

    sql, params = generator.to_sql(filters)

    # The malicious input must not appear in the SQL text.
    assert malicious_city not in sql

    # The city must be represented by a placeholder.
    assert "city = ?" in sql

    # The original input must be passed separately as a parameter.
    assert params == (malicious_city,)

def test_pipeline_rejects_wrong_input_type():
    pipeline = QueryPipeline()

    try:
        pipeline.process(None)
        assert False, "Expected TypeError"
    except TypeError:
        pass

if __name__ == "__main__":

    # Initial Tests
    test_basic_query()
    test_price_range()
    test_bedroom_minimum()
    test_bathroom_count()
    test_amenity()
    test_amenity_negation()
    test_invalid_input_type()

    # Added Tests
    test_price_limits()
    test_price_range_variations()
    test_bedroom_variations()
    test_bathroom_variations()
    test_city_extraction()
    test_amenity_variations()
    test_amenity_negation_variations()
    test_price_in_millions()

    # Schema Validation Tests
    test_valid_schema()
    test_invalid_city()
    test_invalid_bedroom_count()
    test_reversed_price_range()
    test_negative_price()
    test_invalid_amenity()

    test_square_footage_validation()
    test_garage_spaces_validation()
    print("New schema validation tests passed!")

    # SQL Generator Tests
    test_sql_basic_query()
    test_sql_price_range()
    test_sql_room_ranges()
    test_sql_amenities()
    test_sql_injection_is_parameterized()
    test_sql_empty_filters()
    test_sql_rejects_unsafe_table_name()

    # Query Pipeline Tests
    test_full_pipeline()
    test_pipeline_rejects_invalid_city()
    test_pipeline_preserves_parameterization()
    test_pipeline_rejects_wrong_input_type()

    print("All Week 4 tests passed!")
