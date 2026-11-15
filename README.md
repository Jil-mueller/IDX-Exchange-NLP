# IDX Exchange NLP

## Project Overview

This project focuses on developing Natural Language Processing (NLP) tools for real-estate listing data and search queries.

The goal is to make real-estate information easier to understand and search by extracting meaningful information from property descriptions, identifying the intent behind natural-language search queries, generating concise listing summaries, and determining whether search queries can be answered.

The project combines rule-based parsing, signal extraction, machine learning, and text summarization to process real-estate data.

## Project Objectives

- Extract structured information from real-estate listing descriptions.
- Identify property features, amenities, condition keywords, financing terms, and location-related signals.
- Interpret natural-language real-estate search queries.
- Classify search queries into different language-based intent categories.
- Integrate query intent classification with structured property filter extraction.
- Generate concise summaries of real-estate listings.
- Evaluate summary quality using ROUGE metrics and human evaluation.
- Determine whether queries can be processed and explain why searches may not return results.

## Technologies Used

- **Python** – Primary programming language.
- **Pandas** – Data processing and manipulation.
- **NumPy** – Numerical operations.
- **Scikit-learn** – Machine learning and text classification.
- **TF-IDF** – Text feature extraction.
- **Logistic Regression** – Query intent classification.
- **Joblib** – Saving and loading trained models.
- **NLTK** – Sentence processing for extractive summarization.
- **ROUGE** – Evaluation of generated summaries.
- **MySQL** – Real-estate listing data storage.
- **Git and GitHub** – Version control.

## Project Structure

```text
IDX-Internship/
|
├── data/
│   ├── raw/
│   ├── processed/
│   └── models/
│
├── scripts/
│   ├── data_loading.py
│   ├── entity_extractor.py
│   ├── signal_extraction.py
│   ├── evaluate_signals.py
│   ├── query_parse.py
│   ├── query_intent_classifier.py
│   ├── query_understanding.py
│   ├── schema_validation.py
│   ├── sql_generation.py
│   ├── listing_summarizer.py
│   ├── evaluate_summaries.py
│   ├── prepare_human_evaluation.py
│   ├── answerbility_checker.py
│   └── ...
│
├── tests/
│   └── ...
│
└── README.md
```

*Note: The structure highlights the main project components. Additional scripts, datasets, evaluation files, and models may be present.*

# Project Components

## 1. Real-Estate Query Parsing

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

## 2. Real-Estate Listing Signal Extraction

The signal extraction component processes property listing information and identifies meaningful characteristics from listing descriptions.

Extracted signal categories include:

- **Amenities:** Pool, garage, fireplace, patio, gym, and other property features.
- **Condition:** Updated, renovated, remodeled, move-in ready, and fixer-upper.
- **Financing:** FHA, VA, cash-only, seller financing, and assumable financing.
- **Location:** Waterfront, lakefront, gated communities, golf communities, and proximity-related features.
- **Keywords:** Additional descriptive terms found in listing remarks.

The extraction process uses predefined taxonomies, keyword matching, and aliases to standardize different descriptions of similar property features.

### Signal Extraction Coverage

An analysis of 55,212 property listings produced the following coverage:

| Signal category | Listings with signals | Coverage |
|---|---:|---:|
| Amenities | 48,623 | 88.1% |
| Condition | 29,733 | 53.9% |
| Financing | 1,132 | 2.1% |
| Location | 35,280 | 63.9% |
| Keywords | 40,241 | 72.9% |

These results show that signal frequency varies significantly by category, with amenities appearing most frequently and financing terms appearing relatively rarely.

## 3. Query Intent Classification

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

### Training Dataset

A dataset of 210 labeled example queries was created, with an equal number of examples in each category.

| Category | Number of queries |
|---|---:|
| Browsing | 70 |
| Researching | 70 |
| High-intent inquiry | 70 |
| **Total** | **210** |

The dataset was split into training and testing sets using an 80/20 stratified split with a random state of 42.

### Model Evaluation

The classifier achieved the following results:

| Evaluation metric | Result |
|---|---:|
| Test queries | 42 |
| Correct predictions | 41 |
| Incorrect predictions | 1 |
| Accuracy | **97.62%** |

The model exceeded the initial target of 80% held-out accuracy on this dataset.

These results should be interpreted cautiously because the training and testing examples were constructed for this project rather than independently collected from actual users.

## 4. Query Understanding Integration

The query understanding component combines the property query parser with the intent classifier.

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

## 5. Real-Estate Listing Summarization

The listing summarization component generates concise, extractive summaries of property listings.

The `ListingSummarizer` processes listing information using structured property fields and descriptive listing remarks.

The summarizer incorporates:

- Property characteristics, including bedrooms and bathrooms.
- Listing address and city.
- Property price.
- Important amenities and features identified using the signal taxonomy.
- Relevant descriptive sentences selected from the original listing remarks.

The goal is to produce approximately 2–3 sentence summaries that communicate important property information without requiring users to read the entire listing description.

### Summary Generation

The summarization workflow:

1. Loads the processed listing dataset.
2. Loads the signal taxonomy.
3. Processes individual property listings.
4. Identifies relevant property features and descriptive sentences.
5. Generates an extractive summary.
6. Saves the generated summaries for evaluation.

A sample of 1,000 listings was processed, and summaries were generated for all 1,000 records.

### ROUGE Evaluation

Generated summaries were evaluated using ROUGE-1, ROUGE-2, and ROUGE-L.

The evaluation compares generated summaries against the original listing remarks.

| Evaluation metric | Average score |
|---|---:|
| ROUGE-1 | 0.3443 |
| ROUGE-2 | 0.2525 |
| ROUGE-L | 0.2827 |

The initial ROUGE-L target was greater than 0.40. The current result of 0.2827 falls below that target, indicating room for improvement.

An important limitation is that original listing remarks are being used as reference text rather than independently written reference summaries. Generated summaries also incorporate structured information, which may not appear in the original remarks. Therefore, these scores provide a preliminary measure of lexical overlap rather than a complete measure of summary quality.

### Human Evaluation

A separate human evaluation was prepared using 20 generated listing summaries.

The evaluation is designed to assess:

- **Accuracy:** Whether the summary correctly represents the original listing.
- **Coverage:** Whether important property information is included.
- **Readability:** Whether the summary is clear and easy to understand.
- **Overall quality:** The evaluator's overall assessment of the summary.

Teammate evaluations are being collected separately. Human evaluation results will be added once the ratings are available.

## 6. Query Answerability Checking

The answerability component determines whether a natural-language real-estate query can be processed and explains why a query may not be answerable.

The `AnswerabilityChecker` integrates:

- Query understanding.
- Schema validation.
- SQL filter support validation.
- Post-query result checking.

It contains two main components.

### Pre-Query Checking

Before a database search, the checker evaluates whether:

1. The query is nonempty and valid.
2. The query appears to relate to real-estate listings.
3. The predicted query intent is supported.
4. Extracted property filters pass schema validation.
5. The SQL generator supports the extracted filters.

If a query cannot be processed, the checker returns an explanation of the issue.

For example:

**Supported query:**

`Show me homes in San Diego`

The query passes the pre-query checks and can proceed to a database search.

**Unsupported filter:**

`Find homes with more than 2000 square feet`

The checker identifies that `sqft_min` is not currently supported by the SQL generator and explains why the query cannot proceed.

**Unrelated query:**

`What is the weather in San Diego?`

The checker identifies that the query does not appear to describe a real-estate search.

### Post-Query Checking

After a search is completed, the checker evaluates the returned results.

It distinguishes between:

- **Results found:** The search returned one or more listings.
- **No results:** The search was processed, but no listings matched the requested criteria.
- **Not checked:** No valid search results were provided.

For searches with no matching listings, the checker provides an explanation and suggests broadening the search criteria.

### Answerability Testing

The answerability component was tested using supported searches, unsupported filters, unrelated questions, invalid bedroom counts, empty queries, successful search results, and empty result sets.

The tests confirmed that the component correctly identifies queries that can proceed, rejects unsupported or invalid requests, and explains when searches return no listings.

The current implementation validates query answerability and evaluates supplied search results. It does not independently execute database searches.

# Running the Project

## Requirements

Python and the required project dependencies must be installed.

Install the primary dependencies using:

```bash
pip install pandas numpy scikit-learn joblib nltk rouge-score mysql-connector-python
```

Some workflows also require the MySQL database and its associated listing data to be available.

## Prepare the Intent Dataset

From the project root:

```bash
python scripts/prepare_intent_dataset.py
```

## Evaluate and Train the Intent Classifier

```bash
python scripts/evaluate_intent_classifier.py
```

This evaluates the classifier and saves the trained model to:

`data/models/query_intent_classifier.pkl`

## Run the Integrated Query Understanding System

```bash
python scripts/query_understanding.py
```

This runs example queries through both the intent classifier and the property query parser.

## Load Listing Data

Ensure the MySQL database is running and configured before executing:

```bash
python scripts/data_loading.py
```

This loads a sample of listing records into the processed data directory.

## Generate Listing Summaries

```bash
python scripts/listing_summarizer.py
```

This generates extractive summaries for the processed listing sample.

## Evaluate Listing Summaries

```bash
python scripts/evaluate_summaries.py
```

This calculates ROUGE-1, ROUGE-2, and ROUGE-L scores and saves individual evaluation results.

## Prepare Human Evaluation

```bash
python scripts/prepare_human_evaluation.py
```

This prepares the sample used for human evaluation of generated summaries.

## Run Answerability Checks

```bash
python scripts/answerbility_checker.py
```

This executes the pre-query and post-query answerability tests.

# Limitations and Future Improvements

- The intent classification dataset consists of constructed examples, so performance on independently collected real-world queries has not yet been established.
- Intent classification is based on the language of a query and does not establish actual buyer behavior or purchasing likelihood.
- More diverse, independently collected search queries would help evaluate how well the classifier generalizes.
- Confidence scores are model probability estimates and should not be interpreted as guaranteed prediction accuracy.
- Signal extraction can be improved by expanding keyword coverage, refining aliases, and evaluating extraction accuracy across more labeled examples.
- Financing-related signals occur relatively infrequently, which limits their coverage in listing descriptions.
- Listing summaries can be improved by reducing repetition, improving sentence selection, and incorporating more relevant property details.
- The current ROUGE-L score is below the initial target of 0.40.
- Human evaluation is needed to provide additional insight into summary accuracy, coverage, and readability.
- The answerability component currently validates query filters but does not independently execute database searches.
- Additional SQL filter support would allow more types of natural-language queries to be processed.

## Conclusion

This project develops a collection of NLP tools for understanding real-estate listings and natural-language property searches.

By combining structured property filter extraction, listing signal extraction, machine-learning-based intent classification, extractive summarization, and answerability checking, the system provides a foundation for making real-estate search information more structured and interpretable.

Future work can focus on improving extraction accuracy, expanding training data, improving summary quality, supporting additional search filters, and validating system performance using independently collected real-world data.