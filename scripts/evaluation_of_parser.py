
from scripts.query_parse import QueryParser
import pandas as pd
from pathlib import Path
import ast

def load_sample_queries():
    project_root = Path(__file__).resolve().parent.parent
    csv_path = project_root / "data" / "processed" / "sample_queries.csv"

    df = pd.read_csv(csv_path)

    print(f"Loaded {len(df)} queries")
    print("Columns:", df.columns.tolist())
    print(df.head())

    return df

# Tests cases seperate from dataset (tested before dataset)

TEST_CASES = [
    {
        "query": "3 bed under 700k in Irvine",
        "expected": {
            "beds": 3,
            "price_max": 700000,
            "city": "irvine",
        },
    },
    {
        "query": "homes between $400k and $700k",
        "expected": {
            "price_min": 400000,
            "price_max": 700000,
        },
    },
    {
        "query": "at least 3 bedrooms",
        "expected": {"beds_min": 3},
    },
    {
        "query": "2 bathrooms",
        "expected": {"baths": 2},
    },
    {
        "query": "homes with a pool",
        "expected": {"amenities": ["pool"]},
    },
    {
        "query": "homes without a pool",
        "expected": {"exclude_amenities": ["pool"]},
    },
    {
        "query": "homes in San Diego",
        "expected": {"city": "san diego"},
    },
    {
        "query": "under 1.2m",
        "expected": {"price_max": 1200000},
    },
]


def evaluate_parser(test_cases):
    parser = QueryParser()
    total_checks = 0
    correct_checks = 0
    failures = []

    for case in test_cases:
        query = case["query"]
        expected = case["expected"]
        actual = parser.parse(query)

        for field, expected_value in expected.items():
            total_checks += 1
            actual_value = actual.get(field)

            # Compare amenity lists without depending on their order.
            if field in ("amenities", "exclude_amenities"):
                matches = set(actual_value or []) == set(expected_value)
            elif field == "city":
                matches = (
                    actual_value.casefold() if actual_value else None
                ) == expected_value.casefold()
            else:
                matches = actual_value == expected_value

            if matches:
                correct_checks += 1
            else:
                failures.append({
                    "query": query,
                    "field": field,
                    "expected": expected_value,
                    "actual": actual_value,
                })

    accuracy = (
        correct_checks / total_checks * 100
        if total_checks else 0
    )

    print(f"Queries evaluated: {len(test_cases)}")
    print(f"Individual filter checks: {total_checks}")
    print(f"Correct filter checks: {correct_checks}")
    print(f"Filter-level accuracy: {accuracy:.1f}%")
    print(f"Failed checks: {len(failures)}")

    for failure in failures:
        print(
            f"\nQuery: {failure['query']}"
            f"\n  Field: {failure['field']}"
            f"\n  Expected: {failure['expected']}"
            f"\n  Actual: {failure['actual']}"
        )

    return accuracy, failures

def evaluate_sample_dataset(df):
    parser = QueryParser()
    results = []

    for _, row in df.iterrows():
        query = str(row["query"])
        filters = parser.parse(query)

        recognized = {}

        for key, value in filters.items():
            if value is None:
                continue

            if isinstance(value, bool):
                if value:
                    recognized[key] = value
            elif value != [] and value != "":
                recognized[key] = value

        results.append({
            "query": query,
            "intent": row["intent"],
            "recognized_filters": recognized,
            "has_recognized_filters": bool(recognized),
        })

    results_df = pd.DataFrame(results)

    total = len(results_df)
    covered = int(results_df["has_recognized_filters"].sum())

    print("\n--- Week 1 Dataset Evaluation ---")
    print(f"Total queries: {total}")
    print(f"Queries with recognized filters: {covered}")

    if total:
        print(f"Filter coverage: {covered / total * 100:.1f}%")

    print("\nCoverage by intent:")
    print(
        results_df.groupby("intent")["has_recognized_filters"]
        .agg(["sum", "count"])
        .to_string()
    )

    project_root = Path(__file__).resolve().parent.parent
    output_path = (
        project_root
        / "data"
        / "processed"
        / "parser_evaluation_results.csv"
    )
    results_df.to_csv(output_path, index=False)
    print(f"\nDetailed results saved to: {output_path}")

    return results_df


def evaluate_expected_filters(expected_file):
    """Compare expected filters with the parser's actual output."""
    import pandas as pd
    from scripts.query_parse import QueryParser

    expected_df = pd.read_csv(expected_file)
    parser = QueryParser()

    total = 0
    correct = 0
    results = []

    for _, row in expected_df.iterrows():
        query = row["query"]
        expected = ast.literal_eval(row["expected_filters"])
        actual = parser.parse(query)

        # Compare only the expected fields for this query.
        mismatches = {}
        for key, expected_value in expected.items():
            actual_value = actual.get(key)

            if actual_value != expected_value:
                mismatches[key] = {
                    "expected": expected_value,
                    "actual": actual_value
                }

        total += len(expected)
        correct += len(expected) - len(mismatches)

        results.append({
            "query": query,
            "expected_filters": str(expected),
            "actual_filters": str(actual),
            "mismatches": str(mismatches),
            "correct": len(mismatches) == 0
        })

    accuracy = (correct / total * 100) if total else 0

    results_df = pd.DataFrame(results)
    results_df.to_csv(
        "data/processed/expected_filter_evaluation.csv",
        index=False
    )

    print(f"Queries evaluated: {len(expected_df)}")
    print(f"Individual filter checks: {total}")
    print(f"Correct filter checks: {correct}")
    print(f"Filter-level accuracy: {accuracy:.1f}%")
    print("Results saved to data/processed/expected_filter_evaluation.csv")


if __name__ == "__main__":
    evaluate_parser(TEST_CASES)

    sample_df = load_sample_queries()
    evaluate_sample_dataset(sample_df)
