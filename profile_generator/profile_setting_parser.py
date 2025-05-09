import pandas as pd

def load_and_extract_data(excel_file):
    """
    Excelファイルを読み込み、指定された列のデータを抽出します。

    Args:
        excel_file (str): Excelファイルのパス。

    Returns:
        pandas.DataFrame: 抽出されたデータを含むDataFrame。
    """
    try:
        df = pd.read_excel(excel_file, sheet_name=0)  # 最初のシートを読み込む
        # 必要な列
        required_columns = ['属性名', '使用する項目に「1」', 'カスタム設定', '範囲 / カテゴリー / スケール']
        # 列が存在するか確認
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"必要な列 '{col}' がExcelファイルにありません。")

        # 「使用する項目に「1」」列が1である行のみを抽出
        df = df[df['使用する項目に「1」'] == 1]

        # 必要な列のみを選択
        df = df[required_columns]

        return df

    except FileNotFoundError:
        raise FileNotFoundError(f"ファイル '{excel_file}' が見つかりません。")
    except Exception as e:
        raise Exception(f"Excelファイルの読み込み中にエラーが発生しました: {e}")
