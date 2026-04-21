from typing import Any, Dict



def run_eda_skill(payload: Dict[str, Any]) -> Dict[str, Any]:
    from src.skills.eda_skill.scripts.run_eda_skill import run_eda_skill as _run_eda_skill

    return _run_eda_skill(payload)



def run_eda_skill_from_state(state: Dict[str, Any], save_artifacts: bool = True) -> Dict[str, Any]:
    from src.skills.eda_skill.adapters import run_eda_skill_from_state as _run_eda_skill_from_state

    return _run_eda_skill_from_state(state, save_artifacts=save_artifacts)



def run_model_skill(payload: Dict[str, Any]) -> Dict[str, Any]:
    from src.skills.model_skill.scripts.run_model_skill import run_model_skill as _run_model_skill

    return _run_model_skill(payload)



def run_model_skill_from_state(state: Dict[str, Any], save_artifacts: bool = True) -> Dict[str, Any]:
    from src.skills.model_skill.adapters import run_model_skill_from_state as _run_model_skill_from_state

    return _run_model_skill_from_state(state, save_artifacts=save_artifacts)


def run_advisor_skill(payload: Dict[str, Any]) -> Dict[str, Any]:
    from src.skills.advisor_skill.scripts.run_advisor_skill import run_advisor_skill as _run_advisor_skill

    return _run_advisor_skill(payload)


def run_advisor_skill_from_state(state: Dict[str, Any], save_artifacts: bool = True) -> Dict[str, Any]:
    from src.skills.advisor_skill.adapters import run_advisor_skill_from_state as _run_advisor_skill_from_state

    return _run_advisor_skill_from_state(state, save_artifacts=save_artifacts)


def run_evaluate_skill(payload: Dict[str, Any]) -> Dict[str, Any]:
    from src.skills.evaluate_skill.scripts.run_evaluate_skill import run_evaluate_skill as _run_evaluate_skill

    return _run_evaluate_skill(payload)


def run_evaluate_skill_from_state(state: Dict[str, Any], save_artifacts: bool = True) -> Dict[str, Any]:
    from src.skills.evaluate_skill.adapters import run_evaluate_skill_from_state as _run_evaluate_skill_from_state

    return _run_evaluate_skill_from_state(state, save_artifacts=save_artifacts)


def run_report_skill(payload: Dict[str, Any]) -> Dict[str, Any]:
    from src.skills.report_skill.scripts.run_report_skill import run_report_skill as _run_report_skill

    return _run_report_skill(payload)


def run_report_skill_from_state(state: Dict[str, Any], save_artifacts: bool = True) -> Dict[str, Any]:
    from src.skills.report_skill.adapters import run_report_skill_from_state as _run_report_skill_from_state

    return _run_report_skill_from_state(state, save_artifacts=save_artifacts)


__all__ = [
    "run_eda_skill",
    "run_eda_skill_from_state",
    "run_model_skill",
    "run_model_skill_from_state",
    "run_advisor_skill",
    "run_advisor_skill_from_state",
    "run_evaluate_skill",
    "run_evaluate_skill_from_state",
    "run_report_skill",
    "run_report_skill_from_state",
]
