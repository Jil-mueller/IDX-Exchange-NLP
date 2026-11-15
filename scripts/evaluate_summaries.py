import pandas as pd
from rouge_score import rouge_scorer
from pathlib import Path


def evaluate_summaries():

    # Locate project files
    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data" / "processed" / "listing_summaries.csv"

    # Load generated summaries and original remarks
    df = pd.read_csv(data_path)

    # Initialize ROUGE evaluator
    scorer = rouge_scorer.RougeScorer(
        ["rouge1", "rouge2", "rougeL"],
        use_stemmer=True
    )

    rouge1_scores = []
    rouge2_scores = []
    rougeL_scores = []

    # Compare each generated summary with its original remarks
    for _, row in df.iterrows():

        reference = str(row["remarks"])
        generated = str(row["generated_summary"])

        scores = scorer.score(reference, generated)

        rouge1_scores.append(scores["rouge1"].fmeasure)
        rouge2_scores.append(scores["rouge2"].fmeasure)
        rougeL_scores.append(scores["rougeL"].fmeasure)

    # Calculate average scores
    print("\nROUGE EVALUATION RESULTS")
    print("=" * 40)

    print(f"Listings evaluated: {len(df)}")
    print(f"Average ROUGE-1: {sum(rouge1_scores) / len(rouge1_scores):.4f}")
    print(f"Average ROUGE-2: {sum(rouge2_scores) / len(rouge2_scores):.4f}")
    print(f"Average ROUGE-L: {sum(rougeL_scores) / len(rougeL_scores):.4f}")

    # Save individual scores
    df["rouge1"] = rouge1_scores
    df["rouge2"] = rouge2_scores
    df["rougeL"] = rougeL_scores

    output_path = project_root / "data" / "processed" / "rouge_evaluation.csv"
    df.to_csv(output_path, index=False)

    print("\nIndividual scores saved to:", output_path)


if __name__ == "__main__":
    evaluate_summaries()
