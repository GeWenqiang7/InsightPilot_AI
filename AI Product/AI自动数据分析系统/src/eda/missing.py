#缺失值探查

def analyze_missing(df, threshold=0.3):
    result = {}

    for col in df.columns:
        rate = df[col].isnull().mean()

        result[col] = {
            "missing_rate": round(rate, 4),
            "missing_flag": "high" if rate > threshold else "low"
        }

    return result