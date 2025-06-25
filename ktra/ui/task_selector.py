"""
インタラクティブタスクセレクター
矢印キーでタスクを選択し、操作を実行
"""

from typing import List, Optional, Dict, Any, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, Window, VSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout import Layout
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import message_dialog, input_dialog
import asyncio

# Pydanticモデルをインポート
try:
    from ..models import Task, TaskStatus, TaskPriority, EnergyLevel
    from ..tools.task import TaskManager
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

console = Console()


class TaskSelector:
    """インタラクティブタスクセレクター"""
    
    def __init__(self):
        self.console = console
        self.selected_index = 0
        self.tasks = []
        self.filtered_tasks = []
        self.filter_mode = "all"  # all, active, completed, etc.
        self.running = True
        
    def run(self) -> Optional[str]:
        """セレクターを実行し、選択されたアクションを返す"""
        if not PYDANTIC_AVAILABLE:
            self.console.print("[red]この機能にはPydanticモデルが必要です[/red]")
            return None
        
        try:
            self._load_tasks()
            if not self.tasks:
                self.console.print("タスクがありません")
                if Confirm.ask("新しいタスクを作成しますか？"):
                    return "create_task"
                return None
            
            return self._run_selector()
            
        except Exception as e:
            self.console.print(f"[red]エラー: {str(e)}[/red]")
            return None
    
    def _load_tasks(self) -> None:
        """タスクを読み込み"""
        manager = TaskManager()
        self.tasks = manager.load_tasks_as_models()
        self._apply_filter()
    
    def _apply_filter(self) -> None:
        """フィルターを適用"""
        if self.filter_mode == "all":
            self.filtered_tasks = self.tasks
        elif self.filter_mode == "active":
            self.filtered_tasks = [t for t in self.tasks if t.status not in [TaskStatus.DONE, TaskStatus.ARCHIVED]]
        elif self.filter_mode == "completed":
            self.filtered_tasks = [t for t in self.tasks if t.status == TaskStatus.DONE]
        elif self.filter_mode == "in_progress":
            self.filtered_tasks = [t for t in self.tasks if t.status == TaskStatus.IN_PROGRESS]
        elif self.filter_mode == "blocked":
            self.filtered_tasks = [t for t in self.tasks if t.status == TaskStatus.BLOCKED]
        else:
            self.filtered_tasks = self.tasks
        
        # インデックスをリセット
        self.selected_index = min(self.selected_index, len(self.filtered_tasks) - 1) if self.filtered_tasks else 0
    
    def _run_selector(self) -> Optional[str]:
        """セレクターのメインループ"""
        kb = KeyBindings()
        
        @kb.add('up')
        def _(event):
            if self.filtered_tasks:
                self.selected_index = max(0, self.selected_index - 1)
        
        @kb.add('down')
        def _(event):
            if self.filtered_tasks:
                self.selected_index = min(len(self.filtered_tasks) - 1, self.selected_index + 1)
        
        @kb.add('enter')
        def _(event):
            if self.filtered_tasks:
                event.app.exit(result="select_task")
        
        @kb.add('c-c')
        def _(event):
            event.app.exit(result="cancel")
        
        @kb.add('q')
        def _(event):
            event.app.exit(result="cancel")
        
        @kb.add('n')
        def _(event):
            event.app.exit(result="create_task_direct")
        
        @kb.add('f')
        def _(event):
            event.app.exit(result="filter")
        
        @kb.add('h')
        def _(event):
            event.app.exit(result="help")
        
        @kb.add('r')
        def _(event):
            self._load_tasks()
        
        # レイアウトの構築
        def get_title_text():
            filter_text = f" ({self.filter_mode})" if self.filter_mode != "all" else ""
            return HTML(f'タスク一覧{filter_text}')
        
        def get_tasks_text():
            if not self.filtered_tasks:
                return HTML('タスクがありません')
            
            lines = []
            for i, task in enumerate(self.filtered_tasks):
                # 選択状態の表示
                if i == self.selected_index:
                    # 選択中のタスク（シンプル）
                    title = task.title[:60] + "..." if len(task.title) > 60 else task.title
                    lines.append(f'<b>→ {title}</b>')
                else:
                    # 通常のタスク（シンプル）
                    title = task.title[:60] + "..." if len(task.title) > 60 else task.title
                    lines.append(f'  {title}')
            
            return HTML('\n'.join(lines))
        
        def get_help_text():
            return HTML('↑↓ 選択  Enter 操作  n 新規  f フィルター  q 終了')
        
        # ウィンドウの作成
        title_window = Window(
            content=FormattedTextControl(get_title_text),
            height=1,
            dont_extend_width=True
        )
        
        tasks_window = Window(
            content=FormattedTextControl(get_tasks_text),
            wrap_lines=True
        )
        
        help_window = Window(
            content=FormattedTextControl(get_help_text),
            height=3,
            dont_extend_width=True
        )
        
        # レイアウト
        layout = Layout(
            HSplit([
                title_window,
                tasks_window,
                help_window,
            ])
        )
        
        # アプリケーション
        app = Application(
            layout=layout,
            key_bindings=kb,
            full_screen=False,
            mouse_support=False,
        )
        
        # 実行
        while True:
            try:
                result = app.run()
                
                if result == "cancel":
                    return None
                elif result == "select_task":
                    return self._handle_task_selection()
                elif result == "create_task_direct":
                    self._handle_direct_task_creation()
                    continue
                elif result == "filter":
                    self._handle_filter_selection()
                    continue
                elif result == "help":
                    self._show_help()
                    continue
                else:
                    return None
                    
            except KeyboardInterrupt:
                return None
    
    def _handle_task_selection(self) -> Optional[str]:
        """選択されたタスクの操作メニューを表示"""
        if not self.filtered_tasks or self.selected_index >= len(self.filtered_tasks):
            return None
        
        selected_task = self.filtered_tasks[self.selected_index]
        
        # タスク詳細を表示
        self._display_task_details(selected_task)
        
        # 操作メニュー（矢印キー選択）
        actions = [
            ("ステータス変更", "update_status"),
            ("詳細を編集", "edit_task"),
            ("AIに相談", "ai_assist"),
            ("削除", "delete_task"),
            ("キャンセル", "cancel")
        ]
        
        selected_action = self._show_action_selector(actions, selected_task.title)
        
        if selected_action == "cancel":
            return None
        elif selected_action == "update_status":
            return self._handle_status_update(selected_task)
        elif selected_action == "edit_task":
            return self._handle_task_edit(selected_task)
        elif selected_action == "ai_assist":
            return self._handle_ai_assist(selected_task)
        elif selected_action == "delete_task":
            return self._handle_task_delete(selected_task)
        
        return None
    
    def _handle_status_update(self, task: Task) -> Optional[str]:
        """ステータス更新"""
        self.console.print(f"\n[blue]📝 ステータス変更: {task.title}[/blue]")
        
        statuses = [
            ("1", "📥 受信箱", TaskStatus.INBOX),
            ("2", "⏭️ 次のアクション", TaskStatus.NEXT),
            ("3", "🔄 実行中", TaskStatus.IN_PROGRESS),
            ("4", "🚫 ブロック中", TaskStatus.BLOCKED),
            ("5", "✅ 完了", TaskStatus.DONE),
            ("6", "📦 アーカイブ", TaskStatus.ARCHIVED)
        ]
        
        self.console.print("新しいステータス:")
        for num, name, _ in statuses:
            self.console.print(f"  {num}. {name}")
        
        choice = Prompt.ask("選択（1-6）", choices=["1", "2", "3", "4", "5", "6"])
        new_status = statuses[int(choice) - 1][2]
        
        # ステータス更新
        try:
            manager = TaskManager()
            tasks = manager.load_tasks_as_models()
            
            for i, t in enumerate(tasks):
                if t.id == task.id:
                    tasks[i].status = new_status
                    tasks[i].updated_at = task.updated_at.replace()
                    
                    if new_status == TaskStatus.DONE and not tasks[i].completed_at:
                        from datetime import datetime
                        tasks[i].completed_at = datetime.now()
                        
                        # 実際時間の入力
                        actual_time = Prompt.ask("実際にかかった時間（分）", default=str(task.estimated_minutes))
                        try:
                            tasks[i].actual_minutes = int(actual_time)
                        except ValueError:
                            pass
                    
                    break
            
            manager.save_tasks_from_models(tasks)
            
            self.console.print(f"[green]✅ ステータスを更新しました: {statuses[int(choice) - 1][1]}[/green]")
            
            # タスクリストを再読み込み
            self._load_tasks()
            
        except Exception as e:
            self.console.print(f"[red]❌ 更新に失敗しました: {str(e)}[/red]")
        
        return None
    
    def _handle_task_edit(self, task: Task) -> Optional[str]:
        """タスク編集"""
        self.console.print(f"\n[blue]📝 タスク編集: {task.title}[/blue]")
        
        # AIエージェントに編集を依頼
        edit_request = f"タスク「{task.title}」を編集したいです。現在の内容: 説明={task.description}, 優先度={task.priority.value}, エネルギー={task.energy_required.value}, 推定時間={task.estimated_minutes}分, プロジェクト={task.project}, タグ={task.tags}"
        
        return f"ai_request:{edit_request}"
    
    def _handle_ai_assist(self, task: Task) -> Optional[str]:
        """AI支援要請"""
        self.console.print(f"\n[blue]🤖 AIに相談: {task.title}[/blue]")
        
        assist_options = [
            ("1", "このタスクの進め方を相談", "approach"),
            ("2", "必要なリソースを教えて", "resources"),
            ("3", "時間見積もりの妥当性をチェック", "estimation"),
            ("4", "類似タスクとの比較", "comparison"),
            ("5", "カスタム質問", "custom")
        ]
        
        self.console.print("相談内容:")
        for num, desc, _ in assist_options:
            self.console.print(f"  {num}. {desc}")
        
        choice = Prompt.ask("選択（1-5）", choices=["1", "2", "3", "4", "5"])
        
        assist_requests = {
            "1": f"タスク「{task.title}」の進め方を相談したいです。説明: {task.description}。どのようにアプローチすべきでしょうか？",
            "2": f"タスク「{task.title}」（説明: {task.description}）を実行するのに必要なリソースやツールを教えてください。",
            "3": f"タスク「{task.title}」の推定時間{task.estimated_minutes}分は適切でしょうか？過去のデータと比較して分析してください。",
            "4": f"タスク「{task.title}」と類似するタスクがあれば比較して、効率化のヒントを教えてください。",
            "5": ""
        }
        
        if choice == "5":
            custom_question = Prompt.ask("質問内容を入力してください")
            ai_request = f"タスク「{task.title}」について質問です: {custom_question}"
        else:
            ai_request = assist_requests[choice]
        
        return f"ai_request:{ai_request}"
    
    def _handle_task_delete(self, task: Task) -> Optional[str]:
        """タスク削除"""
        self.console.print(f"\n[red]🗑️ タスク削除: {task.title}[/red]")
        
        if not Confirm.ask("このタスクを削除しますか？"):
            self.console.print("[blue]削除をキャンセルしました[/blue]")
            return None
        
        try:
            manager = TaskManager()
            tasks = manager.load_tasks_as_models()
            
            # タスクを削除
            tasks = [t for t in tasks if t.id != task.id]
            manager.save_tasks_from_models(tasks)
            
            self.console.print(f"[green]✅ タスクを削除しました: {task.title}[/green]")
            
            # タスクリストを再読み込み
            self._load_tasks()
            
        except Exception as e:
            self.console.print(f"[red]❌ 削除に失敗しました: {str(e)}[/red]")
        
        return None
    
    def _handle_direct_task_creation(self) -> None:
        """直接タスク作成（AI相談なし）"""
        self.console.print("\n新しいタスクを作成")
        
        # タスクタイトルの入力
        title = Prompt.ask("タスクのタイトル")
        if not title.strip():
            self.console.print("[yellow]タスクの作成をキャンセルしました[/yellow]")
            return
        
        # 基本情報の入力（オプション）
        description = Prompt.ask("説明（Enter でスキップ）", default="")
        
        # プロジェクトの選択（オプション）
        project = self._select_project_for_task()
        
        # 推定時間の入力（オプション）
        estimated_minutes_str = Prompt.ask("推定時間（分、Enter でスキップ）", default="30")
        try:
            estimated_minutes = int(estimated_minutes_str) if estimated_minutes_str else 30
        except ValueError:
            estimated_minutes = 30
        
        # 新しいタスクを作成
        try:
            from datetime import datetime
            
            new_task = Task(
                title=title.strip(),
                description=description.strip() if description else None,
                project=project.strip() if project else None,
                estimated_minutes=estimated_minutes,
                status=TaskStatus.INBOX,
                priority=TaskPriority.NOT_URGENT_IMPORTANT,
                energy_required=EnergyLevel.MEDIUM,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # タスクを保存
            manager = TaskManager()
            tasks = manager.load_tasks_as_models()
            tasks.append(new_task)
            manager.save_tasks_from_models(tasks)
            
            self.console.print(f"[green]✅ タスクを作成しました: {title}[/green]")
            
            # タスクリストを再読み込み
            self._load_tasks()
            
        except Exception as e:
            self.console.print(f"[red]❌ タスクの作成に失敗しました: {str(e)}[/red]")
    
    def _handle_filter_selection(self) -> None:
        """フィルター選択"""
        self.console.print("\nフィルター選択:")
        
        filters = [
            ("1", "すべて", "all"),
            ("2", "アクティブ", "active"),
            ("3", "完了済み", "completed"),
            ("4", "実行中", "in_progress"),
            ("5", "ブロック中", "blocked")
        ]
        
        for num, name, _ in filters:
            current = " (現在)" if self.filter_mode == filters[int(num)-1][2] else ""
            self.console.print(f"  {num}. {name}{current}")
        
        choice = Prompt.ask("選択（1-5）", choices=["1", "2", "3", "4", "5"], default="1")
        self.filter_mode = filters[int(choice) - 1][2]
        self._apply_filter()
    
    def _show_help(self) -> None:
        """ヘルプ表示"""
        help_text = """
[bold cyan]📝 タスクセレクター ヘルプ[/bold cyan]

[bold]キーボード操作:[/bold]
• ↑/↓  - タスク選択
• Enter - 操作メニューを開く
• n     - 新しいタスクを作成（直接入力）
• f     - フィルター変更
• r     - タスクリストを更新
• h     - このヘルプを表示
• q     - 終了

[bold]操作メニュー:[/bold]
• ステータス変更 - タスクの状態を変更
• 詳細を編集    - AIエージェントによる編集支援
• AIに相談      - タスクに関するAI支援
• 削除         - タスクの削除

[bold]フィルター:[/bold]
• すべて   - 全タスクを表示
• アクティブ - 未完了タスクのみ
• 完了済み - 完了したタスクのみ
• 実行中   - 現在作業中のタスクのみ
• ブロック中 - ブロックされたタスクのみ
"""
        
        panel = Panel(help_text.strip(), title="ヘルプ", border_style="cyan")
        self.console.print(panel)
        
        Prompt.ask("Enterキーで戻る", default="")
    
    def _display_task_details(self, task: Task) -> None:
        """タスクの詳細を表示"""
        status_display = self._get_status_display_name(task.status.value)
        priority_display = self._get_priority_display_name(task.priority.value)
        energy_display = self._get_energy_display_name(task.energy_required.value)
        
        content = f"""
[bold]{task.title}[/bold]

{self._get_status_icon(task.status)} {self._get_priority_icon(task.priority)} {self._get_energy_icon(task.energy_required)}

📄 説明: {task.description or '（なし）'}
⏱️  推定時間: {task.estimated_minutes}分
"""
        
        if task.actual_minutes:
            content += f"⏲️  実際時間: {task.actual_minutes}分\n"
        
        if task.due_date:
            content += f"📅 期限: {task.due_date.strftime('%Y-%m-%d %H:%M')}\n"
        
        if task.project:
            content += f"📁 プロジェクト: {task.project}\n"
        
        if task.tags:
            content += f"🏷️  タグ: {', '.join(task.tags)}\n"
        
        content += f"\n🆔 ID: {task.id[:8]}...\n"
        content += f"📅 作成: {task.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        panel = Panel(content.strip(), title="📝 タスク詳細", border_style="blue")
        self.console.print(panel)
    
    def _get_status_icon(self, status: TaskStatus) -> str:
        """ステータスアイコンを取得"""
        icons = {
            TaskStatus.INBOX: "📥",
            TaskStatus.NEXT: "⏭️",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.BLOCKED: "🚫",
            TaskStatus.DONE: "✅",
            TaskStatus.ARCHIVED: "📦"
        }
        return icons.get(status, "❓")
    
    def _get_priority_icon(self, priority: TaskPriority) -> str:
        """優先度アイコンを取得"""
        icons = {
            TaskPriority.URGENT_IMPORTANT: "🔴",
            TaskPriority.NOT_URGENT_IMPORTANT: "🟡",
            TaskPriority.URGENT_NOT_IMPORTANT: "🟠",
            TaskPriority.NOT_URGENT_NOT_IMPORTANT: "🟢"
        }
        return icons.get(priority, "❓")
    
    def _get_energy_icon(self, energy: EnergyLevel) -> str:
        """エネルギーレベルアイコンを取得"""
        icons = {
            EnergyLevel.HIGH: "⚡",
            EnergyLevel.MEDIUM: "🔋",
            EnergyLevel.LOW: "🪫"
        }
        return icons.get(energy, "❓")
    
    def _get_status_display_name(self, status: str) -> str:
        """ステータス表示名を取得"""
        names = {
            "inbox": "📥 受信箱",
            "next": "⏭️ 次のアクション",
            "in_progress": "🔄 実行中",
            "blocked": "🚫 ブロック中",
            "done": "✅ 完了",
            "archived": "📦 アーカイブ"
        }
        return names.get(status, status)
    
    def _get_priority_display_name(self, priority: str) -> str:
        """優先度表示名を取得"""
        names = {
            "urgent_important": "🔴 緊急・重要",
            "not_urgent_important": "🟡 重要・非緊急",
            "urgent_not_important": "🟠 緊急・非重要",
            "not_urgent_not_important": "🟢 非緊急・非重要"
        }
        return names.get(priority, priority)
    
    def _get_energy_display_name(self, energy: str) -> str:
        """エネルギーレベル表示名を取得"""
        names = {
            "high": "⚡ 高エネルギー",
            "medium": "🔋 中エネルギー",
            "low": "🪫 低エネルギー"
        }
        return names.get(energy, energy)
    
    def _select_project_for_task(self) -> Optional[str]:
        """タスク作成時にプロジェクトを選択"""
        try:
            from ..tools.project import ProjectManager
            
            manager = ProjectManager()
            projects = manager.load_projects_as_models()
            
            if not projects:
                # プロジェクトがない場合は直接入力
                project = Prompt.ask("プロジェクト（Enter でスキップ）", default="")
                return project.strip() if project else None
            
            # プロジェクト選択メニュー
            self.console.print("\n[cyan]📁 プロジェクトを選択（番号入力 または Enter でスキップ）:[/cyan]")
            self.console.print("  0. プロジェクトなし")
            
            active_projects = [p for p in projects if p.status.value in ["planning", "active"]]
            for i, project in enumerate(active_projects, 1):
                status_emoji = "🚀" if project.status.value == "active" else "📋"
                self.console.print(f"  {i}. {status_emoji} {project.name}")
            
            self.console.print(f"  {len(active_projects)+1}. ➕ 新しいプロジェクトを作成")
            
            choice = Prompt.ask(
                f"選択（0-{len(active_projects)+1}）", 
                default="0"
            )
            
            try:
                choice_num = int(choice)
                
                if choice_num == 0:
                    return None
                elif 1 <= choice_num <= len(active_projects):
                    selected_project = active_projects[choice_num - 1]
                    return selected_project.name
                elif choice_num == len(active_projects) + 1:
                    # 新しいプロジェクトを作成
                    return self._create_new_project_for_task()
                else:
                    self.console.print("[yellow]無効な選択です。プロジェクトなしに設定します。[/yellow]")
                    return None
                    
            except ValueError:
                self.console.print("[yellow]無効な入力です。プロジェクトなしに設定します。[/yellow]")
                return None
                
        except Exception as e:
            self.console.print(f"[red]プロジェクト選択でエラーが発生しました: {str(e)}[/red]")
            # フォールバック: 直接入力
            project = Prompt.ask("プロジェクト名を直接入力（Enter でスキップ）", default="")
            return project.strip() if project else None
    
    def _create_new_project_for_task(self) -> Optional[str]:
        """タスク作成時に新しいプロジェクトを作成"""
        try:
            from ..tools.project import ProjectManager, Project, ProjectStatus
            from datetime import datetime
            
            self.console.print("\n[cyan]➕ 新しいプロジェクトを作成[/cyan]")
            
            # プロジェクト名の入力
            project_name = Prompt.ask("プロジェクト名")
            if not project_name.strip():
                self.console.print("[yellow]プロジェクト作成をキャンセルしました[/yellow]")
                return None
            
            # プロジェクトの説明（オプション）
            description = Prompt.ask("プロジェクトの説明（Enter でスキップ）", default="")
            
            # プロジェクトを作成
            manager = ProjectManager()
            project = Project(
                name=project_name.strip(),
                description=description.strip() if description else None,
                status=ProjectStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # フォルダを作成
            folder_path = manager.create_project_folder(project)
            project.folder_path = folder_path
            
            # プロジェクトを保存
            projects = manager.load_projects_as_models()
            projects.append(project)
            manager.save_projects_from_models(projects)
            
            self.console.print(f"[green]✅ プロジェクト「{project_name}」を作成しました[/green]")
            self.console.print(f"[dim]📁 フォルダ: {folder_path}[/dim]")
            
            return project.name
            
        except Exception as e:
            self.console.print(f"[red]❌ プロジェクトの作成に失敗しました: {str(e)}[/red]")
            return None
    
    def _show_action_selector(self, actions, title: str) -> Optional[str]:
        """矢印キーで操作を選択するセレクター"""
        selected_index = 0
        
        kb = KeyBindings()
        
        @kb.add('up')
        def _(event):
            nonlocal selected_index
            selected_index = max(0, selected_index - 1)
        
        @kb.add('down')
        def _(event):
            nonlocal selected_index
            selected_index = min(len(actions) - 1, selected_index + 1)
        
        @kb.add('enter')
        def _(event):
            event.app.exit(result=actions[selected_index][1])
        
        @kb.add('c-c')
        def _(event):
            event.app.exit(result="cancel")
        
        @kb.add('q')
        def _(event):
            event.app.exit(result="cancel")
        
        def get_title_text():
            return HTML(f'操作選択: {title[:40]}...' if len(title) > 40 else f'操作選択: {title}')
        
        def get_actions_text():
            lines = []
            for i, (name, _) in enumerate(actions):
                if i == selected_index:
                    lines.append(f'<b>→ {name}</b>')
                else:
                    lines.append(f'  {name}')
            return HTML('\\n'.join(lines))
        
        def get_help_text():
            return HTML('↑↓ 選択  Enter 実行  q キャンセル')
        
        # ウィンドウの作成
        title_window = Window(
            content=FormattedTextControl(get_title_text),
            height=1,
            dont_extend_width=True
        )
        
        actions_window = Window(
            content=FormattedTextControl(get_actions_text),
            wrap_lines=True
        )
        
        help_window = Window(
            content=FormattedTextControl(get_help_text),
            height=1,
            dont_extend_width=True
        )
        
        # レイアウト
        layout = Layout(
            HSplit([
                title_window,
                actions_window,
                help_window,
            ])
        )
        
        # アプリケーション
        app = Application(
            layout=layout,
            key_bindings=kb,
            full_screen=False,
            mouse_support=False,
        )
        
        try:
            result = app.run()
            return result if result else "cancel"
        except KeyboardInterrupt:
            return "cancel"