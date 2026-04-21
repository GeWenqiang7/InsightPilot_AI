def get_meta_info(df):
    return {"rows": df.shape[0], "cols": df.shape[1]}


def get_schema_info(df):
    return {
        col: {
            "dtype": str(df[col].dtype),
            "n_unique": int(df[col].nunique()),
        }
        for col in df.columns
    }
