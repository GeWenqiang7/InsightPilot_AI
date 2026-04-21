import numpy as np


def compute_correlation_matrix(df):
    return df.corr(numeric_only=True)


def get_high_corr_pairs(corr_matrix, threshold=0.8):
    pairs = []
    cols = corr_matrix.columns

    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            col1, col2 = cols[i], cols[j]
            corr = corr_matrix.loc[col1, col2]

            if abs(corr) >= threshold:
                pairs.append(
                    {
                        "feature_1": col1,
                        "feature_2": col2,
                        "correlation": float(corr),
                    }
                )

    return pairs


def detect_multicollinearity_groups(high_corr_pairs):
    groups = []

    for pair in high_corr_pairs:
        f1 = pair["feature_1"]
        f2 = pair["feature_2"]

        found = False
        for group in groups:
            if f1 in group or f2 in group:
                group.update([f1, f2])
                found = True
                break

        if not found:
            groups.append(set([f1, f2]))

    return [list(group) for group in groups]


def compute_feature_target_corr(df, target_series):
    result = {}

    for col in df.select_dtypes(include=np.number).columns:
        if col != target_series.name:
            try:
                result[col] = float(df[col].corr(target_series))
            except Exception:
                result[col] = None

    return result


def get_top_features(feature_target_corr, top_k=10):
    sorted_features = sorted(
        feature_target_corr.items(),
        key=lambda item: abs(item[1]) if item[1] is not None else 0,
        reverse=True,
    )

    return [{"feature": key, "correlation": value} for key, value in sorted_features[:top_k]]


def analyze_correlation(df, target_series=None):
    corr_matrix = compute_correlation_matrix(df)
    high_corr_pairs = get_high_corr_pairs(corr_matrix)
    multicollinearity_groups = detect_multicollinearity_groups(high_corr_pairs)

    result = {
        "pairwise_correlation": corr_matrix.to_dict(),
        "high_correlation_pairs": high_corr_pairs,
        "multicollinearity_groups": multicollinearity_groups,
    }

    if target_series is not None:
        feature_target_corr = compute_feature_target_corr(df, target_series)
        result["feature_target_correlation"] = feature_target_corr
        result["top_features"] = get_top_features(feature_target_corr)

    return result
