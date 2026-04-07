from .profiler import get_meta_info, get_schema_info
from .missing import analyze_missing
from .distribution import analyze_distribution
from .outlier import detect_outliers
from .correlation import analyze_correlation
from .target import analyze_target
from .insights import generate_feature_insights


class EDAPipeline:

    def __init__(self, df, target=None):
        self.df = df
        self.target = target

    def run(self):
        meta = get_meta_info(self.df)
        schema = get_schema_info(self.df)
        missing = analyze_missing(self.df)
        dist = analyze_distribution(self.df)
        outliers = detect_outliers(self.df)
        corr = analyze_correlation(self.df)
        target_info = analyze_target(self.df, self.target)

        insights = generate_feature_insights(missing, dist, outliers)

        return {
            "meta": meta,
            "schema": schema,
            "missing": missing,
            "distribution": dist,
            "outliers": outliers,
            "correlation": corr,
            "target_analysis": target_info,
            "feature_insights": insights
        }