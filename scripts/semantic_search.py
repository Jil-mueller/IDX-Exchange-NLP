import time

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi


class SemanticSearcher:
    """Retrieve real-estate listings using semantic similarity."""

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.listings = None
        self.embeddings = None

    def build_index(self, remarks_list):
        """Encode listing remarks and build a FAISS index."""
        if not remarks_list:
            raise ValueError("Cannot build an index from an empty list.")

        print(f"Encoding {len(remarks_list)} listings...")

        self.listings = remarks_list

        embeddings = self.model.encode(
            remarks_list,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        embeddings = np.ascontiguousarray(
            embeddings, dtype=np.float32
        )

        self.embeddings = embeddings

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)

        print(f"Index built: {self.index.ntotal} listings")
        print(f"Embedding dimensions: {dimension}")

    def search(self, query, top_k=10):
        """Return the most similar listing remarks and scores."""
        if self.index is None:
            raise ValueError("Build the index before searching.")

        if top_k <= 0:
            return []

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        query_embedding = np.ascontiguousarray(
            query_embedding, dtype=np.float32
        )

        k = min(top_k, len(self.listings))

        scores, indices = self.index.search(query_embedding, k)

        results = []

        for j, index in enumerate(indices[0]):
            if index >= 0:
                results.append(
                    (self.listings[index], float(scores[0][j]))
                )

        return results


class BM25Searcher:
    """Retrieve listing remarks using keyword relevance."""

    def __init__(self):
        self.listings = None
        self.bm25 = None

    def build_index(self, remarks_list):
        """Build a BM25 keyword retrieval index."""
        if not remarks_list:
            raise ValueError("Cannot build an index from an empty list.")

        self.listings = remarks_list

        tokenized_remarks = [
            remark.lower().split()
            for remark in remarks_list
        ]

        self.bm25 = BM25Okapi(tokenized_remarks)

    def search(self, query, top_k=10):
        """Return the most relevant keyword matches."""
        if self.bm25 is None:
            raise ValueError("Build the index before searching.")

        if top_k <= 0:
            return []

        scores = self.bm25.get_scores(query.lower().split())

        # Select top results without sorting the entire dataset.
        k = min(top_k, len(self.listings))
        best_indices = []

        for _ in range(k):
            best_index = -1
            best_score = float("-inf")

            for i, score in enumerate(scores):
                if i not in best_indices and score > best_score:
                    best_score = score
                    best_index = i

            if best_index == -1:
                break

            best_indices.append(best_index)

        return [
            (self.listings[i], float(scores[i]))
            for i in best_indices
        ]


def load_listings(csv_path="data/processed/listing_sample.csv"):
    """Load listing IDs and remarks from the processed CSV."""
    df = pd.read_csv(csv_path)

    df = df.dropna(subset=["remarks"]).copy()
    df["remarks"] = df["remarks"].astype(str)

    if "L_ListingID" in df.columns:
        listing_ids = df["L_ListingID"].tolist()
    else:
        listing_ids = df.index.tolist()

    remarks = df["remarks"].tolist()

    return listing_ids, remarks


if __name__ == "__main__":
    listing_ids, remarks = load_listings()

    semantic_searcher = SemanticSearcher()
    semantic_searcher.build_index(remarks)

    bm25_searcher = BM25Searcher()
    bm25_searcher.build_index(remarks)

    query = "spacious home with a swimming pool and large backyard"

    print(f"\nQuery: {query}")

    start = time.perf_counter()
    semantic_results = semantic_searcher.search(query, top_k=5)
    semantic_latency = (time.perf_counter() - start) * 1000

    print(f"\nSemantic results ({semantic_latency:.2f} ms):")

    for remark, score in semantic_results:
        position = remarks.index(remark)
        print(
            f"Listing {listing_ids[position]} | "
            f"Score: {score:.4f} | {remark[:200]}"
        )

    start = time.perf_counter()
    bm25_results = bm25_searcher.search(query, top_k=5)
    bm25_latency = (time.perf_counter() - start) * 1000

    print(f"\nBM25 results ({bm25_latency:.2f} ms):")

    for remark, score in bm25_results:
        position = remarks.index(remark)
        print(
            f"Listing {listing_ids[position]} | "
            f"Score: {score:.4f} | {remark[:200]}"
        )
