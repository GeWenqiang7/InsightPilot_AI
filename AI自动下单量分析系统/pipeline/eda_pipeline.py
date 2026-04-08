# pipeline/eda_pipeline.py

from src.eda.profiler import get_meta_info, get_schema_info
from src.eda.missing import analyze_missing
from src.eda.distribution import analyze_distribution
from src.eda.outlier import detect_outliers
from src.eda.correlation import analyze_correlation
from src.eda.target import analyze_target
from src.eda.insights import generate_feature_insights

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

        # target解析
        target_series, target_meta = analyze_target(self.df, self.target)

        # 传入target做相关性
        corr = analyze_correlation(self.df, target_series)

        insights = generate_feature_insights(missing, dist, outliers)

        return {
            "meta": meta,
            "schema": schema,
            "missing": missing,
            "distribution": dist,
            "outliers": outliers,
            "correlation": corr,
            "target_analysis": target_meta,
            "feature_insights": insights
        }