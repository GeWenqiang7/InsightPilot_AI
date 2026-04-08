import os
import json
from openai import OpenAI

class FeatureEngineeringPromptBuilder:
    
    def __init__(self, eda_result, target):
        self.eda = eda_result
        self.target = target

#生成prompt
    def build(self):

        overview = self._build_overview()
        feature_summary = self._build_feature_summary()
        insights = self._build_insights()

        prompt = f"""
You are a senior data scientist.

This is a customer behavior dataset for predicting user spending.

Target variable: {self.target}

Business goal:
- Understand drivers of user spending
- Improve personalization / targeting

======================
[DATASET OVERVIEW]
{overview}

======================
[FEATURE SUMMARY]
{feature_summary}

======================
[KEY INSIGHTS FROM EDA]
{insights}

======================
Your task:
Generate an ADVANCED FEATURE ENGINEERING PLAN.

IMPORTANT:

Output ONLY valid JSON.

Format:

{
  "drop_columns": [],
  "feature_engineering": [],
  "encoding": [],
  "binning": [],
  "interaction": [],
  "ratio": [],
  "behavior": []
}

Definitions:

- interaction: combine two features (e.g., A * B)
- ratio: divide features (A / B)
- behavior: user behavior signals (e.g., active user, high frequency)

Rules:

- Include interaction features if meaningful
- Include ratio features for behavior modeling
- Include segmentation features (e.g., active users)
- Avoid only basic transformations
- Use exact column names
- Ignore ID/index-like columns (e.g., Unnamed, User_ID)
- Apply log transform for skewed features
- Handle outliers if needed
- Encode categorical features appropriately
- Avoid data leakage
"""

        return prompt

# 生成给LLM的prompt
    def _build_overview(self):
        meta = self.eda.get("meta", {})
        return f"""
- Number of rows: {meta.get("rows")}
- Number of features: {meta.get("cols")}
- Target variable: {self.target}
"""

    def _build_feature_summary(self):
        lines = []

        for col, info in self.eda.get("features", {}).items():

            dtype = info.get("type", {}).get("dtype")

            if dtype in ["int64", "float64"]:
                lines.append(
                    f"{col} (numeric): mean={info.get('mean')}, std={info.get('std')}, skew={info.get('skew')}, missing={info.get('missing')}"
                )
            else:
                lines.append(
                    f"{col} (categorical): unique={info.get('type', {}).get('n_unique')}, missing={info.get('missing')}"
                )

        return "\n".join(lines)


    def _build_insights(self):
        lines = []

        for item in self.eda.get("insights", []):
            lines.append(
                f"{item['column']}: {item['type']} → {item['action']}"
            )

        return "\n".join(lines)


# 保存并加载完整EDA.json结果
if __name__ == "__main__":

    target = "Total_Spending"

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    eda_path = os.path.join(BASE_DIR, "eda_for_llm.json")

    # ========= 1. 读取EDA =========
    with open(eda_path, "r") as f:
        eda_result = json.load(f)

    print("✅ EDA加载成功")

    # 构建Prompt
    builder = FeatureEngineeringPromptBuilder(eda_result, target)
    prompt = builder.build()

    # 保存prompt
    prompt_path = os.path.join(BASE_DIR, "fe_prompt.txt")
    with open(prompt_path, "w") as f:
        f.write(prompt)

    print(f"🧠 Prompt已保存: {prompt_path}")

    # 调用LLM 
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    result_text = response.choices[0].message.content

    # 尝试解析JSON
    try:
        fe_plan = json.loads(result_text)
        print("✅ JSON解析成功")
    except:
        print("⚠️ JSON解析失败，保存原始文本")
        fe_plan = None

    # 保存JSON
    json_path = os.path.join(BASE_DIR, "fe_plan.json")

    if fe_plan:
        with open(json_path, "w") as f:
            json.dump(fe_plan, f, indent=2)

        print(f"🔥 FE Plan已保存: {json_path}")

    # 保存fe执行计划json
    txt_path = os.path.join(BASE_DIR, "fe_suggestions.txt")

    with open(txt_path, "w") as f:
        f.write(result_text)

    print(f"📄 原始建议已保存: {txt_path}")

    # 输出
    print("\n========== LLM OUTPUT ==========\n")
    print(result_text)