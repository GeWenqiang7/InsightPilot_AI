from src.skills.fe_skill.adapters import run_fe_skill_from_state


def run(state):
    print("\n[FE TOOL] Delegating to fe_skill...")
    return run_fe_skill_from_state(state, save_artifacts=True)
