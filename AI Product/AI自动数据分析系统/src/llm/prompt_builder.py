class FeatureEngineeringPromptBuilder:
    
    def __init__(self, eda_result, target):
        self.eda = eda_result
        self.target = target

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

Your tasks:

1. Feature engineering suggestions
2. Data cleaning recommendations
3. Feature selection strategy
4. Modeling approach

Requirements:
- Mention specific feature names
- Identify skewed / high variance / high cardinality features
- Suggest transformations (log, binning, encoding)
- Detect useless features (e.g., IDs)
- Highlight potential leakage
- Output structured bullet points

IMPORTANT:
- Ignore index-like columns (e.g., Unnamed, IDs)
"""
        return prompt

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
    
if __name__ == "__main__":

    import json
    import os
    from openai import OpenAI

    target = "Total_Spending"

    # ========= 1. 读取EDA =========
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_path = os.path.join(BASE_DIR, "eda_for_llm.json")

    with open(file_path, "r") as f:
        eda_result = json.load(f)

    print("✅ EDA加载成功")

    # ========= 2. 构建Prompt =========
    builder = FeatureEngineeringPromptBuilder(eda_result, target)
    prompt = builder.build()

    # 保存prompt（debug用）
    prompt_path = os.path.join(BASE_DIR, "fe_prompt.txt")
    with open(prompt_path, "w") as f:
        f.write(prompt)

    print(f"🧠 Prompt已保存: {prompt_path}")

    # ========= 3. 调用LLM =========
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    result_text = response.choices[0].message.content

    # ========= 4. 保存LLM输出 =========
    output_path = os.path.join(BASE_DIR, "fe_suggestions.txt")

    with open(output_path, "w") as f:
        f.write(result_text)

    print(f"🚀 Feature Engineering建议已生成: {output_path}")

    # 终端打印
    print("\n========== LLM OUTPUT ==========\n")
    print(result_text)