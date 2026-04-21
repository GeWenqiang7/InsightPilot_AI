from src.skills.model_skill.scripts.run_model_skill import run_model_skill


def main() -> None:
    payload = {
        "problem_type": "classification",
        "fe_plan": {
            "problem_type": "classification",
            "data_issues": [{"issue": "missing", "columns": ["income"], "severity": "high"}],
            "feature_engineering": [
                {"column": "income", "method": "impute_median", "priority": "high"},
                {"column": "amount", "method": "log_transform", "priority": "medium"},
            ],
        },
        "eda_result": {
            "missing": {"income": {"missing_rate": 0.38}},
            "outliers": {"amount": {"outlier_ratio": 0.08}},
            "target": {
                "imbalance_flag": "high",
                "class_distribution": {"0": 0.9, "1": 0.1},
            },
            "insights": [{"type": "missing"}, {"type": "outlier"}],
        },
    }

    result = run_model_skill(payload)
    assert result["status"] == "success"
    assert result["problem_type"] == "classification"
    assert len(result["model_candidates_ranked"]) >= 1
    assert "metrics" in result["evaluation_focus"]

    print("model_skill test passed")


if __name__ == "__main__":
    main()
