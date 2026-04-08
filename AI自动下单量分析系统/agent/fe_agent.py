import json
from openai import OpenAI


class FeatureEngineeringAgent:

    def __init__(self, model="gpt-4.1"):
        self.client = OpenAI()
        self.model = model

    def build_prompt(self, eda_data, target):

        prompt = f"""
You are a senior data scientist.

This dataset is used for predicting: {target}

Here is the EDA summary:

{json.dumps(eda_data, indent=2)}

======================

Your task:
Generate a FEATURE ENGINEERING PLAN.

======================

IMPORTANT:
Output ONLY valid JSON in the following format:

{{
  "drop_columns": [],
  "feature_engineering": [
    {{
      "column": "",
      "action": "",
      "params": {{}}
    }}
  ],
  "encoding": [
    {{
      "column": "",
      "method": ""
    }}
  ],
  "binning": [
    {{
      "column": "",
      "bins": []
    }}
  ]
}}

======================

Rules:

1. Drop useless columns (IDs, index-like columns)
2. Apply log transform for skewed features
3. Handle outliers if needed
4. Encode categorical features appropriately
5. Avoid data leakage
6. Use specific column names from the dataset

ONLY RETURN JSON. NO TEXT.
"""

        return prompt

    def run(self, eda_data, target):

        prompt = self.build_prompt(eda_data, target)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        result_text = response.choices[0].message.content

        # 👉 尝试解析JSON（关键）
        try:
            result_json = json.loads(result_text)
        except Exception:
            print("⚠️ JSON解析失败，返回原始文本")
            return result_text

        return result_json