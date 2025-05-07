import pandas as pd

from config import EXCEL_PATH


def load_dataframe():
    df = pd.read_excel(EXCEL_PATH)
    if "Notes" not in df.columns:
        df["Notes"] = ""
    if "Case Done" not in df.columns:
        df["Case Done"] = ""
    return df


def save_dataframe(df):
    df.to_excel(EXCEL_PATH, index=False)
