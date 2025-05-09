import polars
from answer_generator.ai_answer_module import AIAnswerer
from answer_generator.profile_parser import load_profile, load_q_sheet

def test1():
    print("--- Testing AIAnswerer Class ---")
    test_profile = {'name': 'テストユーザー', '年齢': '30', '性別': '女性', '職業': 'エンジニア'}
    # _restructure_profile はクラスの内部メソッドになるため、直接テストする場合はインスタンスが必要
    # print("Input Profile:", test_profile)
    # print("Restructured Profile:\n", AIAnswerer._restructure_profile(None, test_profile)) # 非推奨なテスト方法
    print("-" * 30)

    print("--- Testing get_ai_answers method ---")
    # テスト用のダミーデータ
    # 注意: 実際にAIに問い合わせるには、環境変数に適切なAPIキーが設定されている必要があります。
    test_selected_model = 'gpt-4o-mini' # または利用可能なモデル
    test_profile_for_ai = {'name': 'b883da38-ed1f-430a-b9f9-3ce7bfbbcd1d',
               '年齢': '16',
               '性別': '男性',
               '血液型': 'O型',
               '国籍': '日本'}
    test_question = [{'No':'q1','Question':'あなたは几帳面で、細部にまで注意を払いますか？','Option':'強くそう思う|ややそう思う|どちらとも言えない|あまりそう思わない|まったくそう思わない'},
                     {'No':'q2','Question':'あなたは、自分の責任や約束に対して強い責任感を感じますか？','Option':'強くそう思う|ややそう思う|どちらとも言えない|あまりそう思わない|まったくそう思わない'}]

    # 共通プロンプトと質問テンプレートを統合した新しいベースプロンプトテンプレート
    # profile_text, question_text, options_text のプレースホルダーを含む
    test_base_prompt_template = """あなたは{profile_text}です。

以下の質問に、提示された選択肢の中から最も適切なものを一つだけ選んで回答してください。回答は選択肢のテキストそのものにしてください。

質問: {question_text}
選択肢: {options_text}

回答:
"""

    print(f"Using model: {test_selected_model}")
    print("Profile for AI:", test_profile_for_ai)
    print("Questions:", test_question)
    print("Base Prompt Template:", test_base_prompt_template)


    try:
        print("\nInitializing AIAnswerer...")
        answerer = AIAnswerer(selected_model=test_selected_model)

        print("\nCalling get_ai_answers method (include_previous_answers=False)...")
        test_answer_dict = answerer.get_ai_answers(
            profile=test_profile_for_ai,
            question_list=test_question,
            base_prompt_template=test_base_prompt_template,
            include_previous_answers=False # 各質問間独立＝False
        )
        print("\nResulting answer_dict:", test_answer_dict)

    except ValueError as ve:
        print(f"\nError during get_ai_answers test: {ve}")
        print("Please ensure the necessary API key environment variable is set.")
    except Exception as e:
        print(f"\nAn unexpected error occurred during get_ai_answers test: {e}")

    print("-" * 30)

def test2():
    # プロンプトロード
    base_prompt_path = "prompt\prompt_common_JP.txt"
    with open(base_prompt_path, "r", encoding="utf-8") as f:
        base_prompt = f.read()

    # 質問項目ロード
    q_path = r"Q_sheet_JP.xlsx"
    questions_list:list[dict] = load_q_sheet(q_path)

    # モデル
    model = 'gemini-1.5-pro'

    # プロフィールロード
    p_path = r"F:\GPT_for_LargeSim\profiles\blood_more\blood_more_20250507_1000_A - コピー.xlsx"
    profile_list:list[dict] = load_profile(p_path)

    for num, profile in enumerate(profile_list):
        import time
        t1 = time.time()
        #print(f"Using model: {model}")
        #print("Profile for AI:", profile)
        #print("Questions:", questions_list)
        #print("Base Prompt Template:", base_prompt)
        print(f"{num+1}/1000")
    
        answerer = AIAnswerer(selected_model=model)

        answer_dict = answerer.get_ai_answers(
            profile=profile,
            question_list=questions_list,
            base_prompt_template=base_prompt,
            include_previous_answers=False # 各質問間独立＝False
        )

        for anwser_key, answer_value in answer_dict.items():
            profile_list[num][anwser_key] = answer_value
        print(f"{time.time()-t1:.2f}")

    df_anwser = polars.DataFrame(profile_list)
    df_anwser.write_excel("test_less_A.xlsx")

# テストブロック (クラスを使用する場合)
if __name__ == "__main__":
    #test1()

    test2()