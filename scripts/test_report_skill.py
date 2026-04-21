from src.skills.report_skill.scripts.run_report_skill import run_report_skill


def main() -> None:
    payload = {
        "user_query": "请给出提升CTR模型召回率并控制误报的可执行建议",
        "eda_result": {"insights": [{"type": "missing"}, {"type": "outlier"}]},
        "fe_plan": {"feature_engineering": [{"column": "income", "method": "impute"}]},
        "model_result": {
            "model_candidates_ranked": [{"name": "random_forest_classifier", "priority_score": 105}],
            "evaluation_focus": {"metrics": ["roc_auc", "f1", "recall"]},
        },
        "evaluation_result": {
            "gate_decision": "needs_review",
            "improvement_actions": [{"priority": "high", "action": "run mitigation experiment"}],
            "risk_flags": [{"risk": "class_imbalance", "severity": "high"}],
        },
        "advisor_result": {
            "strategy_plan": [{"stage": "imbalance_mitigation"}],
            "scenario_options": [
                {"name": "稳健优先", "plan": "先缓解风险", "tradeoff": "慢"},
                {"name": "效率优先", "plan": "快速迭代", "tradeoff": "可能降精度"},
                {"name": "收益优先", "plan": "追求上限", "tradeoff": "成本高"},
            ],
            "constraint_optimization": [{"constraint": "latency"}],
            "rag_kg_hooks": {"rag_queries": ["q1"], "kg_links": [{"source": "s", "target": "t", "type": "r"}]},
        },
    }

    result = run_report_skill(payload)
    assert result["status"] == "success"
    assert result["delivery_decision"] == "needs_review"
    assert "# Analysis Report" in result["report_markdown"]
    assert len(result["requirement_alignment"]) >= 1
    assert len(result["visualization_plan"]) >= 2
    assert result["advisor_integration"]["strategy_source"] == "advisor_skill"

    print("report_skill test passed")


if __name__ == "__main__":
    main()
