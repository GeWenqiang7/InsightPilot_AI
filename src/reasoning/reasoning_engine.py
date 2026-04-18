'''
- 接收 KG结果
- 接收 goal
- 接收 RAG
- 输出完整决策（FE + model + strategy）

功能：
- 任务类型识别（Tabular / Time Series / NLP / RL）
    time_series → lag / rolling
    nlp → embedding / tfidf
- 基于KG的特征选择（重要性分析、关系分析）
- 模型选择（基于任务类型和数据规模）
    tabular → xgboost
    time_series → prophet / lstm
    nlp → bert
    rl → dqn（结构预留）
- 训练策略设计（交叉验证、超参调优等）

'''

def detect_task_type(state):

    schema = state.get("eda_result", {}).get("schema", {})
    goal = state.get("selected_goal")

    text_cols = []
    time_cols = []

    for col, info in schema.items():
        dtype = info["dtype"]

        if "object" in dtype:
            text_cols.append(col)

        if "datetime" in dtype:
            time_cols.append(col)

    # =========================
    # NLP
    # =========================
    if len(text_cols) > 2:
        return "nlp"

    # =========================
    # Time Series
    # =========================
    if len(time_cols) > 0:
        return "time_series"

    # =========================
    # RL（预留）
    # =========================
    if goal and "strategy" in goal.goal_name.lower():
        return "reinforcement_learning"

    return "tabular"


# =========================
# 🔥 Feature Engineering（增强）
# =========================
def build_fe_strategy(state, task_type):

    eda = state.get("eda_result", {})
    dist = eda.get("distribution", {})
    missing = eda.get("missing", {})

    fe_plan = []

    # ===== 通用 =====
    for col in eda.get("schema", {}):

        if col in missing and missing[col]["missing_rate"] > 0.3:
            fe_plan.append({"feature": col, "action": "impute"})

        if col in dist and abs(dist[col].get("skew", 0)) > 1:
            fe_plan.append({"feature": col, "action": "log_transform"})

    # ===== Task-specific =====

    # Time series
    if task_type == "time_series":
        fe_plan.append({"action": "lag_features"})
        fe_plan.append({"action": "rolling_mean"})
        fe_plan.append({"action": "trend_decomposition"})

    # NLP
    if task_type == "nlp":
        fe_plan.append({"action": "text_cleaning"})
        fe_plan.append({"action": "tfidf"})
        fe_plan.append({"action": "embedding"})

    return fe_plan


# =========================
# 🔥 模型选择（超级升级版）
# =========================
def select_model(state, task_type):

    eda = state.get("eda_result", {})
    n_rows = eda.get("meta", {}).get("rows", 0)

    # =========================
    # TABULAR
    # =========================
    if task_type == "tabular":

        if n_rows < 5000:
            return {
                "model": "logistic_regression",
                "family": "linear"
            }

        elif n_rows < 100000:
            return {
                "model": "xgboost",
                "family": "tree"
            }

        else:
            return {
                "model": "mlp",
                "framework": "pytorch",
                "family": "deep_learning"
            }

    # =========================
    # TIME SERIES
    # =========================
    if task_type == "time_series":

        return {
            "model": "prophet",
            "candidates": [
                "arima",
                "prophet",
                "lstm",
                "transformer_ts"
            ],
            "family": "time_series"
        }

    # =========================
    # NLP
    # =========================
    if task_type == "nlp":

        return {
            "model": "bert",
            "framework": "huggingface",
            "candidates": [
                "tfidf + logistic",
                "lstm",
                "bert",
                "transformer"
            ],
            "family": "nlp"
        }

    # =========================
    # RL（预留结构）
    # =========================
    if task_type == "reinforcement_learning":

        return {
            "model": "dqn",
            "framework": "pytorch",
            "candidates": [
                "dqn",
                "ppo",
                "a3c"
            ],
            "family": "rl"
        }

    return {"model": "xgboost"}


# =========================
# 🔥 训练策略（增强）
# =========================
def build_training_strategy(task_type):

    strategy = {
        "cross_validation": "kfold",
        "hyperparameter_tuning": "optuna"
    }

    if task_type == "time_series":
        strategy["cv"] = "time_series_split"

    if task_type == "nlp":
        strategy["batch_size"] = 32
        strategy["epochs"] = 5

    if task_type == "reinforcement_learning":
        strategy["episodes"] = 1000

    return strategy


# =========================
# 🔥 主入口
# =========================
def run(state):

    print("🧠 [REASONING ENGINE v3] Multi-task decision system...")

    task_type = detect_task_type(state)

    selected_features = state.get("kg_result", {}).get("key_features", [])
    fe_plan = build_fe_strategy(state, task_type)
    model_plan = select_model(state, task_type)
    training_plan = build_training_strategy(task_type)

    decision = {
        "task_type": task_type,
        "selected_features": selected_features,
        "feature_engineering": fe_plan,
        "model": model_plan,
        "training": training_plan
    }

    state["decision"] = decision

    print("✅ Decision ready")
    print(f"   - task: {task_type}")
    print(f"   - model: {model_plan['model']}")

    return state