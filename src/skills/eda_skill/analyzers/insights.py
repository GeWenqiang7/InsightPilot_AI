def generate_feature_insights(missing, dist, outliers):
    insights = []

    for col, val in missing.items():
        if val["missing_rate"] > 0.3:
            insights.append({"type": "missing", "column": col, "action": "drop_or_impute"})

    for col, val in dist.items():
        if abs(val["skew"]) > 1:
            insights.append({"type": "skew", "column": col, "action": "log_transform"})

    for col, val in outliers.items():
        if val["outlier_ratio"] > 0.05:
            insights.append({"type": "outlier", "column": col, "action": "cap_or_remove"})

    return insights
