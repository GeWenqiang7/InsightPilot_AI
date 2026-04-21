import json
import os
import sys

import pandas as pd


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.skills.eda_skill.scripts.run_eda_skill import run_eda_skill
from src.skills.eda_skill.tools import save_eda_skill_artifacts


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    data_path = os.path.join(project_root, "data", "user_personalized_features.csv")

    print("Loading data from:", data_path)
    if not os.path.exists(data_path):
        raise FileNotFoundError("Data file not found: {0}".format(data_path))

    df = pd.read_csv(data_path)
    result = run_eda_skill(
        {
            "data": df,
            "intent": "Run standalone EDA skill validation.",
            "target": "Total_Spending",
            "problem_type": "regression",
            "analysis_depth": "standard",
        }
    )

    output_dir = os.path.join(project_root, "output", "eda_skill_test")
    artifact_paths = save_eda_skill_artifacts(result, output_dir)

    summary_path = os.path.join(output_dir, "eda_skill_summary.json")
    with open(summary_path, "w", encoding="utf-8") as summary_file:
        json.dump(
            {
                "status": result["status"],
                "meta": result["meta"],
                "insight_count": len(result["insights"]),
                "artifact_paths": artifact_paths,
            },
            summary_file,
            indent=2,
            ensure_ascii=True,
        )

    print("EDA skill test completed.")
    print("Artifacts:", artifact_paths)


if __name__ == "__main__":
    main()
