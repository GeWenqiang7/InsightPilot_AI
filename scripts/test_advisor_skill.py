from src.skills.advisor_skill.scripts.run_advisor_skill import run_advisor_skill


def main() -> None:
    payload = {
        "constraints": {"latency_ms": "<80ms", "false_positive_tolerance": "low"},
        "model_result": {
            "model_candidates_ranked": [{"name": "xgboost_classifier", "priority_score": 100}],
        },
        "evaluation_result": {
            "risk_flags": [
                {"risk": "class_imbalance", "severity": "high"},
                {"risk": "severe_missingness", "severity": "high"},
            ]
        },
    }

    result = run_advisor_skill(payload)
    assert result["status"] == "success"
    assert len(result["strategy_plan"]) >= 2
    assert 3 <= len(result["scenario_options"]) <= 5
    assert len(result["constraint_optimization"]) >= 3

    print("advisor_skill test passed")


if __name__ == "__main__":
    main()
