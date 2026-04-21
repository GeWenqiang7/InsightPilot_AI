import numpy as np


def analyze_outliers(df):
    result = {}
    num_cols = df.select_dtypes(include=np.number).columns

    for col in num_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outlier_count = ((df[col] < lower) | (df[col] > upper)).sum()
        result[col] = {"outlier_ratio": round(outlier_count / len(df), 4)}

    return result
