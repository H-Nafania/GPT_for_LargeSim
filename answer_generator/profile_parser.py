import pandas as pd
import polars as pl
from pprint import pprint

def load_profile(excel_file) -> list[dict]:
    """
    Excelファイルを読み込み、指定された列のデータを抽出します。

    Args:
        excel_file (str): Excelファイルのパス。

    Returns:
        polars.DataFrame: 抽出されたデータを含むDataFrame。
    """
    try:
        df = pl.read_excel(excel_file)
        df_dicts = df.to_dicts()

        return df_dicts

    except FileNotFoundError:
        raise FileNotFoundError(f"ファイル '{excel_file}' が見つかりません。")
    except Exception as e:
        raise Exception(f"Excelファイルの読み込み中にエラーが発生しました: {e}")

def load_q_sheet(excel_file) -> list[dict]:
    try:
        df = pl.read_excel(excel_file)
        if df.columns != ["No", "Question", "Option"]:
            raise ValueError("Q_sheetの構造が")
        df_dicts = df.to_dicts()

        return df_dicts
    
    except FileNotFoundError:
        raise FileNotFoundError(f"ファイル '{excel_file}' が見つかりません。")
    except Exception as e:
        raise Exception(f"Excelファイルの読み込み中にエラーが発生しました: {e}")

if __name__ == "__main__":

    from pprint import pprint

    path = r"profiles\A\A_20250506_500.xlsx"
    pprint(load_profile(path))

    path_sheet = r"Q_sheet_JP.xlsx"
    pprint(load_q_sheet(path_sheet))