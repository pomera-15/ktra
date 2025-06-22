import os
from agents import Agent, Runner
from dotenv import load_dotenv

from .tools.task import add_task, list_tasks, update_task, search_tasks, recommend_next_task
from .tools.shell import execute_command, get_system_info
from .tools.model import change_model, get_current_model, get_available_models, get_default_model, set_default_model
from .tools.knowledge import save_knowledge, search_knowledge, get_knowledge_stats, link_knowledge_to_task
from .tools.analytics import analyze_productivity, find_task_patterns, predict_task_completion, generate_daily_summary
from .tools.context import update_work_context, get_current_context, start_focus_session, update_preferences, get_work_environment_suggestion
from .tools.project import create_project, list_projects, get_project_details, update_project_status, add_task_to_project, read_project_file, create_project_note, search_project_files

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
    
    # エージェントを作成（強化されたツールセット）
    agent = Agent(
        name="ktra",
        instructions=system_prompt,
        tools=[
            # 基本タスク管理
            add_task, list_tasks, update_task, search_tasks, recommend_next_task,
            # システム関連
            execute_command, get_system_info,
            # モデル管理
            change_model, get_current_model,
            # 知識管理
            save_knowledge, search_knowledge, get_knowledge_stats, link_knowledge_to_task,
            # 分析機能
            analyze_productivity, find_task_patterns, predict_task_completion, generate_daily_summary,
            # コンテキスト管理
            update_work_context, get_current_context, start_focus_session, update_preferences, get_work_environment_suggestion,
            # プロジェクト管理
            create_project, list_projects, get_project_details, update_project_status, add_task_to_project, read_project_file, create_project_note, search_project_files
        ],
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