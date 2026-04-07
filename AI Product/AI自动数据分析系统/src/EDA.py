import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

data_path = os.path.join(
    BASE_DIR,
    '..',
    '..',
    'douyinshop_data',
    'user_personalized_features.csv'
)

df = pd.read_csv(data_path)

df = df.drop(df.columns[:2], axis=1)

#数据总体信息
def auto_eda(df):
    eda_result = {}

    # 1. 基本信息
    eda_result["shape"] = {
        "rows": df.shape[0],
        "cols": df.shape[1]
    }

    eda_result["columns"] = list(df.columns)

    eda_result["dtypes"] = {
        col: str(dtype) for col, dtype in df.dtypes.items()
    }

    # 2. 缺失率（比 count 更有用）
    eda_result["missing_rate"] = {
        col: round(df[col].isnull().mean(), 4)
        for col in df.columns
    }

    # 3. 数值统计（只选 numeric）
    eda_result["describe"] = df.describe().to_dict()

    return eda_result

#检查缺失值
def detect_problem(eda):
    if "missing_rate" not in eda:
        raise ValueError("输入不是EDA结果，请传入auto_eda输出")

    issues = []

    for col, rate in eda["missing_rate"].items():
        if rate > 0.3:
            issues.append(f"{col} 缺失严重")

    return issues

if __name__ == "__main__":
    result = auto_eda(df)

    print(result)

    print("\n问题检测：")
    print(detect_problem(result))  