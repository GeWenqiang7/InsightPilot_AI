"""
可交互 Goal 闭环测试脚本

覆盖流程：
1) 上传/读取数据文件（CSV）
2) 输入需求
3) 生成 goal candidates
4) 交互式选择 goal 或追加需求重生成

默认使用 Mock LLM，避免依赖外部 API。
若需要可切换 --use-real-llm（需配置真实环境）。
"""

import argparse
import csv
import json
import os
import sys
import tempfile
from typing import Any, Dict, List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.goal.goal_manager import (  # noqa: E402
    display_goals,
    handle_goal_generation,
    init_goal_state,
    regenerate_goals,
    select_goal,
)
from src.knowledge.knowledge_manager import KnowledgeManager  # noqa: E402


def _infer_type(values: List[str]) -> str:
    non_empty = [v for v in values if v not in ("", None)]
    if not non_empty:
        return "string"

    def _is_int(x: str) -> bool:
        try:
            int(x)
            return True
        except ValueError:
            return False

    def _is_float(x: str) -> bool:
        try:
            float(x)
            return True
        except ValueError:
            return False

    if all(_is_int(v) for v in non_empty[:30]):
        return "int"
    if all(_is_float(v) for v in non_empty[:30]):
        return "float"
    return "string"


def load_csv_schema(data_path: str, sample_size: int = 200) -> Tuple[List[Dict[str, str]], int]:
    if not os.path.exists(data_path):
        raise FileNotFoundError("Data file not found: {0}".format(data_path))
    if not data_path.lower().endswith(".csv"):
        raise ValueError("Only CSV is supported in this script.")

    with open(data_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []
        samples: Dict[str, List[str]] = {name: [] for name in fieldnames}
        row_count = 0
        for row in reader:
            row_count += 1
            if row_count <= sample_size:
                for name in fieldnames:
                    samples[name].append(row.get(name, ""))

    columns = [{"name": name, "type": _infer_type(samples.get(name, []))} for name in fieldnames]
    return columns, row_count


class MockInteractiveLLM:
    def generate(self, prompt: str) -> str:
        low = prompt.lower()
        if "new:" in low or "new requirement" in low or "控制误报" in prompt:
            return """
[
  {
    "goal_id": 2,
    "goal_name": "控制误报并提升召回",
    "target": "label",
    "problem_type": "classification",
    "analysis_perspective": "风险-收益平衡",
    "business_value": "高",
    "model_candidates": [
      {"name":"XGBoost","category":"tree","reason":"非线性与鲁棒性较强"},
      {"name":"LogisticRegression","category":"linear","reason":"阈值与解释性好"}
    ],
    "evaluation_suggestions": {"primary_metric":"recall","secondary_metrics":["precision","f1"]},
    "risks": ["阈值敏感", "数据漂移"],
    "score": 0.94,
    "confidence": 0.87,
    "priority_rank": 1,
    "reason": "满足你最新的误报约束与召回诉求"
  },
  {
    "goal_id": 3,
    "goal_name": "客户分层运营策略",
    "target": null,
    "problem_type": "clustering",
    "analysis_perspective": "分群运营",
    "business_value": "中",
    "model_candidates": [{"name":"KMeans","category":"clustering","reason":"快速可执行"}],
    "evaluation_suggestions": {"primary_metric":"silhouette"},
    "risks": ["可解释性一般"],
    "score": 0.78,
    "confidence": 0.72,
    "priority_rank": 2,
    "reason": "可作为辅助策略"
  }
]
"""
        return """
[
  {
    "goal_id": 1,
    "goal_name": "预测用户流失概率",
    "target": "label",
    "problem_type": "classification",
    "analysis_perspective": "用户留存",
    "business_value": "高",
    "model_candidates": [
      {"name":"LogisticRegression","category":"linear","reason":"可解释、上线快"},
      {"name":"RandomForest","category":"tree","reason":"鲁棒性较好"}
    ],
    "evaluation_suggestions": {"primary_metric":"auc","secondary_metrics":["f1","recall"]},
    "risks": ["类别不平衡"],
    "score": 0.90,
    "confidence": 0.83,
    "priority_rank": 1,
    "reason": "可直接支持留存策略投放"
  },
  {
    "goal_id": 4,
    "goal_name": "识别高价值用户特征",
    "target": "label",
    "problem_type": "classification",
    "analysis_perspective": "用户价值洞察",
    "business_value": "中",
    "model_candidates": [{"name":"XGBoost","category":"tree","reason":"特征交互能力强"}],
    "evaluation_suggestions": {"primary_metric":"auc"},
    "risks": ["解释成本"],
    "score": 0.81,
    "confidence": 0.76,
    "priority_rank": 2,
    "reason": "可补充业务理解"
  }
]
"""


def _print_selected(state: Dict[str, Any]) -> None:
    selected = state["selected_goal"].to_dict()
    print("\n🎯 最终选定 Goal：")
    print(json.dumps(selected, indent=2, ensure_ascii=False))


def interactive_loop(data_path: str, use_real_llm: bool = False) -> None:
    columns, rows = load_csv_schema(data_path)
    schema_summary = {"rows": rows, "columns": columns}

    if use_real_llm:
        from src.llm.client import LLMClient  # 延迟导入，避免本地无依赖时报错

        llm_client = LLMClient()
    else:
        llm_client = MockInteractiveLLM()

    km = KnowledgeManager(llm_client=None)

    print("✅ 数据已加载")
    print("Path:", data_path)
    print("Rows:", rows)
    print("Columns:", len(columns))
    print("字段预览:", [c["name"] for c in columns[:8]])

    user_query = input("\n🧠 请输入分析需求：\n> ").strip()
    state = init_goal_state(df=None, user_query=user_query, knowledge_manager=km)
    state["schema"] = schema_summary

    while True:
        state = handle_goal_generation(state, llm_client)
        goals_json = display_goals(state)
        print("\n👉 输入规则：")
        print("- 输入 goal_id（数字）选择目标")
        print("- 输入 new:你的补充需求 重新生成")
        print("- 输入 exit 退出")
        user_input = input("> ").strip()

        if user_input.lower() == "exit":
            print("👋 已退出")
            return

        if user_input.startswith("new:"):
            new_query = user_input.replace("new:", "", 1).strip()
            if not new_query:
                print("⚠️ new: 后面请输入具体需求")
                continue
            state = regenerate_goals(state, "new: " + new_query, llm_client)
            continue

        try:
            goal_id = int(user_input)
            candidate_ids = [g.get("goal_id") for g in goals_json]
            if goal_id not in candidate_ids:
                print("❌ 无效 goal_id，可选:", candidate_ids)
                continue
            state = select_goal(state, goal_id)
            _print_selected(state)
            return
        except ValueError:
            print("❌ 输入格式错误，请输入数字 goal_id / new:xxx / exit")


def _build_temp_demo_csv() -> str:
    fd, path = tempfile.mkstemp(prefix="goal_loop_demo_", suffix=".csv")
    os.close(fd)
    with open(path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["user_id", "age", "income", "label"])
        writer.writerow([1, 23, 5000, 0])
        writer.writerow([2, 35, 12000, 1])
        writer.writerow([3, 29, 9000, 0])
        writer.writerow([4, 42, 15000, 1])
    return path


def demo_run(data_path: str) -> None:
    """
    非交互演示模式：自动走一遍流程，便于 CI/本地快速确认脚本逻辑。
    """
    source_path = data_path
    remove_after = False
    if not source_path or not os.path.exists(source_path):
        source_path = _build_temp_demo_csv()
        remove_after = True

    columns, rows = load_csv_schema(source_path)
    state = init_goal_state(
        df=None,
        user_query="我想预测流失",
        knowledge_manager=KnowledgeManager(llm_client=None),
    )
    state["schema"] = {"rows": rows, "columns": columns}
    llm_client = MockInteractiveLLM()

    state = handle_goal_generation(state, llm_client)
    first = display_goals(state)
    assert len(first) >= 1

    state = regenerate_goals(state, "new: 需要控制误报并提高召回", llm_client)
    second = display_goals(state)
    assert len(second) >= 1

    chosen_id = second[0]["goal_id"]
    state = select_goal(state, chosen_id)
    assert state["selected_goal"].goal_id == chosen_id
    print("interactive loop demo test passed")
    if remove_after and os.path.exists(source_path):
        os.remove(source_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive goal-loop test runner")
    parser.add_argument(
        "--data-path",
        type=str,
        default="",
        help="CSV data path for schema extraction",
    )
    parser.add_argument("--use-real-llm", action="store_true", help="use real LLM client instead of mock")
    parser.add_argument("--demo", action="store_true", help="run non-interactive demo mode")
    args = parser.parse_args()

    if args.demo:
        demo_run(args.data_path)
    else:
        interactive_loop(args.data_path, use_real_llm=args.use_real_llm)


if __name__ == "__main__":
    main()
