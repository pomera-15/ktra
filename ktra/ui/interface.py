"""
Enhanced user interface for ktra using rich and prompt_toolkit
"""

import os
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import WordCompleter, FuzzyCompleter
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout import Layout as PTLayout
import time
import threading

class KtraInterface:
    """Enhanced user interface for ktra"""
    
    def __init__(self):
        self.console = Console()
        self.history = InMemoryHistory()
        
        # Commands and examples for autocompletion
        self.task_examples = [
            "明日までに資料作成",
            "来週までにプレゼン準備", 
            "今日やることは？",
            "タスク一覧を見せて",
            "進捗状況を教えて",
            "完了したタスクを表示",
        ]
        
        self.shell_examples = [
            "ls",
            "pwd", 
            "git status",
            "git log",
            "システム情報を教えて",
            "現在のディレクトリは？",
        ]
        
        self.help_commands = [
            "/help", "/commands", "/examples", "/quit", "/clear", "/models", "/tools"
        ]
        
        all_suggestions = self.task_examples + self.shell_examples + self.help_commands
        self.completer = FuzzyCompleter(WordCompleter(all_suggestions, ignore_case=True))
    
    def show_welcome(self):
        """Welcome screen with enhanced styling"""
        self.console.clear()
        
        # ASCII Art for ktra (Beautiful box drawing style)
        ascii_art = """
[bright_blue]  ██╗  ██╗████████╗███████╗ █████╗ 
  ██║ ██╔╝╚══██╔══╝██╔══██╗██╔══██╗
  █████╔╝    ██║   ███████╔╝███████║
  ██╔═██╗    ██║   ██╔══██╗██╔══██║
  ██║  ██╗   ██║   ██║  ╚██╗██║  ██║
  ╚═╝  ╚═╝   ╚═╝   ╚═╝   ╚═╝╚═╝  ╚═╝[/bright_blue]
        """
        
        # Display ASCII art
        self.console.print(Align.center(ascii_art))
        
        # Main title and subtitle with Claude Code style
        self.console.print(Align.center("[bold magenta]🤖 ktra (カトレア)[/bold magenta]"))
        self.console.print(Align.center("[bright_black]Personal AI Agent powered by OpenAI[/bright_black]"))
        self.console.print()
        
        # Quick start info with Claude Code style
        self.console.print("[bold cyan]Quick Start[/bold cyan]")
        info_items = [
            ("💡 ヒント:", "自然言語でタスクの追加や管理ができます"),
            ("📋 例:", "'明日までに資料作成' → タスクが自動登録"),
            ("💻 コマンド:", "'ls' や 'git status' などの安全なコマンドも実行可能"),
            ("❓ ヘルプ:", "/help でコマンド一覧を表示"),
            ("🔄 終了:", "/quit または Ctrl+C で終了")
        ]
        
        for label, description in info_items:
            self.console.print(f"  [bright_black]⎿[/bright_black] [yellow]{label}[/yellow] [white]{description}[/white]")
        
        self.console.print()
    
    def show_help(self):
        """Display help information"""
        help_table = Table(title="🔧 利用可能なコマンド", show_header=True, header_style="bold magenta")
        help_table.add_column("コマンド", style="cyan", width=15)
        help_table.add_column("説明", style="white")
        help_table.add_column("例", style="dim", width=30)
        
        help_table.add_row("/help", "このヘルプを表示", "/help")
        help_table.add_row("/commands", "利用可能なシェルコマンド一覧", "/commands")
        help_table.add_row("/examples", "使用例を表示", "/examples")
        help_table.add_row("/clear", "画面をクリア", "/clear")
        help_table.add_row("/models", "モデル選択（数字キーで選択）", "/models")
        help_table.add_row("/tools", "利用可能なツール一覧を表示", "/tools")
        help_table.add_row("/quit", "アプリケーションを終了", "/quit")
        
        self.console.print(help_table)
        self.console.print()
        
        # Task management examples with Claude Code style
        self.console.print("[bold green]📝 タスク管理の例[/bold green]")
        examples = [
            ("明日までに資料作成", "新しいタスクを追加"),
            ("今日やることは？", "今日のタスク一覧を表示"),
            ("資料作成タスク完了", "指定したタスクを完了にする"),
            ("進捗状況を教えて", "全体の進捗を要約")
        ]
        
        for example, action in examples:
            self.console.print(f"  [bright_black]⎿[/bright_black] [yellow]{example}[/yellow] → [white]{action}[/white]")
        
        self.console.print()
    
    def show_commands(self):
        """Display available shell commands with Claude Code style"""
        self.console.print("[bold blue]💻 利用可能なシェルコマンド[/bold blue]")
        
        commands = [
            ("ls", "ファイル・ディレクトリ一覧"),
            ("pwd", "現在のディレクトリパス"),
            ("git status", "Gitの状態確認"),
            ("git log", "コミット履歴表示"),
            ("git diff", "変更差分表示"),
            ("date", "現在の日時"),
            ("whoami", "現在のユーザー名"),
            ("echo", "文字列の出力"),
        ]
        
        for cmd, desc in commands:
            self.console.print(f"  [bright_black]⎿[/bright_black] [cyan]{cmd}[/cyan] - [white]{desc}[/white]")
        
        self.console.print()
    
    def show_examples(self):
        """Display usage examples with Claude Code style"""
        self.console.print("[bold green]📚 使用例[/bold green]")
        self.console.print()
        
        # Task management examples
        self.console.print("[bold yellow]タスク管理:[/bold yellow]")
        task_examples = [
            "明日までに請求書送っておくこと",
            "今週中にプレゼン資料作成", 
            "今日やることは？",
            "完了したタスクを見せて",
            "請求書送付タスク完了"
        ]
        for example in task_examples:
            self.console.print(f"  [bright_black]⎿[/bright_black] [white]{example}[/white]")
        self.console.print()
        
        # Information examples
        self.console.print("[bold yellow]情報確認:[/bold yellow]")
        info_examples = [
            "システム情報を教えて",
            "現在のディレクトリは？",
            "git status",
            "ls"
        ]
        for example in info_examples:
            self.console.print(f"  [bright_black]⎿[/bright_black] [cyan]{example}[/cyan]")
        self.console.print()
        
        # Dialog examples
        self.console.print("[bold yellow]対話例:[/bold yellow]")
        dialog_examples = [
            "進捗状況を教えて",
            "優先度の高いタスクは？",
            "今週の予定を要約して"
        ]
        for example in dialog_examples:
            self.console.print(f"  [bright_black]⎿[/bright_black] [magenta]{example}[/magenta]")
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
        
        # Claude Code style model display
        self.console.print(f"[bold blue]⏺ Models[/bold blue]")
        self.console.print(f"  [green]⎿  Current: {current_model}[/green]")
        self.console.print()
        
        # Available models list
        self.console.print("[bold magenta]📋 利用可能なモデル（数字キーで選択）[/bold magenta]")
        for i, model in enumerate(models, 1):
            is_current = "[green]✓[/green]" if model == current_model else " "
            description = model_descriptions.get(model, "")
            current_mark = " [green](current)[/green]" if model == current_model else ""
            self.console.print(f"  {is_current} [cyan]{i}[/cyan]. [yellow]{model}[/yellow] - [bright_black]{description}[/bright_black]{current_mark}")
        
        self.console.print()
        self.console.print("[yellow]💡 使用方法: 数字を入力してEnter、またはqでキャンセル[/yellow]")
        
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
        """Display available tools interface with Claude Code style"""
        # Claude Code style tools display
        self.console.print("[bold blue]⏺ Tools[/bold blue]")
        self.console.print("  [green]⎿  7 tools available[/green]")
        self.console.print()
        
        tools_info = [
            {
                "name": "add_task",
                "description": "新しいタスクを追加",
                "example": "明日までに資料作成",
                "category": "タスク管理"
            },
            {
                "name": "list_tasks", 
                "description": "タスク一覧を表示",
                "example": "今日やることは？",
                "category": "タスク管理"
            },
            {
                "name": "update_task",
                "description": "タスクを更新・完了",
                "example": "資料作成タスク完了",
                "category": "タスク管理"
            },
            {
                "name": "execute_command",
                "description": "安全なシェルコマンドを実行",
                "example": "ls, pwd, git status",
                "category": "システム"
            },
            {
                "name": "get_system_info",
                "description": "システム情報を取得",
                "example": "システム情報を教えて",
                "category": "システム"
            },
            {
                "name": "change_model",
                "description": "使用するAIモデルを変更",
                "example": "モデルを gpt-4 に変更して",
                "category": "設定"
            },
            {
                "name": "get_current_model",
                "description": "現在のモデル設定を表示",
                "example": "現在のモデルは？",
                "category": "設定"
            }
        ]
        
        # Group by category
        categories = {}
        for tool in tools_info:
            cat = tool["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool)
        
        # Color mapping for categories
        category_colors = {
            "タスク管理": "green",
            "システム": "blue", 
            "設定": "magenta"
        }
        
        # Display by category with Claude Code style
        for category, tools in categories.items():
            color = category_colors.get(category, "white")
            self.console.print(f"[bold {color}]📂 {category}[/bold {color}]")
            for tool in tools:
                self.console.print(f"  [bright_black]⎿[/bright_black] [cyan]{tool['name']}[/cyan] - [bright_black]{tool['description']}[/bright_black]")
                self.console.print(f"      [yellow]例:[/yellow] [white]{tool['example']}[/white]")
            self.console.print()
        
        self.console.print("[yellow]💡 これらのツールは自然言語で呼び出すことができます[/yellow]")
        self.console.print()
    
    def get_input(self) -> str:
        """Get user input with enhanced prompt"""
        try:
            # Check if stdin is a terminal before using advanced features
            if os.isatty(0):
                # Terminal mode - use full features with enhanced colors
                prompt_text = HTML('<ansibrightgreen>❯</ansibrightgreen> ')
                user_input = prompt(
                    prompt_text,
                    history=self.history,
                    completer=self.completer,
                    complete_style='column',
                    mouse_support=True,
                ).strip()
            else:
                # Non-terminal mode - use simple input with enhanced colors
                self.console.print("[bright_green]❯[/bright_green] ", end="")
                user_input = input().strip()
            
            return user_input
            
        except (KeyboardInterrupt, EOFError):
            return "/quit"
    
    def show_thinking(self, message: str = "考え中..."):
        """Show thinking animation"""
        return Progress(
            SpinnerColumn(),
            TextColumn(f"[blue]{message}[/blue]"),
            console=self.console,
            transient=True
        )
    
    def show_detailed_thinking(self, steps: List[str]):
        """Show detailed thinking process with steps (without panel)"""
        self.console.print("[bold cyan]🧠 エージェントの思考過程[/bold cyan]")
        for step in steps:
            self.console.print(f"🔄 {step}")
        self.console.print()
    
    def show_agent_thinking(self, message: str = "考え中..."):
        """Show agent thinking with Claude Code style"""
        self.console.print(f"[bright_blue]✻ Thinking…[/bright_blue]")
        self.console.print()
    
    def show_thinking_detail(self, reasoning: str):
        """Show detailed thinking process with Claude Code style indentation"""
        # Split reasoning into paragraphs and wrap text
        paragraphs = reasoning.strip().split('\n\n')
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # Wrap text to fit nicely with indentation
                lines = paragraph.strip().split('\n')
                for line in lines:
                    if line.strip():
                        self.console.print(f"  [bright_black]{line.strip()}[/bright_black]")
                self.console.print()
    
    def show_tool_execution(self, tool_name: str, params: dict = None, file_info: str = None):
        """Show tool execution with Claude Code style"""
        if file_info:
            self.console.print(f"[bold green]⏺ {tool_name}([cyan]{file_info}[/cyan])[/bold green]")
        else:
            self.console.print(f"[bold green]⏺ {tool_name}[/bold green]")
        
        if params:
            # Show parameters in a nice format
            for key, value in params.items():
                if isinstance(value, str) and len(value) > 80:
                    value = value[:77] + "..."
                self.console.print(f"  [yellow]{key}:[/yellow] [white]{repr(value)}[/white]")
    
    def show_tool_result(self, result: str, success: bool = True, expand_hint: str = None):
        """Show tool execution result with Claude Code style"""
        if success:
            if expand_hint:
                self.console.print(f"  [bright_black]⎿  {expand_hint}[/bright_black]")
            else:
                # Truncate long results but show structure
                if len(result) > 120:
                    lines = result.split('\n')
                    if len(lines) > 3:
                        self.console.print(f"  [bright_black]⎿  {len(lines)} lines (ctrl+r to expand)[/bright_black]")
                    else:
                        display_result = result[:117] + "..."
                        self.console.print(f"  [bright_black]⎿  {display_result}[/bright_black]")
                else:
                    self.console.print(f"  [green]⎿  {result}[/green]")
        else:
            self.console.print(f"  [red]⎿  Error: {result}[/red]")
        
        self.console.print()
    
    def show_action_start(self, action: str):
        """Show action starting with Claude Code style"""
        self.console.print(f"[bold blue]⏺ {action}[/bold blue]")
        self.console.print()
    
    def show_agent_reasoning(self, reasoning: str):
        """Show agent's reasoning process with Claude Code style"""
        self.console.print(f"[bright_blue]✻ Thinking…[/bright_blue]")
        self.console.print()
        self.show_thinking_detail(reasoning)
        self.console.print()
    
    def show_agent_action(self, action: str, details: str = ""):
        """Show what action the agent is taking (without panel)"""
        self.console.print(f"[bold yellow]🎯 Agent Action:[/bold yellow]")
        self.console.print(f"🎯 {action}")
        if details:
            self.console.print(f"💡 {details}")
        self.console.print()
    
    def display_response(self, response: str, response_type: str = "assistant"):
        """Display assistant response with Claude Code style"""
        
        if response_type == "assistant":
            # Claude Code style response display
            self.console.print(f"[bold magenta]⏺ Response[/bold magenta]")
            
            # Split response into lines and display with proper indentation
            lines = response.strip().split('\n')
            if len(lines) == 1 and len(response) < 100:
                # Short response
                self.console.print(f"  [cyan]⎿  {response}[/cyan]")
            else:
                # Longer response with expand hint
                preview = lines[0][:80] + "..." if len(lines[0]) > 80 else lines[0]
                if len(lines) > 1:
                    self.console.print(f"  [bright_black]⎿  {len(lines)} lines - {preview}[/bright_black]")
                else:
                    self.console.print(f"  [bright_black]⎿  {preview}[/bright_black]")
                
                # Show full response with indentation and colors
                self.console.print()
                for line in lines:
                    if line.strip():
                        # Color code different types of content
                        if line.startswith('✅') or line.startswith('🎯'):
                            self.console.print(f"  [green]{line}[/green]")
                        elif line.startswith('❌') or line.startswith('⚠️'):
                            self.console.print(f"  [red]{line}[/red]")
                        elif line.startswith('📝') or line.startswith('📋'):
                            self.console.print(f"  [blue]{line}[/blue]")
                        elif line.startswith('💡') or line.startswith('ℹ️'):
                            self.console.print(f"  [yellow]{line}[/yellow]")
                        else:
                            self.console.print(f"  [white]{line}[/white]")
        
        elif response_type == "system":
            # System messages with Claude Code style
            self.console.print(f"[bright_black]⏺ System: {response}[/bright_black]")
        
        elif response_type == "error":
            # Error messages with Claude Code style
            self.console.print(f"[bold red]⏺ Error[/bold red]")
            self.console.print(f"  [red]⎿  {response}[/red]")
        
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
        
        return False
    
    def confirm_action(self, message: str) -> bool:
        """Ask for user confirmation"""
        return Confirm.ask(message)
    
    def show_status(self, status_info: Dict[str, Any]):
        """Display current status information"""
        status_table = Table(title="📊 Status", show_header=False, box=None)
        status_table.add_column(style="cyan", width=15)
        status_table.add_column(style="white")
        
        for key, value in status_info.items():
            status_table.add_row(f"{key}:", str(value))
        
        status_panel = Panel(
            status_table,
            title="Current Status",
            border_style="dim",
            padding=(0, 1)
        )
        
        self.console.print(status_panel)
        self.console.print()