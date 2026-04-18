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
