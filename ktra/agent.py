import os
from agents import Agent, Runner
from dotenv import load_dotenv

from .tools.task import add_task, list_tasks, update_task
from .tools.shell import execute_command, get_system_info
from .tools.model import change_model, get_current_model, get_available_models, get_default_model, set_default_model

load_dotenv()

def create_ktra_agent(model: str = None) -> Agent:
    """
    ktraエージェントを作成します。
    
    Args:
        model: 使用するモデル名（デフォルト: gpt-3.5-turbo）
    """
    
    # システムプロンプトを読み込み
    system_prompt = _load_system_prompt()
    
    # モデルの設定
    if model is None:
        model = get_default_model()
    
    # エージェントを作成
    agent = Agent(
        name="ktra",
        instructions=system_prompt,
        tools=[add_task, list_tasks, update_task, execute_command, get_system_info, change_model, get_current_model],
        model=model
    )
    
    return agent


def _load_system_prompt() -> str:
    """システムプロンプトをファイルから読み込みます。"""
    try:
        import pkg_resources
        prompt_path = pkg_resources.resource_filename('ktra', 'prompts/system.txt')
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except (FileNotFoundError, ModuleNotFoundError):
        # パッケージリソースが見つからない場合の相対パス
        try:
            import os
            current_dir = os.path.dirname(__file__)
            prompt_path = os.path.join(current_dir, "prompts", "system.txt")
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "あなたはユーザーのパーソナルアシスタント「ktra（カトレア）」です。日常のタスク管理、支援、実行補助を担当します。"