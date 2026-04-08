#转json工具
import numpy as np
import pandas as pd

def make_json_serializable(obj):
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]

    elif isinstance(obj, pd.Series):
        return obj.to_dict()

    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict()

    elif isinstance(obj, np.ndarray):
        return obj.tolist()

    elif isinstance(obj, (np.int64, np.float64)):
        return obj.item()

    else:
        return obj