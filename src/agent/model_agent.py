'''
功能：
1. 根据 decision 选择模型
2. 构建训练数据（X, y）
3. 训练多个模型（baseline + candidates）
4. 做交叉验证
5. 输出最优模型 + performance

'''
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, mean_squared_error

from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

# 可选
try:
    from xgboost import XGBClassifier, XGBRegressor
except:
    XGBClassifier = None
    XGBRegressor = None


# =========================
#   构建训练数据
# =========================
def prepare_data(state):

    df = state["df"]
    target_series = state.get("target_series")

    selected_features = state.get("decision", {}).get("selected_features", [])

    if not selected_features:
        selected_features = df.columns.tolist()

    X = df[selected_features]

    if target_series is not None:
        y = target_series
    else:
        y = None

    return X, y


# =========================
#  模型库
# =========================
def get_models(task_type, problem_type):

    models = {}

    # 分类
    if problem_type == "classification":
        models = {
            "logistic": LogisticRegression(max_iter=1000),
            "rf": RandomForestClassifier()
        }

        if XGBClassifier:
            models["xgb"] = XGBClassifier()

    # 回归
    elif problem_type == "regression":
        models = {
            "linear": LinearRegression(),
            "rf": RandomForestRegressor()
        }

        if XGBRegressor:
            models["xgb"] = XGBRegressor()

    return models


# =========================
#  训练 + 评估
# =========================
def train_and_evaluate(X, y, models, problem_type):

    results = []

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    for name, model in models.items():

        try:
            model.fit(X_train, y_train)

            preds = model.predict(X_test)

            if problem_type == "classification":
                score = accuracy_score(y_test, preds)
            else:
                score = -mean_squared_error(y_test, preds)

            results.append({
                "model": name,
                "score": score,
                "model_obj": model
            })

        except Exception as e:
            results.append({
                "model": name,
                "error": str(e)
            })

    return results


# =========================
# 🔥 选择最佳模型
# =========================
def select_best_model(results):

    valid = [r for r in results if "score" in r]

    if not valid:
        return None

    best = sorted(valid, key=lambda x: x["score"], reverse=True)[0]

    return best


# =========================
# 🔥 主入口
# =========================
def run(state):

    print("🤖 [MODEL AGENT] Training models...")

    decision = state.get("decision", {})
    task_type = decision.get("task_type")
    problem_type = state.get("selected_goal").problem_type

    X, y = prepare_data(state)

    # =========================
    # Tabular
    # =========================
    if task_type == "tabular":

        models = get_models(task_type, problem_type)

        results = train_and_evaluate(X, y, models, problem_type)

        best_model = select_best_model(results)

    # =========================
    # Time Series（简单版）
    # =========================
    elif task_type == "time_series":

        print("⏳ Using simple baseline for time series")

        best_model = {
            "model": "baseline_ts",
            "score": 0
        }
        results = []

    # =========================
    # NLP（简单版）
    # =========================
    elif task_type == "nlp":

        print("🧠 Using TF-IDF baseline")

        best_model = {
            "model": "tfidf_logistic",
            "score": 0
        }
        results = []

    # =========================
    # RL（不执行）
    # =========================
    elif task_type == "reinforcement_learning":

        print("⚠️ RL training not implemented")

        best_model = None
        results = []

    else:
        best_model = None
        results = []

    # =========================
    # 存结果
    # =========================
    state["model_results"] = results
    state["best_model"] = best_model

    print("✅ Model training done")

    if best_model:
        print(f"🏆 Best model: {best_model['model']}")

    return state