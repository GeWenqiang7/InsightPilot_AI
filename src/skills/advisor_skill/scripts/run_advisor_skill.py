from typing import Any, Dict

from src.skills.advisor_skill.tools import (
    build_advisor_for_llm,
    build_constraint_optimization,
    build_rag_kg_hooks,
    build_scenario_options,
    build_strategy_plan,
    validate_payload,
)



def run_advisor_skill(payload: Dict[str, Any]) -> Dict[str, Any]:
    validate_payload(payload)

    result: Dict[str, Any] = {
        "status": "success",
        "strategy_plan": build_strategy_plan(payload),
        "constraint_optimization": build_constraint_optimization(payload),
        "scenario_options": build_scenario_options(payload),
        "rag_kg_hooks": build_rag_kg_hooks(payload),
        "advisor_for_llm": {},
        "confidence_notes": [],
    }

    result["advisor_for_llm"] = build_advisor_for_llm(result)
    return result
