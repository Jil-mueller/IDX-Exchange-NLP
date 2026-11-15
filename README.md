# IDX Exchange NLP

## Project Overview

This project focuses on developing Natural Language Processing (NLP) tools for real-estate listing data and search queries.

The goal is to make real-estate information easier to understand and search by extracting meaningful information from property descriptions and identifying the intent behind natural-language search queries.

The project combines rule-based parsing, signal extraction, and machine learning to process real-estate data.

## Project Objectives

- Extract structured information from real-estate listing descriptions.
- Identify property features, amenities, condition keywords, financing terms, and location-related signals.
- Interpret natural-language real-estate search queries.
- Classify search queries into different language-based intent categories.
- Integrate query intent classification with structured property filter extraction.

## Technologies Used

- **Python** – Primary programming language.
- **Pandas** – Data processing and manipulation.
- **NumPy** – Numerical operations.
- **Scikit-learn** – Machine learning and text classification.
- **TF-IDF** – Text feature extraction.
- **Logistic Regression** – Query intent classification.
- **Joblib** – Saving and loading trained models.
- **Git and GitHub** – Version control.

## Project Structure

```text
IDX-Internship/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── models/
│
├── scripts/
│   ├── query_parse.py
│   ├── query_intent_classifier.py
│   ├── query_understanding.py
│   ├── prepare_intent_dataset.py
│   ├── evaluate_intent_classifier.py
│   ├── signal_extraction.py
│   └── ...
│
├── tests/
│   ├── tests_week4.py
│   ├── test_query_understanding.py
│   └── ...
│
└── README.md
```

*Note: The structure above highlights the main project components. Additional scripts, datasets, and tests may be present.*

## Project Components

### 1. Real-Estate Query Parsing

A rule-based query parser processes natural-language property searches and extracts structured property filters.

Supported filters include:

- Number of bedrooms and bathrooms
- Minimum and maximum price
- City
- Property type
- Square footage
- Amenities and excluded amenities
- Garage spaces
- Property condition
- Property views
- HOA restrictions
- Investment-related keywords

For example:

**Input:**
`3 bed under 700k in Irvine`

**Extracted filters:**

- Bedrooms: 3
- Maximum price: $700,000
- City: Irvine

### 2. Real-Estate Listing Signal Extraction

The signal extraction component processes property listing information and identifies meaningful characteristics from listing descriptions.

Extracted signal categories include:

- **Amenities:** Pool, garage, fireplace, patio, gym, and other property features.
- **Condition:** Updated, renovated, remodeled, move-in ready, and fixer-upper.
- **Financing:** FHA, VA, cash-only, seller financing, and assumable financing.
- **Location:** Waterfront, lakefront, gated communities, golf communities, and proximity-related features.
- **Keywords:** Additional descriptive terms found in listing remarks.

The extraction process uses predefined taxonomies, keyword matching, and aliases to standardize different descriptions of similar property features.

#### Signal Extraction Coverage

An analysis of 55,212 property listings produced the following coverage:

| Signal category | Listings with signals | Coverage |
|---|---:|---:|
| Amenities | 48,623 | 88.1% |
| Condition | 29,733 | 53.9% |
| Financing | 1,132 | 2.1% |
| Location | 35,280 | 63.9% |
| Keywords | 40,241 | 72.9% |

These results show that signal frequency varies significantly by category, with amenities appearing most frequently and financing terms appearing relatively rarely.

### 3. Query Intent Classification

A machine-learning classifier identifies the language-based intent expressed in real-estate search queries.

Three intent categories are used:

| Intent | Description |
|---|---|
| `browsing` | General searches for properties or available homes. |
| `researching` | Queries seeking information about locations, property characteristics, or real-estate considerations. |
| `high_intent_inquiry` | More specific searches expressing a focused property inquiry. |

The classifier uses:

- TF-IDF vectorization with unigrams and bigrams.
- Logistic Regression for multi-class classification.
- Prediction probabilities to estimate confidence.
- A confidence threshold of 0.60 to flag uncertain predictions.

#### Training Dataset

A dataset of 210 labeled example queries was created, with an equal number of examples in each category.

| Category | Number of queries |
|---|---:|
| Browsing | 70 |
| Researching | 70 |
| High-intent inquiry | 70 |
| **Total** | **210** |

The dataset was split into training and testing sets using an 80/20 stratified split with a random state of 42.

#### Model Evaluation

The classifier achieved the following results:

| Evaluation metric | Result |
|---|---:|
| Test queries | 42 |
| Correct predictions | 41 |
| Incorrect predictions | 1 |
| Accuracy | **97.62%** |

The model exceeded the initial target of 80% held-out accuracy on this dataset.

These results should be interpreted cautiously because the training and testing examples were constructed for this project rather than independently collected from actual users.

### 4. Query Understanding Integration

The query understanding component combines the Week 4 property query parser with the Week 7 intent classifier.

Both components independently process the same natural-language query.

The integration returns:

- The original search query.
- The predicted intent category.
- The prediction confidence.
- An uncertainty indicator.
- The structured property filters extracted by the query parser.

For example:

**Input:**

`Find move-in ready homes in Irvine under 900k`

**Combined output:**

- Predicted intent: `high_intent_inquiry`
- Confidence: Approximately 73%
- Condition: `move_in_ready`
- Maximum price: $900,000

This integration allows the system to interpret both what property characteristics a user is searching for and what type of information their query appears to seek.

## Running the Project

### Requirements

Python and the required project dependencies must be installed.

The main machine-learning dependencies include:

```bash
pip install pandas numpy scikit-learn joblib
```

### Prepare the Intent Dataset

From the project root:

```bash
python scripts/prepare_intent_dataset.py
```

### Evaluate and Train the Intent Classifier

```bash
python scripts/evaluate_intent_classifier.py
```

This evaluates the classifier and saves the final trained model to:

`data/models/query_intent_classifier.pkl`

### Run the Integrated Query Understanding System

```bash
python scripts/query_understanding.py
```

This runs example queries through both the intent classifier and the property query parser.

### Run Integration Tests

```bash
python -m unittest tests.test_query_understanding -v
```

## Limitations and Future Improvements

- The intent classification dataset consists of constructed examples, so performance on independently collected real-world queries has not yet been established.
- Intent classification is based on the language of a query and does not establish actual buyer behavior or purchasing likelihood.
- More diverse, independently collected search queries would help evaluate how well the classifier generalizes.
- Confidence scores are model probability estimates and should not be interpreted as guaranteed prediction accuracy.
- Signal extraction can be improved by expanding keyword coverage, refining aliases, and evaluating extraction accuracy across more labeled examples.
- Financing-related signals occur relatively infrequently, which limits their coverage in listing descriptions.

## Conclusion

This project develops a collection of NLP tools for understanding real-estate listings and natural-language property searches.

By combining structured property filter extraction, listing signal extraction, and machine-learning-based intent classification, the system provides a foundation for making real-estate search information more structured and interpretable.

Future work can focus on improving extraction accuracy, expanding training data, and validating model performance using independently collected real-world search queries.
