from pathlib import Path
import unittest

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))

from query_understanding import QueryUnderstanding


class TestQueryUnderstanding(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.understanding = QueryUnderstanding()

    def test_browsing_query(self):
        result = self.understanding.understand(
            "Show me homes in San Diego"
        )

        self.assertEqual(result["intent"]["label"], "browsing")
        self.assertIn("city", result["filters"])
        self.assertEqual(result["filters"]["city"], "san diego")

    def test_researching_query(self):
        result = self.understanding.understand(
            "Which areas in San Diego have low property taxes?"
        )

        self.assertEqual(result["intent"]["label"], "researching")

    def test_high_intent_query(self):
        result = self.understanding.understand(
            "Find move-in ready homes in Irvine under 900k"
        )

        self.assertEqual(
            result["intent"]["label"],
            "high_intent_inquiry"
        )
        self.assertEqual(result["filters"]["price_max"], 900000)
        self.assertIn(
            "move_in_ready",
            result["filters"]["condition"]
        )

    def test_confidence_score(self):
        result = self.understanding.understand(
            "Show me homes in San Diego"
        )

        self.assertGreaterEqual(result["intent"]["confidence"], 0)
        self.assertLessEqual(result["intent"]["confidence"], 1)

    def test_original_query_is_preserved(self):
        query = "Show me homes in San Diego"
        result = self.understanding.understand(query)

        self.assertEqual(result["query"], query)


if __name__ == "__main__":
    unittest.main()
