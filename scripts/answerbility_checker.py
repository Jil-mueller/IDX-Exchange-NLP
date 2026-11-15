
import re

from query_understanding import QueryUnderstanding
from schema_validation import SchemaValidator
from sql_generation import SQLGenerator


class AnswerabilityChecker:
    """Check whether a real-estate query can be processed and answered."""

    PROPERTY_TERMS = [
        "home", "homes", "house", "houses",
        "property", "properties",
        "real estate", "listing", "listings",
        "condo", "condos", "townhouse", "townhome",
        "bed", "beds", "bedroom", "bedrooms",
        "bath", "baths", "bathroom", "bathrooms",
        "garage", "pool", "fireplace", "basement",
        "patio", "balcony", "waterfront",
        "square feet", "sqft"
    ]

    SUPPORTED_INTENTS = {
        "browsing",
        "high_intent_inquiry",
        "researching"
    }

    def __init__(self):
        self.query_understanding = QueryUnderstanding()
        self.validator = SchemaValidator()
        self.sql_generator = SQLGenerator()

    def check_pre_query(self, query):
        """Check a query before sending it to the database."""

        if not isinstance(query, str) or not query.strip():
            return {
                "answerable": False,
                "status": "not_answerable",
                "message": "Please enter a nonempty search query.",
                "reasons": ["The query is empty or invalid."]
            }

        # Parse the query and predict its intent.
        try:
            understanding = self.query_understanding.understand(query)
        except Exception as error:
            return {
                "answerable": False,
                "status": "not_answerable",
                "message": "The query could not be processed.",
                "reasons": [str(error)]
            }

        filters = understanding["filters"]
        intent = understanding["intent"]

        reasons = []
        warnings = []

        # Check whether the query contains real-estate-related language.
        query_lower = query.lower()

        has_property_terms = any(
            re.search(r"\b" + re.escape(term) + r"\b", query_lower)
            for term in self.PROPERTY_TERMS
        )

        if not has_property_terms:
            reasons.append(
                "The query does not appear to describe a real-estate search."
            )

        # Check the predicted intent.
        if intent["label"] not in self.SUPPORTED_INTENTS:
            reasons.append(
                "The predicted query intent is not supported."
            )

        if intent["uncertain"]:
            warnings.append(
                "The intent classifier is uncertain about this query."
            )

        # Validate filter values.
        is_valid, validation_errors = self.validator.validate(filters)

        if not is_valid:
            reasons.extend(validation_errors)

        # Check whether the SQL generator supports the extracted filters.
        try:
            self.sql_generator.to_sql(filters)
        except ValueError as error:
            reasons.append(str(error))

        answerable = len(reasons) == 0

        if answerable:
            message = (
                "This query appears answerable and can proceed "
                "to the database search."
            )
        else:
            message = (
                "This query cannot be processed yet. "
                "Please review the following issues."
            )

        return {
            "answerable": answerable,
            "status": (
                "answerable" if answerable else "not_answerable"
            ),
            "message": message,
            "query": query,
            "intent": intent,
            "filters": filters,
            "reasons": reasons,
            "warnings": warnings
        }

    def check_post_query(self, results):
        """Explain whether a completed database search found listings."""

        if results is None:
            return {
                "answerable": False,
                "status": "not_checked",
                "message": "No database results were provided."
            }

        # Support pandas DataFrames and ordinary lists.
        if hasattr(results, "empty"):
            result_count = len(results)
        else:
            try:
                result_count = len(results)
            except TypeError:
                return {
                    "answerable": False,
                    "status": "not_checked",
                    "message": "The search results have an unsupported format."
                }

        if result_count == 0:
            return {
                "answerable": False,
                "status": "no_results",
                "result_count": 0,
                "message": (
                    "Your search was processed successfully, "
                    "but no listings matched your criteria. "
                    "Try broadening your search filters."
                )
            }

        return {
            "answerable": True,
            "status": "results_found",
            "result_count": result_count,
            "message": (
                f"Your search was successful. "
                f"Found {result_count} matching listings."
            )
        }


if __name__ == "__main__":

    checker = AnswerabilityChecker()

    test_queries = [
        "Show me homes in San Diego",
        "Find 3 bedroom houses with a pool",
        "Find homes with more than 2000 square feet",
        "What is the weather in San Diego?"
    ]

    print("\nPRE-QUERY ANSWERABILITY TESTS")
    print("=" * 50)

    for query in test_queries:
        result = checker.check_pre_query(query)

        print("\nQUERY:", query)
        print("ANSWERABLE:", result["answerable"])
        print("MESSAGE:", result["message"])

        if result.get("reasons"):
            print("REASONS:", result["reasons"])

        if result.get("warnings"):
            print("WARNINGS:", result["warnings"])

    print("\nPOST-QUERY ANSWERABILITY TESTS")
    print("=" * 50)

    # Simulate a successful search with three results.
    successful_results = [
        {"listing_id": 1},
        {"listing_id": 2},
        {"listing_id": 3}
    ]

    print("\nSuccessful search:")
    print(checker.check_post_query(successful_results))

    # Simulate a search with no matching listings.
    empty_results = []

    print("\nEmpty search:")
    print(checker.check_post_query(empty_results))

    print("\nADDITIONAL EDGE-CASE TESTS")
    print("=" * 50)

    # Test an empty query.
    empty_query_result = checker.check_pre_query("")
    print("\nEmpty query:")
    print(empty_query_result)

    # Test an invalid bedroom count.
    invalid_query_result = checker.check_pre_query(
        "Find 100 bedroom homes in San Diego"
    )
    print("\nInvalid bedroom count:")
    print(invalid_query_result)

    # Test an empty pandas DataFrame.
    import pandas as pd

    empty_dataframe = pd.DataFrame(columns=["listing_id"])

    print("\nEmpty DataFrame:")
    print(checker.check_post_query(empty_dataframe))
