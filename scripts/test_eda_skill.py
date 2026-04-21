import os
import sys
import tempfile
import json

import pandas as pd


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.skills.eda_skill.scripts.run_eda_skill import run_eda_skill
from src.skills.eda_skill.tools import invoke_tool, list_tools
from src.skills.eda_skill.adapters import payload_from_state, run_eda_skill_from_state
from src.skills.eda_skill.analyzers.profiler import get_meta_info, get_schema_info
from src.skills.eda_skill.analyzers.target import analyze_target
from src.tools.eda_tool import run as legacy_eda_tool_run


def test_minimal_supervised_runtime():
    df = pd.DataFrame(
        {
            "age": [25, 30, 22, 45, 40],
            "income": [50000, 62000, None, 120000, 95000],
            "tenure_months": [3, 12, 1, 36, 24],
            "churn_flag": [1, 0, 1, 0, 0],
        }
    )

    result = run_eda_skill(
        {
            "data": df,
            "intent": "Analyze this dataset before feature engineering.",
            "target": "churn_flag",
            "problem_type": "classification",
            "analysis_depth": "standard",
        }
    )

    assert result["status"] == "success"
    assert result["meta"]["rows"] == 5
    assert result["meta"]["cols"] == 4
    assert "income" in result["missing"]
    assert "age" in result["distribution"]
    assert isinstance(result["insights"], list)
    assert "features" in result["eda_for_llm"]
    assert "kg_candidates" in result
    assert "rag_queries" in result
    assert result["skipped_modules"] == []


def test_tools_registry_surface():
    df = pd.DataFrame({"age": [25, 30], "flag": [1, 0]})

    tool_names = list_tools()

    assert "build_meta" in tool_names
    assert "analyze_missing" in tool_names

    meta = invoke_tool("build_meta", df)
    assert meta["rows"] == 2
    assert meta["cols"] == 2


def test_runtime_accepts_csv_path():
    df = pd.DataFrame(
        {
            "feature_a": [1, 2, 3],
            "feature_b": [3.5, 4.1, 5.2],
            "label": [0, 1, 0],
        }
    )

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_file:
        csv_path = tmp_file.name

    try:
        df.to_csv(csv_path, index=False)
        result = run_eda_skill(
            {
                "data": csv_path,
                "intent": "Analyze from a file path.",
                "target": "label",
                "problem_type": "classification",
            }
        )
        assert result["meta"]["rows"] == 3
        assert result["target"]["target_name"] == "label"
    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_project_state_adapter_preserves_expected_keys():
    df = pd.DataFrame(
        {
            "age": [25, 30, 22, 45],
            "income": [50000, 62000, 58000, 120000],
            "target_flag": [1, 0, 1, 0],
        }
    )
    state = {
        "df": df,
        "target": "target_flag",
        "problem_type": "classification",
        "output_dir": "output_test_skill",
    }

    payload = payload_from_state(state)
    assert payload["data"] is df
    assert payload["target"] == "target_flag"

    updated_state = run_eda_skill_from_state(dict(state), save_artifacts=False)
    assert "eda_result" in updated_state
    assert "eda_for_llm" in updated_state
    assert "kg_candidates" in updated_state
    assert "eda_skill_result" in updated_state
    assert updated_state["eda_result"]["target"]["target_name"] == "target_flag"


def test_tool_manifest_exists_and_matches_registry():
    manifest_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "src",
        "skills",
        "eda_skill",
        "tool_manifest.json",
    )

    with open(manifest_path, "r", encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)

    manifest_tools = sorted(tool["name"] for tool in manifest["tools"])
    assert "run_eda_skill" in manifest_tools
    assert "load_tabular_data" in manifest_tools
    assert "build_meta" in manifest_tools
    assert set(list_tools()).issubset(set(manifest_tools))
    for tool in manifest["tools"]:
        assert "parameters_schema" in tool
        assert tool["parameters_schema"]["type"] == "object"


def test_legacy_eda_tool_delegates_to_skill():
    df = pd.DataFrame(
        {
            "amount": [10, 20, 30, 40],
            "score": [0.2, 0.4, 0.8, 0.9],
            "label": [0, 0, 1, 1],
        }
    )

    state = {
        "df": df,
        "target": "label",
        "problem_type": "classification",
        "output_dir": "output_test_skill_legacy",
    }

    updated_state = legacy_eda_tool_run(state)
    assert "eda_result" in updated_state
    assert "eda_for_llm" in updated_state
    assert "eda_path" in updated_state
    assert updated_state["eda_result"]["target"]["target_name"] == "label"


def test_internal_analyzers_cover_profiler_and_expression_target():
    df = pd.DataFrame(
        {
            "click": [10, 20, 30],
            "impression": [100, 200, 300],
            "segment": ["a", "b", "b"],
        }
    )

    meta = get_meta_info(df)
    schema = get_schema_info(df)
    target_series, target_meta = analyze_target(df, "click / impression")

    assert meta["rows"] == 3
    assert meta["cols"] == 3
    assert schema["segment"]["dtype"] == "object"
    assert target_meta["type"] == "expression"
    assert round(float(target_series.iloc[0]), 2) == 0.10


if __name__ == "__main__":
    test_minimal_supervised_runtime()
    test_tools_registry_surface()
    test_runtime_accepts_csv_path()
    test_project_state_adapter_preserves_expected_keys()
    test_tool_manifest_exists_and_matches_registry()
    test_legacy_eda_tool_delegates_to_skill()
    test_internal_analyzers_cover_profiler_and_expression_target()
    print("EDA skill runtime test passed.")
