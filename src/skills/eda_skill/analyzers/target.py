def analyze_target(df, target_config):
    if isinstance(target_config, str) and target_config in df.columns:
        return df[target_config], {"type": "column", "name": target_config}

    if isinstance(target_config, str):
        try:
            target_series = df.eval(target_config)
            return target_series, {"type": "expression", "formula": target_config}
        except Exception:
            raise ValueError("Invalid target expression: {0}".format(target_config))

    if callable(target_config):
        target_series = target_config(df)
        description = target_config.__name__ if hasattr(target_config, "__name__") else "lambda"
        return target_series, {"type": "function", "description": description}

    raise ValueError("Unsupported target_config type")
