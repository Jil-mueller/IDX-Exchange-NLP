
import os
import re
import time
import pandas as pd

from scripts.semantic_search import (
    SemanticSearcher,
    BM25Searcher,
    load_listings,
)


QUERIES = [
    "homes with swimming pools",
    "spacious homes with large backyards",
    "houses with attached garages",
    "homes with updated kitchens",
    "properties with waterfront views",
    "homes with fireplaces",
    "houses with large lots",
    "homes with open floor plans",
    "properties with mountain views",
    "homes with private swimming pools",
    "four bedroom homes",
    "three bedroom two bathroom houses",
    "homes with multiple bathrooms",
    "large family homes",
    "small starter homes",
    "single story homes",
    "two story homes",
    "homes with master suites",
    "homes with guest bedrooms",
    "properties with bonus rooms",
    "homes with renovated bathrooms",
    "houses with modern kitchens",
    "homes with stainless steel appliances",
    "properties with granite countertops",
    "homes with hardwood floors",
    "houses with vaulted ceilings",
    "homes with spacious living rooms",
    "properties with formal dining rooms",
    "homes with laundry rooms",
    "houses with walk in closets",
    "homes with covered patios",
    "properties with outdoor entertaining areas",
    "homes with landscaped gardens",
    "houses with fenced yards",
    "homes with RV parking",
    "properties with oversized garages",
    "homes in gated communities",
    "houses on quiet cul de sacs",
    "homes near shopping centers",
    "properties with city views",
    "homes with recently updated interiors",
    "move in ready houses",
    "homes with renovation potential",
    "properties with separate guest quarters",
    "homes with spacious driveways",
    "houses with lots of natural light",
    "homes with energy efficient features",
    "luxury homes with premium finishes",
    "homes suitable for entertaining guests",
    "properties with flexible living spaces",
]


STOPWORDS = {
    "a", "an", "and", "are", "at", "for", "from", "in",
    "into", "near", "of", "on", "or", "the", "to", "with",
    "home", "homes", "house", "houses", "property", "properties",
    "featuring", "that", "has", "have", "with",
}

# Normalize common alternative ways of describing features.
ALIASES = {
    "pools": "pool",
    "swimming": "pool",
    "backyards": "yard",
    "backyard": "yard",
    "yards": "yard",
    "garages": "garage",
    "bedrooms": "bedroom",
    "baths": "bathroom",
    "bathrooms": "bathroom",
    "kitchens": "kitchen",
    "updated": "update",
    "renovated": "renovate",
    "renovations": "renovation",
    "patios": "patio",
    "gardens": "garden",
    "lots": "lot",
    "views": "view",
    "floors": "floor",
    "appliances": "appliance",
    "closets": "closet",
    "rooms": "room",
    "driveways": "driveway",
    "communities": "community",
    "suites": "suite",
    "quarters": "quarter",
    "finishes": "finish",
    "features": "feature",
    "spaces": "space",
    "stories": "story",
    "two": "2",
    "three": "3",
    "four": "4",
}


def normalize(text):
    tokens = re.findall(r"[a-z0-9]+", str(text).lower())
    return [
        ALIASES.get(token, token)
        for token in tokens
    ]


def query_concepts(query):
    return {
        token
        for token in normalize(query)
        if token not in STOPWORDS and len(token) > 1
    }


def estimate_relevance(query, remarks):
    """
    Transparent keyword-based estimate, NOT human-verified relevance.

    A result is estimated relevant when at least half of the
    query's meaningful terms appear in the listing description.
    """
    concepts = query_concepts(query)

    if not concepts:
        return 0

    listing_terms = set(normalize(remarks))
    matched = concepts.intersection(listing_terms)

    coverage = len(matched) / len(concepts)
    return int(coverage >= 0.5)


def main():
    listing_ids, remarks = load_listings()

    print(f"Loaded {len(remarks)} listings.")
    print(f"Evaluating {len(QUERIES)} queries.")

    semantic = SemanticSearcher()
    semantic.build_index(remarks)

    bm25 = BM25Searcher()
    bm25.build_index(remarks)

    rows = []

    for query_number, query in enumerate(QUERIES, start=1):
        print(f"Query {query_number}/{len(QUERIES)}: {query}")

        start = time.perf_counter()
        semantic_results = semantic.search(query, top_k=5)
        semantic_ms = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        bm25_results = bm25.search(query, top_k=5)
        bm25_ms = (time.perf_counter() - start) * 1000

        for method, results, latency in [
            ("semantic", semantic_results, semantic_ms),
            ("BM25", bm25_results, bm25_ms),
        ]:
            relevant_count = 0

            for rank, result in enumerate(results, start=1):
                remark, score = result
                relevant = estimate_relevance(query, remark)
                relevant_count += relevant

                rows.append({
                    "query_number": query_number,
                    "query": query,
                    "method": method,
                    "rank": rank,
                    "score": float(score),
                    "remarks": remark,
                    "estimated_relevant": relevant,
                    "search_latency_ms": latency,
                })

    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)

    results_df = pd.DataFrame(rows)

    results_path = os.path.join(
        output_dir, "relevance_judgments.csv"
    )
    results_df.to_csv(results_path, index=False)

    # Precision@5 for each query and search method.
    per_query = (
        results_df.groupby(
            ["query_number", "query", "method"]
        )
        .agg(
            relevant_results=("estimated_relevant", "sum"),
            returned_results=("estimated_relevant", "count"),
            latency_ms=("search_latency_ms", "first"),
        )
        .reset_index()
    )

    per_query["precision_at_5"] = (
        per_query["relevant_results"]
        / per_query["returned_results"]
    )

    summary = (
        per_query.groupby("method")
        .agg(
            queries_evaluated=("query_number", "nunique"),
            mean_precision_at_5=("precision_at_5", "mean"),
            mean_latency_ms=("latency_ms", "mean"),
            max_latency_ms=("latency_ms", "max"),
        )
        .reset_index()
    )

    summary_path = os.path.join(
        output_dir, "search_evaluation_summary.csv"
    )
    summary.to_csv(summary_path, index=False)

    print("\nEvaluation complete.")
    print(f"Results saved to: {results_path}")
    print(f"Summary saved to: {summary_path}")
    print("\nSummary:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
