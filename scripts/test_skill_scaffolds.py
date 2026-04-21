import json
import os
import sys


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.skills.fe_skill import run_fe_skill, run_fe_skill_from_state
from src.skills.model_skill import run_model_skill
from src.skills.report_skill import run_report_skill
from src.tools.fe_tool import run as legacy_fe_tool_run


def _load_manifest(skill_name):
    manifest_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "src",
        "skills",
        skill_name,
        "tool_manifest.json",
    )
    with open(manifest_path, "r", encoding="utf-8") as manifest_file:
        return json.load(manifest_file)


def test_fe_skill_scaffold():
    result = run_fe_skill(
        {
            "intent": "Build an FE plan.",
            "problem_type": "classification",
            "eda_result": {
                "missing": {
                    "income": {"missing_rate": 0.35, "missing_flag": "high"},
                    "city": {"missing_rate": 0.02, "missing_flag": "low"},
                },
                "distribution": {
                    "amount": {"skew": 1.7},
                    "age": {"skew": 0.1},
                },
                "outliers": {
                    "amount": {"outlier_ratio": 0.08},
                    "age": {"outlier_ratio": 0.01},
                },
                "correlation": {
                    "high_correlation_pairs": [
                        {"feature_1": "amount", "feature_2": "amount_log", "correlation": 0.91}
                    ]
                },
                "schema": {
                    "city": {"semantic_type": "categorical", "n_unique": 5},
                    "merchant_id": {"semantic_type": "categorical", "n_unique": 25},
                    "amount": {"semantic_type": "numeric", "n_unique": 100}
                }
            },
            "model_candidates": [
                {"name": "LogisticRegression", "category": "linear"},
                {"name": "RandomForest", "category": "tree"}
            ]
        }
    )
    manifest = _load_manifest("fe_skill")

    assert result["skill"] == "fe_skill"
    assert result["status"] == "success"
    assert result["problem_type"] == "classification"
    assert len(result["data_issues"]) >= 2
    assert len(result["feature_engineering"]) >= 3
    assert "drop" in result["feature_selection"]
    assert len(result["model_alignment"]) == 2
    assert manifest["skill_name"] == "fe_skill"
    assert len(manifest["tools"]) >= 3


def test_fe_skill_state_adapter_and_legacy_tool():
    state = {
        "intent": "Generate FE plan after EDA.",
        "problem_type": "regression",
        "output_dir": "output_test_fe_skill",
        "eda_result": {
            "missing": {"income": {"missing_rate": 0.33, "missing_flag": "high"}},
            "distribution": {"amount": {"skew": 1.5}},
            "outliers": {"amount": {"outlier_ratio": 0.06}},
            "correlation": {"high_correlation_pairs": []},
            "schema": {"amount": {"semantic_type": "numeric", "n_unique": 50}}
        },
        "model_candidates": [{"name": "XGBoostRegressor", "category": "tree"}]
    }

    updated_state = run_fe_skill_from_state(dict(state), save_artifacts=False)
    assert updated_state["fe_plan"]["status"] == "success"
    assert updated_state["fe_plan"]["problem_type"] == "regression"

    legacy_state = legacy_fe_tool_run(dict(state))
    assert legacy_state["fe_plan"]["status"] == "success"
    assert "fe_skill_result" in legacy_state


def test_model_skill_scaffold():
    result = run_model_skill({"intent": "Build a model plan.", "problem_type": "classification"})
    manifest = _load_manifest("model_skill")

    assert result["skill"] == "model_skill"
    assert result["status"] == "scaffold"
    assert manifest["skill_name"] == "model_skill"
    assert len(manifest["tools"]) >= 3


def test_report_skill_scaffold():
    result = run_report_skill({"intent": "Build a report plan."})
    manifest = _load_manifest("report_skill")

    assert result["skill"] == "report_skill"
    assert result["status"] == "scaffold"
    assert manifest["skill_name"] == "report_skill"
    assert len(manifest["tools"]) >= 3


if __name__ == "__main__":
    test_fe_skill_scaffold()
    test_model_skill_scaffold()
    test_report_skill_scaffold()
    print("Skill scaffold tests passed.")
