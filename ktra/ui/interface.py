"""
Simple user interface for ktra
"""

import os
from typing import Optional, Dict, Any
from rich.console import Console
from rich.prompt import Confirm
from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion


class SimpleContextManager:
    """Simple context manager for thinking display"""
    
    def __init__(self, console, message: str):
        self.console = console
        self.message = message
    
    def __enter__(self):
        self.console.print(f"[dim]{self.message}[/dim]")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # シンプルなので終了時は何もしない
        pass

class CommandCompleter(Completer):
    """カスタムコマンド補完クラス"""
    
    def __init__(self, commands):
        self.commands = commands
    
    def get_completions(self, document, complete_event):
        # 現在の入力を取得
        text = document.text_before_cursor
        
        # /で始まる場合のみ補完
        if text.startswith('/'):
            # 入力されたテキストで始まるコマンドを検索
            for command in self.commands:
                if command.startswith(text):
                    # 現在の入力の長さから補完部分を計算
                    yield Completion(command, start_position=-len(text))


class KtraInterface:
    """Simple user interface for ktra"""
    
    def __init__(self):
        self.console = Console()
        self.pending_ai_request = None
        
        # コマンド補完の設定
        self.commands = [
            "/help", "/quit", "/exit", "/clear", "/tasks", "/projects", 
            "/models", "/tools", "/commands", "/examples"
        ]
        self.completer = CommandCompleter(self.commands)
    
    def show_welcome(self):
        """Welcome screen with ASCII art"""
        self.console.clear()
        
        # KTRA AGENT 3D ASCII Art
        ascii_art = """
    ██╗  ██╗████████╗██████╗  █████╗     ██╗     ██╗
   ██╔╝ ██╔╝╚══██╔══╝██╔══██╗██╔══██╗   ██╔╝    ██╔╝
  ██╔╝ ██╔╝    ██║   ██████╔╝███████║  ██╔╝    ██╔╝
 ██╔╝ ██╔╝     ██║   ██╔══██╗██╔══██║ ██╔╝    ██╔╝
██╔╝ ██╔╝      ██║   ██║  ██║██║  ██║██╔╝    ██╔╝
╚═╝ ╚═╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝

 █████╗  ██████╗ ███████╗███╗   ██╗████████╗██╗     ██╗
██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝╚██╗   ██╔╝
███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║    ╚██╗ ██╔╝
██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║     ╚████╔╝
██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║      ╚██╔╝
╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝       ╚═╝
        """
        
        self.console.print("[bold cyan]" + ascii_art + "[/bold cyan]")
        self.console.print("[bold blue]Personal AI Agent - あなたの生産性をサポート[/bold blue]")
        self.console.print()
        
        # Essential info only
        self.console.print("[dim]タスク追加:[/dim] '明日までに資料作成'")
        self.console.print("[dim]コマンド:[/dim] /tasks, /projects, /help, /models")
        self.console.print("[dim]Web検索:[/dim] 'Pythonについて調べて'")
        self.console.print()
    
    def show_help(self):
        """Display simple help information"""
        self.console.print("[bold]コマンド:[/bold]")
        self.console.print("  /tasks     - タスク管理")
        self.console.print("  /projects  - プロジェクト管理")
        self.console.print("  /clear     - 画面クリア")
        self.console.print("  /quit      - 終了")
        self.console.print()
        
        self.console.print("[bold]使い方:[/bold]")
        self.console.print("  タスク作成: '明日までに資料作成'")
        self.console.print("  シェル実行: 'git status'")
        self.console.print()
    
    def show_commands(self):
        """Display simple shell commands"""
        self.console.print("[bold]シェルコマンド:[/bold]")
        self.console.print("  ls, pwd, git status, git log, date")
        self.console.print()
    
    def show_examples(self):
        """Display simple examples"""
        self.console.print("[bold]使用例:[/bold]")
        self.console.print("  '明日までに資料作成'")
        self.console.print("  '今日やることは？'")
        self.console.print("  'git status'")
        self.console.print()
    
    def show_models(self):
        """Display model selection interface in conversation flow"""
        from ..tools.model import get_available_models, get_default_model, set_default_model
        
        models = get_available_models()
        current_model = get_default_model()
        
        model_descriptions = {
            "gpt-3.5-turbo": "高速で効率的、日常的なタスクに最適",
            "gpt-4": "高精度、複雑なタスクに適している",
            "gpt-4-turbo": "GPT-4の高速版、バランスの取れた性能",
            "gpt-4o": "最新のGPT-4モデル、最高の性能",
            "gpt-4o-mini": "GPT-4oの軽量版、高速で効率的"
        }
        
        # Simple model display
        self.console.print(f"[bold]現在のモデル:[/bold] {current_model}")
        self.console.print()
        
        # Available models list
        self.console.print("[bold]利用可能なモデル:[/bold]")
        for i, model in enumerate(models, 1):
            is_current = "✓" if model == current_model else " "
            self.console.print(f"  {is_current} {i}. {model}")
        
        self.console.print()
        self.console.print("数字を入力してEnter、qでキャンセル")
        
        # Get user selection
        try:
            if os.isatty(0):
                # Terminal mode - use prompt
                selection = prompt("モデル選択 (1-{}) または q でキャンセル: ".format(len(models)))
            else:
                # Non-terminal mode - use input
                self.console.print("モデル選択 (1-{}) または q でキャンセル: ".format(len(models)), end="")
                selection = input()
            
            selection = selection.strip().lower()
            
            # Handle cancellation
            if selection in ['q', 'quit', 'cancel', '']:
                self.console.print("[yellow]⬅️ モデル変更をキャンセルしました[/yellow]")
                self.console.print()
                return
            
            # Handle numeric selection
            try:
                choice_num = int(selection)
                if 1 <= choice_num <= len(models):
                    selected_model = models[choice_num - 1]
                    
                    # Check if same model
                    if selected_model == current_model:
                        self.console.print(f"[green]✅ {selected_model} が既に選択されています[/green]")
                        self.console.print()
                        return
                    
                    # Show selection
                    self.console.print(f"[blue]選択されたモデル:[/blue] [white]{selected_model}[/white]")
                    
                    # Confirm change
                    if os.isatty(0):
                        confirm_text = f"モデルを {current_model} から {selected_model} に変更しますか？ (y/n): "
                        confirmation = prompt(confirm_text)
                    else:
                        self.console.print(f"モデルを {current_model} から {selected_model} に変更しますか？ (y/n): ", end="")
                        confirmation = input()
                    
                    if confirmation.strip().lower() not in ['y', 'yes', 'はい']:
                        self.console.print("[yellow]⬅️ モデル変更をキャンセルしました[/yellow]")
                        self.console.print()
                        return
                    
                    # Apply change
                    if set_default_model(selected_model):
                        self.console.print(f"[bold green]✅ モデル変更完了[/bold green]")
                        self.console.print(f"[dim]変更前:[/dim] {current_model}")
                        self.console.print(f"[dim]変更後:[/dim] [green]{selected_model}[/green]")
                        self.console.print()
                        self.console.print("[yellow]💡 新しいモデルは次回起動時から使用されます[/yellow]")
                    else:
                        self.console.print("[red]❌ モデルの変更に失敗しました[/red]")
                else:
                    self.console.print(f"[red]❌ 無効な選択です。1-{len(models)} の数字を入力してください[/red]")
            
            except ValueError:
                self.console.print("[red]❌ 無効な入力です。数字を入力してください[/red]")
        
        except (KeyboardInterrupt, EOFError):
            self.console.print("[yellow]⬅️ モデル変更をキャンセルしました[/yellow]")
        
        self.console.print()
    
    def show_tools(self):
        """Display simple tools list"""
        self.console.print("[bold]利用可能な機能:[/bold]")
        self.console.print("  タスク管理 - 追加、一覧、更新")
        self.console.print("  プロジェクト管理 - 作成、管理")
        self.console.print("  シェル実行 - 安全なコマンド実行")
        self.console.print("  知識管理 - メモの保存・検索")
        self.console.print()
    
    def get_input(self) -> str:
        """Get user input with enhanced prompt"""
        # pending_ai_requestがある場合はそれを返す
        if self.pending_ai_request:
            request = self.pending_ai_request
            self.pending_ai_request = None
            return request
        
        try:
            # Simple prompt with command completion
            if os.isatty(0):
                # Terminal mode - prompt with completion
                user_input = prompt("❯ ", completer=self.completer).strip()
            else:
                # Non-terminal mode - simple input
                self.console.print("❯ ", end="")
                user_input = input().strip()
            
            return user_input
            
        except (KeyboardInterrupt, EOFError):
            return "/quit"
    
    def show_thinking(self, message: str = "考え中..."):
        """Show simple thinking indicator with context manager support"""
        return SimpleContextManager(self.console, message)
    
    def show_detailed_thinking(self, steps):
        """Skip detailed thinking"""
        pass
    
    def show_agent_thinking(self, message: str = "考え中..."):
        """Show simple thinking indicator"""
        self.console.print(f"[dim]{message}[/dim]")
    
    def show_thinking_detail(self, reasoning: str):
        """Skip thinking detail"""
        pass
    
    def show_tool_execution(self, tool_name: str, params: dict = None, file_info: str = None):
        """Skip tool execution display"""
        pass
    
    def show_tool_result(self, result: str, success: bool = True, expand_hint: str = None):
        """Skip tool result display"""
        pass
    
    def show_action_start(self, action: str):
        """Skip action display"""
        pass
    
    def show_agent_reasoning(self, reasoning: str):
        """Skip reasoning display"""
        pass
    
    def show_agent_action(self, action: str, details: str = ""):
        """Skip action display"""
        pass
    
    def display_response(self, response: str, response_type: str = "assistant"):
        """Display simple response"""
        
        if response_type == "assistant":
            # Simple response display
            self.console.print(response)
        
        elif response_type == "system":
            # System messages
            self.console.print(f"[dim]{response}[/dim]")
        
        elif response_type == "error":
            # Error messages
            self.console.print(f"[red]Error: {response}[/red]")
        
        self.console.print()
    
    def handle_special_commands(self, user_input: str) -> bool:
        """Handle special UI commands. Returns True if handled."""
        
        if user_input.lower() in ["/quit", "/exit", "quit", "exit"]:
            self.console.print("[yellow]👋 ktraを終了します。お疲れ様でした！[/yellow]")
            return True
        
        elif user_input.lower() == "/help":
            self.show_help()
            return True
        
        elif user_input.lower() == "/commands":
            self.show_commands()
            return True
        
        elif user_input.lower() == "/examples":
            self.show_examples()
            return True
        
        elif user_input.lower() == "/clear":
            self.console.clear()
            self.show_welcome()
            return True
        
        elif user_input.lower() == "/models":
            self.show_models()
            return True
        
        elif user_input.lower() == "/tools":
            self.show_tools()
            return True
        
        elif user_input.lower() == "/tasks":
            result = self.enter_task_mode()
            if result and result.startswith("ai_request:"):
                # AI支援リクエストを処理するため、メインループに返す
                ai_request = result[11:]  # "ai_request:" を除去
                self.pending_ai_request = ai_request
                return False  # メインループでAI処理を続行
            return True
        
        elif user_input.lower() == "/projects":
            self.enter_project_mode()
            return True
        
        return False
    
    def enter_task_mode(self) -> Optional[str]:
        """Enter interactive task selector"""
        try:
            from ..ui.task_selector import TaskSelector
            
            selector = TaskSelector()
            result = selector.run()
            
            return result
            
        except ImportError as e:
            self.console.print(f"[red]❌ タスクセレクターの読み込みに失敗しました: {str(e)}[/red]")
            return None
        except Exception as e:
            self.console.print(f"[red]❌ タスクセレクターでエラーが発生しました: {str(e)}[/red]")
            return None
    
    def enter_project_mode(self) -> None:
        """Enter interactive project selector"""
        try:
            from ..ui.project_selector import ProjectSelector
            
            selector = ProjectSelector()
            selector.run()
            
        except ImportError as e:
            self.console.print(f"[red]❌ プロジェクトセレクターの読み込みに失敗しました: {str(e)}[/red]")
        except Exception as e:
            self.console.print(f"[red]❌ プロジェクトセレクターでエラーが発生しました: {str(e)}[/red]")
    
    def confirm_action(self, message: str) -> bool:
        """Ask for user confirmation"""
        return Confirm.ask(message)
    
    def show_status(self, status_info: Dict[str, Any]):
        """Display simple status information"""
        self.console.print("[bold]状態:[/bold]")
        for key, value in status_info.items():
            self.console.print(f"  {key}: {value}")
        self.console.print()