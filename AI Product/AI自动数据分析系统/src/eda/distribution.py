#数据分布

import numpy as np

def analyze_distribution(df):
    result = {}

    num_cols = df.select_dtypes(include=np.number).columns

    for col in num_cols:
        result[col] = {
            "mean": float(df[col].mean()),
            "std": float(df[col].std()),
            "skew": float(df[col].skew()),
            "kurtosis": float(df[col].kurt())
        }

    return result