from typing import Any, Dict

from src.skills.report_skill.tools import (
    build_action_plan,
    build_advisor_integration,
    build_executive_summary,
    build_key_findings,
    build_markdown_report,
    build_rag_kg_hooks,
    build_report_for_llm,
    build_requirement_alignment,
    build_visualization_plan,
    validate_payload,
)



def run_report_skill(payload: Dict[str, Any]) -> Dict[str, Any]:
    validate_payload(payload)

    result: Dict[str, Any] = {
        "status": "success",
        "executive_summary": build_executive_summary(payload),
        "key_findings": build_key_findings(payload),
        "action_plan": build_action_plan(payload),
        "delivery_decision": payload["evaluation_result"].get("gate_decision", "proceed"),
        "requirement_alignment": build_requirement_alignment(payload),
        "visualization_plan": build_visualization_plan(payload),
        "advisor_integration": build_advisor_integration(payload),
        "rag_kg_hooks": build_rag_kg_hooks(payload),
        "report_markdown": "",
        "report_for_llm": {},
        "confidence_notes": [],
    }

    result["report_markdown"] = build_markdown_report(result)
    result["report_for_llm"] = build_report_for_llm(result)

    if result["delivery_decision"] == "needs_review":
        result["confidence_notes"].append("report indicates unresolved high-risk items before delivery")

    if not result["requirement_alignment"]:
        result["confidence_notes"].append("user requirement alignment is limited because no initial query/intent was provided")

    return result
