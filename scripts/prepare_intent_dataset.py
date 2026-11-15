
import pandas as pd
from pathlib import Path


# --------------------------------------------------
# 1. Define file paths and valid intent labels
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "intent_training_data_starter.csv"

OUTPUT_FILE = (
    PROJECT_ROOT / "data" / "processed" / "intent_training_data_clean.csv"
)

VALID_LABELS = [
    "browsing",
    "researching",
    "high_intent_inquiry"
]


# --------------------------------------------------
# 2. Load the dataset
# --------------------------------------------------

def load_dataset(file_path):

    print("\nLoading intent dataset...")

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    required_columns = [
        "query_id",
        "query",
        "intent_label"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    print(f"Loaded {len(df)} queries.")

    return df


# --------------------------------------------------
# 3. Clean missing values and text formatting
# --------------------------------------------------

def clean_dataset(df):

    print("\nCleaning dataset...")

    original_count = len(df)

    # Remove rows with missing queries or labels
    df = df.dropna(
        subset=["query", "intent_label"]
    ).copy()

    # Standardize query and label formatting
    df["query"] = df["query"].astype(str).str.strip()

    df["intent_label"] = (
        df["intent_label"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # Remove empty queries and labels
    df = df[
        (df["query"] != "") &
        (df["intent_label"] != "")
    ].copy()

    # Remove labels outside our three categories
    invalid_labels = ~df["intent_label"].isin(VALID_LABELS)

    if invalid_labels.any():
        print("\nInvalid labels found:")
        print(df.loc[invalid_labels, "intent_label"].value_counts())

        df = df[~invalid_labels].copy()

    # Remove duplicate queries (case-insensitive)
    duplicate_mask = df["query"].str.lower().duplicated()

    duplicates_removed = duplicate_mask.sum()

    df = df[~duplicate_mask].copy()

    df = df.reset_index(drop=True)

    removed_count = original_count - len(df)

    print(f"Original queries: {original_count}")
    print(f"Removed queries: {removed_count}")
    print(f"Duplicates removed: {duplicates_removed}")
    print(f"Remaining queries: {len(df)}")

    return df


# --------------------------------------------------
# 4. Validate label distribution
# --------------------------------------------------

def validate_labels(df):

    print("\nValidating intent labels...")

    distribution = df["intent_label"].value_counts()

    print("\nIntent distribution:")
    print(distribution)

    print("\nIntent percentages:")
    print(
        (distribution / len(df) * 100).round(2)
    )

    missing_labels = [
        label for label in VALID_LABELS
        if label not in distribution.index
    ]

    if missing_labels:
        raise ValueError(
            f"Missing intent categories: {missing_labels}"
        )

    if len(df) < 30:
        raise ValueError(
            "Not enough valid queries remaining."
        )

    print("\nAll three intent categories are represented.")


# --------------------------------------------------
# 5. Save cleaned dataset
# --------------------------------------------------

def save_dataset(df, file_path):

    df.to_csv(
        file_path,
        index=False,
        encoding="utf-8"
    )

    print(f"\nCleaned dataset saved to:\n{file_path}")


# --------------------------------------------------
# 6. Main execution
# --------------------------------------------------

def main():

    print("=" * 50)
    print("REAL ESTATE QUERY INTENT DATA PREPARATION")
    print("=" * 50)

    df = load_dataset(INPUT_FILE)

    df = clean_dataset(df)

    validate_labels(df)

    save_dataset(df, OUTPUT_FILE)

    print("\nDataset preparation completed successfully!")


if __name__ == "__main__":
    main()
