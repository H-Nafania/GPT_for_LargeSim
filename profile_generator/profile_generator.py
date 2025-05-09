from modules import config_loader
from profile_generator import profile_setting_parser
import os
import polars as pl

# ai_handler から移動したインポート
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from tenacity import retry, stop_after_attempt, wait_random_exponential
from typing import Optional

import datetime

class ProfileGenerator:
    def __init__(self, excel_file, default_temperature=0.0):
        """
        ProfileGeneratorクラスの初期化。

        Args:
            excel_file (str): Excelファイルのパス。
            default_temperature (float): AIモデルのデフォルト温度。
        """
        self.df = profile_setting_parser.load_and_extract_data(excel_file)
        self.individual_dict:dict = {}  # {name_code1: {profile1}, ...}
        self.df_dict:dict = {}          # {col1: [values1], col2:[values2], ...}
        self.df_profile:pl.DataFrame = pl.DataFrame()
        self.default_temperature:float = default_temperature
        # ai_handler から移動したAPIキー初期化
        self.openai_api_key = config_loader.get_api_key("chatgpt")
        if self.openai_api_key is None:
            print("OpenAI のAPIキーが設定されていません。AIモデルは利用できません。")

    def _initialize_llm(self, model_name: str, temperature: Optional[float]):
        """
        OpenAIモデルのインスタンスを初期化します。
        """
        if self.openai_api_key is None:
             raise ValueError("OpenAI のAPIキーが設定されていません。")

        # gpt-4o または gpt-4o-mini のみを受け入れる
        if model_name not in ["gpt-4o", "gpt-4o-mini"]:
             print(f"警告: サポートされていないモデル名 '{model_name}' が指定されました。デフォルトの 'gpt-4o-mini' を使用します。")
             model_name = "gpt-4o-mini"

        return ChatOpenAI(
            model=model_name,
            api_key=self.openai_api_key,
            temperature=temperature if temperature is not None else self.default_temperature,
        )

    # ai_handler から移動したメソッド
    @retry(stop=stop_after_attempt(3), wait=wait_random_exponential(min=1, max=60))
    def _generate_from_ai(self, model_name: str, prompt_instruction: str):
        """
        LangChainを使用してプロフィールを生成します（OpenAI専用）。
        JsonOutputParserを使用します。
        """
        model = self._initialize_llm(model_name, self.default_temperature)

        output_parser = JsonOutputParser()
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "あなたはJSON形式で人物プロファイルを生成するAIです。回答は必ず以下のJSON形式で記述してください: {{\"年齢\": 25, \"職業\": \"エンジニア\", ...}}。"),
            ("user", "{instruction}")
        ])

        chain = prompt_template | model | output_parser

        try:
            response = chain.invoke({"instruction": prompt_instruction})
            return response
        except Exception as e:
            # エラー発生時もリトライのために例外を再発生させる
            raise Exception(f"エラー: JSON形式のプロファイルの生成に失敗しました: {e}")


    def generate_profiles(self, names: list, model_name="gpt-4o", batch_size: int = 50) -> dict:
        """
        名前のリストを受け取り、バッチごとにプロファイルを生成します。

        Args:
            names (list): 名前のリスト。
            model_name (str): 使用するAIモデルの名前。デフォルトは "gpt-4o"。
            temperature (float): AIの出力の多様性を制御するパラメータ。デフォルトは None (クラスのデフォルト温度を使用)。
            batch_size (int): 一度に生成するプロファイルの数。デフォルトは 50。

        Returns:
            dict: 生成されたプロファイルの辞書
        """
        all_generated_profiles = {}
        num_names = len(names)

        for i in range(0, num_names, batch_size):
            batch_names = names[i:i + batch_size]
            print(f"プロフィール生成、グループ {i//batch_size + 1}/{(num_names + batch_size - 1) // batch_size} ({len(batch_names)} names)...")

            try:
                # プロンプトを生成する
                attribute_instructions = ""
                for index, row in self.df.iterrows():
                    attribute_name = row['属性名']
                    custom_setting = row['カスタム設定']
                    range_category_scale = row['範囲 / カテゴリー / スケール']

                    # カスタム設定がnanの場合は「完全ランダムに生成」という指示を追加
                    if custom_setting is None or str(custom_setting).lower() == 'nan':
                        custom_setting_instruction = "完全ランダムに生成"
                    else:
                        custom_setting_instruction = custom_setting

                    attribute_instructions += f"- 属性名: {attribute_name}, 条件: {range_category_scale}, カスタム設定: {custom_setting_instruction}\n"

                prompt_instruction = f"""
以下の属性を持つ人物プロファイルをJSON形式で生成してください。
JSON形式で、キーが属性名、バリューが生成された値であること。
生成される値は、可能な限り多様でユニークになるようにしてください。
各人物の名前or番号は以下の通りです: {", ".join(batch_names)}
出力例: {{"太郎": {{"年齢": 25, "職業": "エンジニア"}}, "花子": {{"年齢": 30, "職業": "デザイナー"}}}}
{attribute_instructions}
"""

                # AIにプロンプトを送信してプロファイルを生成する (ai_handlerのメソッドをselfのメソッドに変更)
                batch_profiles = self._generate_from_ai(model_name, prompt_instruction)
                # generate_profile_from_ai は JsonOutputParser を使うので、通常は辞書が返る

                # 生成されたプロファイルを統合
                all_generated_profiles.update(batch_profiles)

            except Exception as e:
                print(f"Error generating profiles for batch starting with {batch_names[0]}: {e}")
                # エラーが発生した場合でも、これまでに生成されたプロファイルは保持する

        self.individual_dict = all_generated_profiles
        return all_generated_profiles

    def reform_profile(self, profiles: dict) -> None:
        """
        生成されたプロファイルを self.dict に保存します。

        Args:
            profiles (dict): 生成されたプロファイルの辞書。
        """
        # Excelファイルから読み込んだ全ての属性名をキーとしてself.dictを初期化
        if self.df_dict == {}:
            all_attribute_names = self.df['属性名'].tolist()
            self.df_dict = {attr_name: [] for attr_name in all_attribute_names}
            self.df_dict["name_code"] = []

        all_attribute_names = self.df['属性名'].tolist()

        for name, profile in profiles.items():
            self.df_dict["name_code"].append(name)
            for attr_name in all_attribute_names:
                # AIの応答に含まれていればその値を使用、含まれていなければNoneを使用
                v = profile.get(attr_name, None)
                self.df_dict[attr_name].append(v) # Corrected indentation

        self.df_profile = pl.DataFrame(self.df_dict, strict=False)
        return self.df_profile

    def export_profile(self, export_folder):
        if self.df_profile.is_empty():
            return None
        if not os.path.exists(export_folder):
            return None
        
        filename = "_".join([os.path.basename(export_folder), datetime.date.today().strftime("%Y%m%d"), str(self.df_profile.shape[0])]) + ".xlsx"
        if os.path.exists(filename):
            filename = "_".join([os.path.basename(export_folder), datetime.date.today().strftime("%Y%m%d"), str(self.df_profile.shape[0])]) + f"_({len(os.listdir(export_folder))+1}).xlsx"
        
        path = os.path.join(export_folder, filename)
        self.df_profile.write_excel(path)

        return True
