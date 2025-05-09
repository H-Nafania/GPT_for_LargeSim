import os
from dotenv import load_dotenv

load_dotenv()

def get_api_key(provider):
    """
    指定されたプロバイダのAPIキーを.envファイルから取得します。
    """
    api_key = os.getenv(provider.upper() + "_API_KEY")
    if not api_key:
        raise ValueError(f"{provider}のAPIキーが.envファイルに設定されていません。")
    return api_key

if __name__ == '__main__':
    # Example usage
    try:
        gemini_api_key = get_api_key("gemini")
        print(f"Gemini API Key: {gemini_api_key}")
    except ValueError as e:
        print(e)
