import os
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser # 必要に応じて使用
from pydantic import BaseModel, Field # 必要に応じて使用
from modules import config_loader

class AIAnswerer:
    def __init__(self, selected_model: str):
        """
        AIモデルを初期化し、answer_dictを準備します。
        """
        self.llm = self._initialize_llm(selected_model)
        self.answer_dict: Dict[str, str] = {} # インスタンス変数として保持

    def _initialize_llm(self, selected_model: str) -> Any:
        """
        選択されたモデルに基づいてLangchainのLLMインスタンスを初期化します。
        """
        llm = None
        if selected_model.startswith('gpt'): # OpenAIモデル
            if not os.environ.get("OPENAI_API_KEY"):
                 raise ValueError("OPENAI_API_KEY environment variable not set.")
            llm = ChatOpenAI(model=selected_model, api_key=os.environ.get("OPENAI_API_KEY"))
        elif selected_model.startswith('gemini'): # Google Geminiモデル
            if not os.environ.get("GEMINI_API_KEY"):
                 raise ValueError("GEMINI_API_KEY environment variable not set.")
            llm = ChatGoogleGenerativeAI(model=selected_model, google_api_key=os.environ.get("GEMINI_API_KEY"))
        elif selected_model.startswith('claude'): # Anthropic Claudeモデル
            if not os.environ.get("ANTHROPIC_API_KEY"):
                 raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
            llm = ChatAnthropic(model=selected_model, api_key=os.environ.get("ANTHROPIC_API_KEY"))
        # 他のモデルもここに追加

        if llm is None:
            raise ValueError(f"Unsupported model: {selected_model}")
        return llm

    def _restructure_profile(self, profile: Dict[str, str]) -> str:
        """
        profile辞書を「キー: 値」形式の文字列に変換します。
        """
        return "\n".join([f"{key}: {value}" for key, value in profile.items()])

    def _structure_answers(self) -> str:
        """
        現在のanswer_dictの内容を構造化されたテキスト形式に変換します。
        """
        if not self.answer_dict:
            return "" # 回答がない場合は空文字列を返す

        structured_text = "--- 過去の回答 ---\n"
        for q_key, answer in self.answer_dict.items():
            structured_text += f"{q_key}: {answer}\n"
        structured_text += "------------------\n"
        return structured_text

    def _get_single_answer(
        self,
        full_prompt_text: str, # 構築済みの完全なプロンプトテキストを受け取る
        options: List[str],
    ) -> str:
        """
        単一の質問に対してAIに問い合わせ、回答を取得・解析します。
        """
        prompt = ChatPromptTemplate.from_messages([
            HumanMessage(content=full_prompt_text)
        ])

        chain = prompt | self.llm
        response = chain.invoke({})
        ai_response_text = response.content.strip()

        matched_option = None
        for option in options:
            if option in ai_response_text:
                matched_option = option
                break

        if matched_option:
            return matched_option
        else:
            # Warningメッセージを修正: full_prompt_textではなくquestion_textを表示
            # ただし、_get_single_answerはquestion_textを直接受け取らないため、
            # ここではfull_prompt_textの一部を表示するか、警告をシンプルにする
            # 例として、警告をシンプルにします。
            print(f"Warning: AI response '{ai_response_text}' did not match any option.")
            return "解析失敗"

    def get_ai_answers(
        self,
        profile: Dict[str, str],
        question_list: List[Dict[str, str]], # 変更: パラメータ名と型
        base_prompt_template: str,
        include_previous_answers: bool = False
    ) -> Dict[str, str]:
        """
        AIモデルを使用して各質問に回答させ、結果をanswer_dict形式で返します。
        新しい入力形式: List[Dict[str, str]] に対応
        """
        profile_text = self._restructure_profile(profile)
        # 新しい質問セットのためにanswer_dictをリセットし、新しいキーで初期化
        self.answer_dict = {item['No']: "" for item in question_list}

        for question_data in question_list: # 変更: リストをイテレート
            q_key = question_data['No']
            question_text = question_data['Question']
            option_string = question_data['Option'] # 変更: Option文字列を取得

            # 質問タイプ（選択式 or 自由記述）を判定し、プロンプトに含める部分を決定
            if '|' in option_string:
                # 選択式質問
                options_list = option_string.split('|')
                options_text_for_prompt = ', '.join(options_list)
                prompt_options_part = f"選択肢: {options_text_for_prompt}"
                is_multiple_choice = True
            else:
                # 自由記述質問
                instruction_text = option_string
                prompt_options_part = f"指示: {instruction_text}"
                is_multiple_choice = False

            # 現在の質問に対するベースプロンプトを構築
            current_question_prompt_text = base_prompt_template.format(
                profile_text=profile_text,
                question_text=question_text,
                options_text=prompt_options_part # 決定したプロンプト部分を使用
            )

            # include_previous_answers が True の場合、過去の回答をプロンプトに追記
            # 現在の質問より前の回答を含める（元のロジックを踏襲）
            if include_previous_answers and self.answer_dict:
                # 現在の質問キーを一時的に削除して、_structure_answersに含めないようにする
                current_answer_temp = self.answer_dict.pop(q_key, None)
                structured_answers = self._structure_answers()
                if current_answer_temp is not None:
                    self.answer_dict[q_key] = current_answer_temp # 削除したキーを元に戻す

                if structured_answers:
                    full_prompt_text = f"{structured_answers}\n{current_question_prompt_text}"
                else:
                    full_prompt_text = current_question_prompt_text
            else:
                full_prompt_text = current_question_prompt_text

            try:
                if is_multiple_choice:
                    # 選択式の場合は既存の _get_single_answer を使用
                    answer = self._get_single_answer(
                        full_prompt_text=full_prompt_text,
                        options=options_list, # 選択肢リストを渡す
                    )
                else:
                    # 自由記述の場合はLLMを直接呼び出し
                    prompt = ChatPromptTemplate.from_messages([
                        HumanMessage(content=full_prompt_text)
                    ])
                    chain = prompt | self.llm
                    response = chain.invoke({})
                    answer = response.content.strip() # AIの生レスポンスを回答とする

                self.answer_dict[q_key] = answer # 回答を格納

            except Exception as e:
                print(f"Error processing question '{question_text}': {e}")
                self.answer_dict[q_key] = f"エラー: {e}"

        return self.answer_dict
