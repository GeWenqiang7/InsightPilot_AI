'''
作用：
    1️⃣ 评估模型性能
    - classification → accuracy / F1
    - regression → RMSE
    2️⃣ 检测问题
    - overfitting
    - underfitting
    - imbalance问题
    3️⃣ 给出改进建议
    - 换模型
    - 加特征
    - 调参
    - 改FE
    4️⃣ 决定是否重训（闭环关键）
    if 模型不好 → trigger retrain
    if 模型好 → 结束流程
    


'''
# src/agents/evaluation_agent.py

import numpy as np


# =========================
# 🔥 评估模型
# =========================
def evaluate_model(state):

    results = state.get("model_results", [])
    best_model = state.get("best_model")

    if not best_model:
        return {"status": "no_model"}

    score = best_model.get("score", None)

    return {
        "best_score": score,
        "model": best_model["model"]
    }


# =========================
# 🔥 检测问题
# =========================
def diagnose_issues(state, eval_result):

    issues = []

    score = eval_result.get("best_score")

    if score is None:
        issues.append("no_valid_model")
        return issues

    # =========================
    # 低性能
    # =========================
    if score < 0.6:
        issues.append("low_performance")

    # =========================
    # 过拟合（简化判断）
    # =========================
    # 后期可以加入 train vs val
    if score > 0.95:
        issues.append("possible_overfitting")

    return issues


# =========================
# 🔥 给出优化建议
# =========================
def generate_improvements(state, issues):

    suggestions = []

    for issue in issues:

        if issue == "low_performance":
            suggestions.append({
                "action": "try_more_models",
                "detail": "add boosting / deep learning"
            })

            suggestions.append({
                "action": "feature_engineering",
                "detail": "add interaction / PCA"
            })

        if issue == "possible_overfitting":
            suggestions.append({
                "action": "regularization",
                "detail": "reduce model complexity"
            })

        if issue == "no_valid_model":
            suggestions.append({
                "action": "data_check",
                "detail": "check data quality"
            })

    return suggestions


# =========================
# 🔥 是否触发重新训练
# =========================
def should_retrain(issues):

    if "low_performance" in issues:
        return True

    if "no_valid_model" in issues:
        return True

    return False


# =========================
# 🔥 主入口
# =========================
def run(state):

    print("📊 [EVALUATION AGENT] Evaluating model...")

    # =========================
    # 1️⃣ 评估
    # =========================
    eval_result = evaluate_model(state)

    # =========================
    # 2️⃣ 问题诊断
    # =========================
    issues = diagnose_issues(state, eval_result)

    # =========================
    # 3️⃣ 优化建议
    # =========================
    improvements = generate_improvements(state, issues)

    # =========================
    # 4️⃣ 是否重训
    # =========================
    retrain_flag = should_retrain(issues)

    result = {
        "evaluation": eval_result,
        "issues": issues,
        "improvements": improvements,
        "retrain": retrain_flag
    }

    state["evaluation_result"] = result

    print("✅ Evaluation complete")
    print(f"   - score: {eval_result.get('best_score')}")
    print(f"   - issues: {issues}")
    print(f"   - retrain: {retrain_flag}")

    return state