import json
import os
from typing import Any, Dict, List


class AdvisorSkillValidationError(ValueError):
    pass



def validate_payload(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise AdvisorSkillValidationError("payload must be a dict")

    required = ["model_result", "evaluation_result"]
    missing = [name for name in required if not isinstance(payload.get(name), dict)]
    if missing:
        raise AdvisorSkillValidationError(f"missing required dict inputs: {', '.join(missing)}")



def build_strategy_plan(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    eval_result = payload["evaluation_result"]
    risk_flags = eval_result.get("risk_flags", [])

    plan = [
        {
            "stage": "baseline_confirmation",
            "objective": "验证当前最优模型在固定切分上的可重复性",
            "success_criteria": "关键指标波动小于预设阈值",
        },
        {
            "stage": "robustness_review",
            "objective": "检验模型对异常值、缺失、样本偏移的稳定性",
            "success_criteria": "风险切片指标未显著退化",
        },
    ]

    if any(r.get("risk") == "class_imbalance" for r in risk_flags):
        plan.append(
            {
                "stage": "imbalance_mitigation",
                "objective": "优化召回与误报平衡",
                "success_criteria": "在业务阈值下召回提升且误报可控",
            }
        )

    if any(r.get("risk") in {"high_missing", "severe_missingness"} for r in risk_flags):
        plan.append(
            {
                "stage": "missing_strategy_optimization",
                "objective": "比较插补策略并评估稳定性",
                "success_criteria": "验证集性能和稳定性双提升",
            }
        )

    return plan



def build_constraint_optimization(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    constraints = payload.get("constraints", {}) if isinstance(payload.get("constraints"), dict) else {}

    presets = [
        {"constraint": "inference_latency", "target": constraints.get("latency_ms", "<100ms"), "action": "模型压缩或蒸馏"},
        {"constraint": "false_positive_cost", "target": constraints.get("false_positive_tolerance", "medium"), "action": "阈值重标定"},
        {"constraint": "interpretability", "target": constraints.get("interpretability", "medium"), "action": "保留可解释基线模型并输出特征贡献"},
    ]

    return presets



def build_scenario_options(payload: Dict[str, Any], min_count: int = 3, max_count: int = 5) -> List[Dict[str, Any]]:
    model_candidates = payload["model_result"].get("model_candidates_ranked", [])
    top_name = model_candidates[0].get("name") if model_candidates else "baseline_model"

    scenarios = [
        {
            "name": "稳健优先",
            "plan": f"以 {top_name} 为主，先做风险缓解后再上线",
            "tradeoff": "上线速度较慢但风险可控",
        },
        {
            "name": "效率优先",
            "plan": "选择较轻量模型并快速迭代，缩短验证周期",
            "tradeoff": "可能牺牲部分极端场景性能",
        },
        {
            "name": "收益优先",
            "plan": "接受更高训练复杂度换取关键指标上限",
            "tradeoff": "算力与维护成本增加",
        },
        {
            "name": "解释优先",
            "plan": "保留线性/树模型双轨输出，提高业务可解释性",
            "tradeoff": "整体上限可能略低于黑盒模型",
        },
    ]

    return scenarios[:max(min_count, min(max_count, len(scenarios)))]



def build_rag_kg_hooks(payload: Dict[str, Any]) -> Dict[str, Any]:
    hooks = {"rag_queries": [], "kg_links": []}
    for risk in payload["evaluation_result"].get("risk_flags", []):
        risk_name = risk.get("risk")
        if risk_name == "class_imbalance":
            hooks["rag_queries"].append("business-aligned threshold tuning for imbalanced binary classification")
            hooks["kg_links"].append({"source": "class_imbalance", "target": "threshold_policy", "type": "requires"})
        elif risk_name in {"high_missing", "severe_missingness"}:
            hooks["rag_queries"].append("missing mechanism diagnosis and imputation robustness best practices")
            hooks["kg_links"].append({"source": "missingness", "target": "imputation_policy", "type": "mitigated_by"})

    if payload.get("rag_context"):
        hooks["rag_queries"].append("use existing retrieved context to refine decision constraints")
    if payload.get("kg_context"):
        hooks["kg_links"].append({"source": "kg_context", "target": "advisor_decision", "type": "supports"})

    return hooks



def build_advisor_for_llm(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "decision_focus": "strategy_and_constraints",
        "scenario_options": result.get("scenario_options", [])[:3],
        "top_constraints": result.get("constraint_optimization", [])[:3],
    }



def save_advisor_skill_artifacts(result: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)

    result_path = os.path.join(output_dir, "advisor_skill_result.json")
    llm_path = os.path.join(output_dir, "advisor_skill_for_llm.json")

    with open(result_path, "w", encoding="utf-8") as result_file:
        json.dump(result, result_file, indent=2, ensure_ascii=False)

    with open(llm_path, "w", encoding="utf-8") as llm_file:
        json.dump(result.get("advisor_for_llm", {}), llm_file, indent=2, ensure_ascii=False)

    return {"result_path": result_path, "llm_path": llm_path}
