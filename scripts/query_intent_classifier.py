
import joblib

from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


class QueryIntentClassifier:

    def __init__(self, confidence_threshold=0.60):

        self.confidence_threshold = confidence_threshold

        # Combine text vectorization and classification
        self.pipeline = Pipeline([
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=1000,
                    ngram_range=(1, 2),
                    lowercase=True,
                    strip_accents="unicode"
                )
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    random_state=42
                )
            )
        ])

        self.is_trained = False

    # ----------------------------------------------
    # Train the classifier
    # ----------------------------------------------

    def train(self, queries, labels):

        if len(queries) != len(labels):
            raise ValueError(
                "Queries and labels must have equal lengths."
            )

        if len(queries) == 0:
            raise ValueError("Training data cannot be empty.")

        self.pipeline.fit(queries, labels)

        self.is_trained = True

        print("Query intent classifier trained successfully.")

    # ----------------------------------------------
    # Predict intent for one query
    # ----------------------------------------------

    def predict(self, query):

        if not self.is_trained:
            raise RuntimeError(
                "Classifier must be trained before prediction."
            )

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a nonempty string.")

        # Get probability for each intent category
        probabilities = self.pipeline.predict_proba([query])[0]

        # Get the model's learned class labels
        labels = self.pipeline.classes_

        # Find the category with the highest probability
        best_index = probabilities.argmax()

        predicted_intent = labels[best_index]

        confidence = float(probabilities[best_index])

        # Identify uncertain predictions
        uncertain = confidence < self.confidence_threshold

        return {
            "intent": predicted_intent,
            "confidence": round(confidence, 4),
            "uncertain": uncertain,
            "probabilities": {
                label: round(float(probability), 4)
                for label, probability in zip(labels, probabilities)
            }
        }

    # ----------------------------------------------
    # Save trained classifier
    # ----------------------------------------------

    def save(self, file_path):

        if not self.is_trained:
            raise RuntimeError(
                "Cannot save an untrained classifier."
            )

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(
            {
                "pipeline": self.pipeline,
                "confidence_threshold": self.confidence_threshold
            },
            file_path
        )

        print(f"Classifier saved to: {file_path}")

    # ----------------------------------------------
    # Load previously trained classifier
    # ----------------------------------------------

    @classmethod
    def load(cls, file_path):

        saved_model = joblib.load(file_path)

        classifier = cls(
            confidence_threshold=saved_model["confidence_threshold"]
        )

        classifier.pipeline = saved_model["pipeline"]
        classifier.is_trained = True

        return classifier
