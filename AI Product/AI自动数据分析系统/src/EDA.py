import pandas as pd
import numpy as np

class EDAPipeline:

    def __init__(self, df, target=None):
        self.df = df
        self.target = target

    def run(self):
        return {
            "meta": self.meta_info(),
            "schema": self.schema_info(),
            "missing": self.missing_analysis(),
            "distribution": self.distribution_analysis(),
            "outliers": self.outlier_analysis(),
            "correlation": self.correlation_analysis(),
            "target_analysis": self.target_analysis(),
            "feature_insights": self.feature_insights()
        }

    # =========================
    # 1. Meta
    # =========================
    def meta_info(self):
        return {
            "rows": self.df.shape[0],
            "cols": self.df.shape[1]
        }

    # =========================
    # 2. Schema
    # =========================
    def schema_info(self):
        return {
            col: str(dtype)
            for col, dtype in self.df.dtypes.items()
        }

    # =========================
    # 3. Missing
    # =========================
    def missing_analysis(self):
        return {
            col: {
                "missing_rate": round(self.df[col].isnull().mean(), 4),
                "missing_flag": "high" if self.df[col].isnull().mean() > 0.3 else "low"
            }
            for col in self.df.columns
        }

    # =========================
    # 4. Distribution
    # =========================
    def distribution_analysis(self):
        result = {}

        for col in self.df.select_dtypes(include=np.number).columns:
            result[col] = {
                "mean": float(self.df[col].mean()),
                "std": float(self.df[col].std()),
                "skew": float(self.df[col].skew()),
                "kurtosis": float(self.df[col].kurt())
            }

        return result

    # =========================
    # 5. Outliers (IQR)
    # =========================
    def outlier_analysis(self):
        result = {}

        for col in self.df.select_dtypes(include=np.number).columns:
            q1 = self.df[col].quantile(0.25)
            q3 = self.df[col].quantile(0.75)
            iqr = q3 - q1

            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            outliers = self.df[(self.df[col] < lower) | (self.df[col] > upper)]

            result[col] = {
                "outlier_ratio": round(len(outliers) / len(self.df), 4)
            }

        return result

    # =========================
    # 6. Correlation
    # =========================
    def correlation_analysis(self):
        corr = self.df.corr(numeric_only=True)

        return corr.to_dict()

    # =========================
    # 7. Target Analysis
    # =========================
    def target_analysis(self):
        if not self.target or self.target not in self.df.columns:
            return {}

        result = {}
        for col in self.df.select_dtypes(include=np.number).columns:
            if col != self.target:
                result[col] = float(self.df[col].corr(self.df[self.target]))

        return result

    # =========================
    # 8. Feature Insights（AI用）
    # =========================
    def feature_insights(self):
        insights = []

        # missing
        for col, val in self.missing_analysis().items():
            if val["missing_rate"] > 0.3:
                insights.append({
                    "type": "missing",
                    "column": col,
                    "severity": "high",
                    "suggestion": "consider drop or imputation"
                })

        # skew
        for col, val in self.distribution_analysis().items():
            if abs(val["skew"]) > 1:
                insights.append({
                    "type": "skew",
                    "column": col,
                    "suggestion": "log transform recommended"
                })

        # outlier
        for col, val in self.outlier_analysis().items():
            if val["outlier_ratio"] > 0.05:
                insights.append({
                    "type": "outlier",
                    "column": col,
                    "suggestion": "consider capping or removal"
                })

        return insights