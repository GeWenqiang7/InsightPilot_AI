from src.skills.evaluate_skill.scripts.run_evaluate_skill import run_evaluate_skill


def main() -> None:
    payload = {
        "model_result": {
            "risk_flags": [
                {"risk": "class_imbalance", "severity": "high", "evidence": {"0": 0.9, "1": 0.1}},
                {"risk": "outlier_sensitive_features", "severity": "medium", "evidence": ["amount"]},
            ],
            "evaluation_focus": {
                "metrics": ["roc_auc", "f1_macro", "recall"],
                "checks": ["threshold_tuning_curve"],
            },
        },
        "eda_result": {
            "missing": {
                "income": {"missing_rate": 0.42},
            }
        },
    }

    result = run_evaluate_skill(payload)
    assert result["status"] == "success"
    assert result["gate_decision"] == "needs_review"
    assert len(result["risk_flags"]) >= 2
    assert len(result["improvement_actions"]) >= 1

    print("evaluate_skill test passed")


if __name__ == "__main__":
    main()
