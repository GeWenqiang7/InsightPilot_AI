from src.skills.eda_skill.adapters import run_eda_skill_from_state


def run(state):
    print("\n[EDA TOOL] Delegating to eda_skill...")
    return run_eda_skill_from_state(state, save_artifacts=True)
