
import pandas as pd

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

from query_intent_classifier import QueryIntentClassifier


# --------------------------------------------------
# 1. Define file paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "intent_training_data_clean.csv"
)

MODEL_FILE = (
    PROJECT_ROOT / "data" / "models"
    / "query_intent_classifier.pkl"
)

RESULTS_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "intent_evaluation_results.csv"
)

CONFUSION_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "intent_confusion_matrix.csv"
)

VALID_LABELS = [
    "browsing",
    "researching",
    "high_intent_inquiry"
]


# --------------------------------------------------
# 2. Load cleaned dataset
# --------------------------------------------------

def load_dataset():

    print("\nLoading cleaned intent dataset...")

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    if df[["query", "intent_label"]].isna().any().any():
        raise ValueError("Dataset contains missing values.")

    if not set(df["intent_label"]).issubset(VALID_LABELS):
        raise ValueError("Dataset contains invalid labels.")

    if set(df["intent_label"]) != set(VALID_LABELS):
        raise ValueError("All three intent labels must be present.")

    print(f"Loaded {len(df)} queries.")

    return df


# --------------------------------------------------
# 3. Split dataset into training and testing sets
# --------------------------------------------------

def split_dataset(df):

    print("\nSplitting dataset...")

    X = df["query"]
    y = df["intent_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    print(f"Training queries: {len(X_train)}")
    print(f"Testing queries: {len(X_test)}")

    return X_train, X_test, y_train, y_test


# --------------------------------------------------
# 4. Train classifier using training data
# --------------------------------------------------

def train_classifier(X_train, y_train):

    print("\nTraining logistic regression classifier...")

    classifier = QueryIntentClassifier()

    classifier.train(
        X_train.tolist(),
        y_train.tolist()
    )

    return classifier


# --------------------------------------------------
# 5. Evaluate classifier
# --------------------------------------------------

def evaluate_classifier(classifier, X_test, y_test):

    print("\nEvaluating classifier...")

    predictions = classifier.pipeline.predict(
        X_test.tolist()
    )

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    print("\nAccuracy:")
    print(f"{accuracy:.2%}")

    print("\nClassification Report:")

    report = classification_report(
        y_test,
        predictions,
        labels=VALID_LABELS,
        zero_division=0
    )

    print(report)

    print("\nConfusion Matrix:")

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=VALID_LABELS
    )

    matrix_df = pd.DataFrame(
        matrix,
        index=VALID_LABELS,
        columns=VALID_LABELS
    )

    print(matrix_df)

    matrix_df.to_csv(CONFUSION_FILE)

    # Create detailed prediction results
    results = []

    for query, actual, predicted in zip(
        X_test,
        y_test,
        predictions
    ):

        prediction = classifier.predict(query)

        results.append({
            "query": query,
            "actual_intent": actual,
            "predicted_intent": predicted,
            "confidence": prediction["confidence"],
            "uncertain": prediction["uncertain"],
            "correct": actual == predicted
        })

    results_df = pd.DataFrame(results)

    results_df.to_csv(
        RESULTS_FILE,
        index=False
    )

    print(f"\nEvaluation results saved to: {RESULTS_FILE}")
    print(f"Confusion matrix saved to: {CONFUSION_FILE}")

    uncertain_count = results_df["uncertain"].sum()

    print(
        f"\nUncertain predictions: {uncertain_count}"
        f" / {len(results_df)}"
    )

    return accuracy


# --------------------------------------------------
# 6. Retrain on all available data and save model
# --------------------------------------------------

def save_final_model(df):

    print("\nTraining final model on all 210 queries...")

    final_classifier = QueryIntentClassifier()

    final_classifier.train(
        df["query"].tolist(),
        df["intent_label"].tolist()
    )

    final_classifier.save(MODEL_FILE)

    print("Final classifier saved successfully.")


# --------------------------------------------------
# 7. Main execution
# --------------------------------------------------

def main():

    print("=" * 55)
    print("REAL ESTATE QUERY INTENT CLASSIFIER EVALUATION")
    print("=" * 55)

    df = load_dataset()

    X_train, X_test, y_train, y_test = split_dataset(df)

    classifier = train_classifier(
        X_train,
        y_train
    )

    accuracy = evaluate_classifier(
        classifier,
        X_test,
        y_test
    )

    save_final_model(df)

    print("\n" + "=" * 55)
    print("EVALUATION COMPLETED")
    print(f"Test accuracy: {accuracy:.2%}")
    print("=" * 55)


if __name__ == "__main__":
    main()
