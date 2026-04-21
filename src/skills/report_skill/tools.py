import json
import os
from typing import Any, Dict, List


class ReportSkillValidationError(ValueError):
    pass



def validate_payload(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ReportSkillValidationError("payload must be a dict")

    required = ["eda_result", "fe_plan", "model_result", "evaluation_result"]
    missing = [name for name in required if not isinstance(payload.get(name), dict)]
    if missing:
        raise ReportSkillValidationError(f"missing required dict inputs: {', '.join(missing)}")



def build_executive_summary(payload: Dict[str, Any]) -> str:
    model_result = payload["model_result"]
    evaluation_result = payload["evaluation_result"]

    top_models = model_result.get("model_candidates_ranked", [])
    top_model_name = top_models[0]["name"] if top_models else "baseline_model"
    gate = evaluation_result.get("gate_decision", "proceed")

    if gate == "needs_review":
        return (
            f"当前推荐首选模型为 {top_model_name}，但评估阶段识别到高风险项。"
            "建议在执行风险缓解实验后再进入最终上线决策。"
        )

    return (
        f"当前推荐首选模型为 {top_model_name}，评估结果显示可继续推进。"
        "建议进入受控验证并准备部署前检查清单。"
    )



def build_key_findings(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    eda_insights = payload["eda_result"].get("insights", [])
    if eda_insights:
        findings.append({"stage": "eda", "finding": f"识别到 {len(eda_insights)} 条核心数据洞察", "evidence": eda_insights[:3]})

    fe_actions = payload["fe_plan"].get("feature_engineering", [])
    findings.append({"stage": "fe", "finding": f"规划了 {len(fe_actions)} 条特征工程动作", "evidence": fe_actions[:3]})

    model_ranked = payload["model_result"].get("model_candidates_ranked", [])
    findings.append({"stage": "model", "finding": f"完成 {len(model_ranked)} 个候选模型优先级排序", "evidence": model_ranked[:3]})

    eval_risks = payload["evaluation_result"].get("risk_flags", [])
    findings.append({"stage": "evaluate", "finding": f"评估阶段记录风险项 {len(eval_risks)} 个", "evidence": eval_risks[:3]})

    return findings



def build_action_plan(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    actions = payload["evaluation_result"].get("improvement_actions", [])
    if actions:
        return actions

    return [{"priority": "medium", "action": "run baseline verification and production-readiness checklist"}]



def build_requirement_alignment(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = payload.get("user_query") or payload.get("intent") or ""
    if not query:
        return []

    decision = payload["evaluation_result"].get("gate_decision", "proceed")
    return [
        {
            "user_need": str(query),
            "response": "当前已完成从数据到模型到评估的闭环分析，并汇总为交付报告。",
            "coverage": "partial" if decision == "needs_review" else "high",
            "gap": "需先完成高风险缓解实验" if decision == "needs_review" else "无关键阻塞",
        }
    ]



def build_visualization_plan(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    model_metrics = payload["model_result"].get("evaluation_focus", {}).get("metrics", [])
    eval_risks = payload["evaluation_result"].get("risk_flags", [])

    plan = [
        {"chart": "model_leaderboard_bar", "purpose": "展示候选模型优先级与关键指标", "source": "model_result.model_candidates_ranked"},
        {"chart": "risk_heatmap", "purpose": "展示风险类型与严重度", "source": "evaluation_result.risk_flags"},
    ]

    if model_metrics:
        plan.append({"chart": "metric_profile_radar", "purpose": "比较核心评估指标表现", "source": "model_result.evaluation_focus.metrics"})

    if any(r.get("risk") in {"class_imbalance", "severe_missingness"} for r in eval_risks):
        plan.append({"chart": "mitigation_impact_line", "purpose": "展示缓解策略前后收益变化", "source": "evaluation_result.improvement_actions + retrain_results"})

    return plan



def build_advisor_integration(payload: Dict[str, Any]) -> Dict[str, Any]:
    advisor = payload.get("advisor_result")
    if not isinstance(advisor, dict):
        return {"strategy_source": "none", "strategy_plan": [], "scenario_options": [], "constraint_optimization": []}

    return {
        "strategy_source": "advisor_skill",
        "strategy_plan": advisor.get("strategy_plan", []),
        "scenario_options": advisor.get("scenario_options", []),
        "constraint_optimization": advisor.get("constraint_optimization", []),
    }



def build_rag_kg_hooks(payload: Dict[str, Any]) -> Dict[str, Any]:
    hooks = {"rag_queries": [], "kg_links": []}

    advisor = payload.get("advisor_result")
    if isinstance(advisor, dict):
        advisor_hooks = advisor.get("rag_kg_hooks", {})
        hooks["rag_queries"].extend(advisor_hooks.get("rag_queries", []))
        hooks["kg_links"].extend(advisor_hooks.get("kg_links", []))

    if payload.get("rag_context"):
        hooks["rag_queries"].append("summarize retrieved guidance into business-facing recommendations")
    if payload.get("kg_context"):
        hooks["kg_links"].append({"source": "kg_context", "target": "report_section", "type": "supports"})

    return hooks



def build_markdown_report(report: Dict[str, Any]) -> str:
    lines = ["# Analysis Report", "", "## Executive Summary", report["executive_summary"], "", "## Key Findings"]

    for finding in report["key_findings"]:
        lines.append(f"- **[{finding['stage']}]** {finding['finding']}")

    lines.extend(["", "## Action Plan"])
    for action in report["action_plan"]:
        lines.append(f"- ({action.get('priority', 'medium')}) {action.get('action')}")

    lines.extend(["", "## Visualization Plan"])
    for viz in report.get("visualization_plan", []):
        lines.append(f"- `{viz['chart']}`: {viz['purpose']}")

    advisor = report.get("advisor_integration", {})
    if advisor.get("strategy_source") == "advisor_skill":
        lines.extend(["", "## Strategy & Constraint Suggestions (from advisor_skill)"])
        for option in advisor.get("scenario_options", [])[:5]:
            lines.append(f"- **{option.get('name', 'scenario')}**: {option.get('plan')}（权衡：{option.get('tradeoff', '-') }）")

    lines.extend(["", "## Delivery Decision", f"- Gate: `{report['delivery_decision']}`"])
    return "\n".join(lines)



def build_report_for_llm(report: Dict[str, Any]) -> Dict[str, Any]:
    advisor = report.get("advisor_integration", {})
    return {
        "executive_summary": report["executive_summary"],
        "delivery_decision": report["delivery_decision"],
        "top_actions": report["action_plan"][:3],
        "requirement_alignment": report.get("requirement_alignment", []),
        "scenario_options": advisor.get("scenario_options", [])[:3],
    }



def save_report_skill_artifacts(result: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)

    result_path = os.path.join(output_dir, "report_skill_result.json")
    llm_path = os.path.join(output_dir, "report_skill_for_llm.json")
    md_path = os.path.join(output_dir, "analysis_report.md")

    with open(result_path, "w", encoding="utf-8") as result_file:
        json.dump(result, result_file, indent=2, ensure_ascii=False)

    with open(llm_path, "w", encoding="utf-8") as llm_file:
        json.dump(result.get("report_for_llm", {}), llm_file, indent=2, ensure_ascii=False)

    with open(md_path, "w", encoding="utf-8") as markdown_file:
        markdown_file.write(result.get("report_markdown", ""))

    return {"result_path": result_path, "llm_path": llm_path, "markdown_path": md_path}
