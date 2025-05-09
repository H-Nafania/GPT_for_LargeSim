import pandas as pd

class ResultsExporter:
    def export_results(self, all_results, output_excel_path):
        """
        シミュレーション結果をExcelファイルに出力します。
        """
        df = pd.DataFrame.from_dict(all_results, orient='index')
        df.to_excel(output_excel_path)

    def export_profiles(self, profile_folder, output_excel_path):
        """
        プロフィール一覧をExcelファイルに出力します。
        """
        # TODO: プロファイル一覧をExcelに出力するロジックを実装
        pass
