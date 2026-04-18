'''
测试目标生成流程
目的：
- 验证从用户输入到目标生成的完整流程是否正常工作
- 确保生成的目标符合预期的结构和内容要求
流程：
1. 初始化系统：创建LLM客户端和知识管理器实例
2. 模拟用户输入：定义一个用户查询和数据集schema
3. 生成目标：调用handle_goal_generation函数生成分析目标 
4. 输出结果：打印生成的目标列表，验证其正确性
使用说明：
1. 确保已安装必要的依赖（如openai等）。
2. 运行脚本：python test_goal_generator.py
3. 查看输出的分析目标列表，验证其正确性和合理性。
'''


import sys
import os
import json
 
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

 
from src.goal.goal_manager import (
    init_goal_state,
    handle_goal_generation,
    display_goals,
    select_goal,
    regenerate_goals,
    reset_state
)

from src.llm.client import LLMClient
from src.knowledge.knowledge_manager import KnowledgeManager


# =========================
# 🔥 主流程
# =========================
def main():

    print("\n🚀 AI Data Analysis System Started")

    # 🔥 初始化 LLM + RAG
    llm = LLMClient()
    km = KnowledgeManager(llm_client=llm)

    # 🔥 模拟 schema（后面你可以换成真实EDA输出）
    schema_summary = {
        "columns": [
            {"name": "user_id", "type": "int"},
            {"name": "age", "type": "int"},
            {"name": "spending", "type": "float"},
            {"name": "is_churn", "type": "int"}
        ]
    }

    # =========================
    # 🔥 Step 1：用户初始输入
    # =========================
    user_query = input("\n请输入你的分析需求：\n> ")

    state = init_goal_state(df=None, user_query=user_query, knowledge_manager=km)
    state["schema"] = schema_summary

    # =========================
    # 🔥 主循环（核心）
    # =========================
    while True:

        # 生成 goals
        state = handle_goal_generation(state, llm)

        # 展示
        display_goals(state)

        # 用户输入
        user_input = input(
            "\n请输入操作：\n"
            "👉 输入 goal_id 选择目标\n"
            "👉 输入 new:xxx 修改需求\n"
            "👉 输入 exit 退出\n> "
        )

        # =========================
        # 🔥 exit
        # =========================
        if user_input.lower() == "exit":

            state = reset_state(state)

            print("\n👋 已退出系统")
            break

        # =========================
        # 🔥 修改需求
        # =========================
        elif user_input.startswith("new:"):

            new_query = user_input.replace("new:", "").strip()

            state = regenerate_goals(state, new_query, llm)

            continue

        # =========================
        # 🔥 选择 goal
        # =========================
        else:
            try:
                goal_id = int(user_input)

                state = select_goal(state, goal_id)

                print("\n🎯 最终选定 Goal：")
                print(
                    json.dumps(
                        state["selected_goal"].to_dict(),
                        indent=2,
                        ensure_ascii=False
                        )
                    )

                break

            except Exception as e:
                print("❌ 输入无效，请重试")


# =========================
# 🔥 运行入口
# =========================
if __name__ == "__main__":
    main()