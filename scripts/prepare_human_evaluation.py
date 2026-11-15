import pandas as pd
from pathlib import Path


def prepare_human_evaluation():

    project_root = Path(__file__).resolve().parents[1]

    input_path = project_root / "data" / "processed" / "listing_summaries.csv"
    output_path = project_root / "data" / "processed" / "human_evaluation.csv"

    df = pd.read_csv(input_path)

    # Select 20 listings randomly, using a fixed seed
    sample = df.sample(n=20, random_state=42)

    # Keep the information reviewers need
    evaluation = sample[
        ["L_ListingID", "L_Address", "L_City", "generated_summary"]
    ].copy()

    # Add blank columns for reviewer feedback
    evaluation["accuracy"] = ""
    evaluation["coverage"] = ""
    evaluation["readability"] = ""
    evaluation["overall_rating"] = ""
    evaluation["comments"] = ""

    evaluation.to_csv(output_path, index=False)

    print("HUMAN EVALUATION FILE CREATED")
    print("Summaries selected:", len(evaluation))
    print("Saved to:", output_path)


if __name__ == "__main__":
    prepare_human_evaluation()