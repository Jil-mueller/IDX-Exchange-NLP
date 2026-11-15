
from pathlib import Path

from query_parse import QueryParser
from query_intent_classifier import QueryIntentClassifier


# --------------------------------------------------
# 1. Define model location
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_FILE = (
    PROJECT_ROOT / "data" / "models"
    / "query_intent_classifier.pkl"
)


# --------------------------------------------------
# 2. Combined query understanding class
# --------------------------------------------------

class QueryUnderstanding:

    def __init__(self):

        # Initialize existing Week 4 parser
        self.parser = QueryParser()

        # Load trained Week 7 intent classifier
        if not MODEL_FILE.exists():
            raise FileNotFoundError(
                f"Intent classifier model not found: {MODEL_FILE}"
            )

        self.classifier = QueryIntentClassifier.load(MODEL_FILE)

    # ----------------------------------------------
    # Process a natural-language search query
    # ----------------------------------------------

    def understand(self, query):

        if not isinstance(query, str) or not query.strip():
            raise ValueError(
                "Query must be a nonempty string."
            )

        # Step 1: Extract structured property filters
        filters = self.parser.parse(query)

        # Step 2: Predict language-based search intent
        intent = self.classifier.predict(query)

        # Step 3: Combine both outputs
        result = {
            "query": query,
            "intent": {
                "label": str(intent["intent"]),
                "confidence": intent["confidence"],
                "uncertain": intent["uncertain"]
            },
            "filters": filters
        }

        return result


# --------------------------------------------------
# 3. Example execution
# --------------------------------------------------

def main():

    understanding = QueryUnderstanding()

    test_queries = [
        "Show me homes in San Diego",
        "Which areas in San Diego have low property taxes?",
        "Find move-in ready homes in Irvine under 900k"
    ]

    for query in test_queries:

        result = understanding.understand(query)

        print("\n" + "=" * 60)
        print("QUERY:", result["query"])

        print("\nPREDICTED INTENT:")
        print(result["intent"])

        print("\nEXTRACTED PROPERTY FILTERS:")
        print(result["filters"])


if __name__ == "__main__":
    main()
