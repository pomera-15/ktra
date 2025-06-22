"""
インタラクティブプロジェクトセレクター
矢印キーでプロジェクトを選択し、操作を実行
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
    from ..models import Project, ProjectStatus
    from ..tools.project import ProjectManager
    from ..tools.task import TaskManager
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

console = Console()


class ProjectSelector:
    """インタラクティブプロジェクトセレクター"""
    
    def __init__(self):
        self.console = console
        self.selected_index = 0
        self.projects = []
        self.filtered_projects = []
        self.filter_mode = "all"  # all, active, completed, planning, on_hold
        self.running = True
        
    def run(self) -> Optional[str]:
        """セレクターを実行し、選択されたアクションを返す"""
        if not PYDANTIC_AVAILABLE:
            self.console.print("[red]この機能にはPydanticモデルが必要です[/red]")
            return None
        
        try:
            self._load_projects()
            if not self.projects:
                self.console.print("プロジェクトがありません")
                if Confirm.ask("新しいプロジェクトを作成しますか？"):
                    self._handle_direct_project_creation()
                return None
            
            return self._run_selector()
            
        except Exception as e:
            self.console.print(f"[red]エラー: {str(e)}[/red]")
            return None
    
    def _load_projects(self) -> None:
        """プロジェクトを読み込み"""
        manager = ProjectManager()
        self.projects = manager.load_projects_as_models()
        self._apply_filter()
    
    def _apply_filter(self) -> None:
        """フィルターを適用"""
        if self.filter_mode == "all":
            self.filtered_projects = self.projects
        elif self.filter_mode == "active":
            self.filtered_projects = [p for p in self.projects if p.status == ProjectStatus.ACTIVE]
        elif self.filter_mode == "completed":
            self.filtered_projects = [p for p in self.projects if p.status == ProjectStatus.COMPLETED]
        elif self.filter_mode == "planning":
            self.filtered_projects = [p for p in self.projects if p.status == ProjectStatus.PLANNING]
        elif self.filter_mode == "on_hold":
            self.filtered_projects = [p for p in self.projects if p.status == ProjectStatus.ON_HOLD]
        else:
            self.filtered_projects = self.projects
        
        # インデックスをリセット
        self.selected_index = min(self.selected_index, len(self.filtered_projects) - 1) if self.filtered_projects else 0
    
    def _run_selector(self) -> Optional[str]:
        """セレクターのメインループ"""
        kb = KeyBindings()
        
        @kb.add('up')
        def _(event):
            if self.filtered_projects:
                self.selected_index = max(0, self.selected_index - 1)
        
        @kb.add('down')
        def _(event):
            if self.filtered_projects:
                self.selected_index = min(len(self.filtered_projects) - 1, self.selected_index + 1)
        
        @kb.add('enter')
        def _(event):
            if self.filtered_projects:
                event.app.exit(result="select_project")
        
        @kb.add('c-c')
        def _(event):
            event.app.exit(result="cancel")
        
        @kb.add('q')
        def _(event):
            event.app.exit(result="cancel")
        
        @kb.add('n')
        def _(event):
            event.app.exit(result="create_project_direct")
        
        @kb.add('f')
        def _(event):
            event.app.exit(result="filter")
        
        @kb.add('h')
        def _(event):
            event.app.exit(result="help")
        
        @kb.add('r')
        def _(event):
            self._load_projects()
        
        @kb.add('o')
        def _(event):
            if self.filtered_projects:
                event.app.exit(result="open_folder")
        
        # レイアウトの構築
        def get_title_text():
            filter_text = f" ({self.filter_mode})" if self.filter_mode != "all" else ""
            return HTML(f'プロジェクト一覧{filter_text}')
        
        def get_projects_text():
            if not self.filtered_projects:
                return HTML('プロジェクトがありません')
            
            lines = []
            for i, project in enumerate(self.filtered_projects):
                # タスク数を取得
                task_count = self._get_project_task_count(project.name)
                
                # 選択状態の表示
                if i == self.selected_index:
                    # 選択中のプロジェクト（シンプル）
                    name = project.name[:50] + "..." if len(project.name) > 50 else project.name
                    lines.append(f'<b>→ {name} ({task_count}タスク)</b>')
                else:
                    # 通常のプロジェクト（シンプル）
                    name = project.name[:50] + "..." if len(project.name) > 50 else project.name
                    lines.append(f'  {name} ({task_count}タスク)')
            
            return HTML('\\n'.join(lines))
        
        def get_help_text():
            return HTML('↑↓ 選択  Enter 操作  n 新規  f フィルター  o フォルダ開く  q 終了')
        
        # ウィンドウの作成
        title_window = Window(
            content=FormattedTextControl(get_title_text),
            height=1,
            dont_extend_width=True
        )
        
        projects_window = Window(
            content=FormattedTextControl(get_projects_text),
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
                projects_window,
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
                elif result == "select_project":
                    return self._handle_project_selection()
                elif result == "create_project_direct":
                    self._handle_direct_project_creation()
                    continue
                elif result == "filter":
                    self._handle_filter_selection()
                    continue
                elif result == "help":
                    self._show_help()
                    continue
                elif result == "open_folder":
                    self._handle_open_folder()
                    continue
                else:
                    return None
                    
            except KeyboardInterrupt:
                return None
    
    def _handle_project_selection(self) -> Optional[str]:
        """選択されたプロジェクトの操作メニューを表示"""
        if not self.filtered_projects or self.selected_index >= len(self.filtered_projects):
            return None
        
        selected_project = self.filtered_projects[self.selected_index]
        
        # プロジェクト詳細を表示
        self._display_project_details(selected_project)
        
        # 操作メニュー
        self.console.print("\\n操作を選択してください:")
        
        actions = [
            ("1", "ステータス変更", "update_status"),
            ("2", "詳細を編集", "edit_project"),
            ("3", "フォルダを開く", "open_folder"),
            ("4", "メモを作成", "create_note"),
            ("5", "ファイル一覧", "list_files"),
            ("6", "削除", "delete_project"),
            ("7", "キャンセル", "cancel")
        ]
        
        for num, name, _ in actions:
            self.console.print(f"  {num}. {name}")
        
        choice = Prompt.ask("選択（1-7）", choices=["1", "2", "3", "4", "5", "6", "7"], default="7")
        
        action_map = {action[0]: action[2] for action in actions}
        selected_action = action_map[choice]
        
        if selected_action == "cancel":
            return None
        elif selected_action == "update_status":
            return self._handle_status_update(selected_project)
        elif selected_action == "edit_project":
            return self._handle_project_edit(selected_project)
        elif selected_action == "open_folder":
            return self._handle_open_folder()
        elif selected_action == "create_note":
            return self._handle_create_note(selected_project)
        elif selected_action == "list_files":
            return self._handle_list_files(selected_project)
        elif selected_action == "delete_project":
            return self._handle_project_delete(selected_project)
        
        return None
    
    def _handle_status_update(self, project: Project) -> Optional[str]:
        """ステータス更新"""
        self.console.print(f"\\n[blue]📝 ステータス変更: {project.name}[/blue]")
        
        statuses = [
            ("1", "📋 計画中", ProjectStatus.PLANNING),
            ("2", "🚀 アクティブ", ProjectStatus.ACTIVE),
            ("3", "⏸️ 保留中", ProjectStatus.ON_HOLD),
            ("4", "✅ 完了", ProjectStatus.COMPLETED),
            ("5", "📦 アーカイブ", ProjectStatus.ARCHIVED)
        ]
        
        self.console.print("新しいステータス:")
        for num, name, _ in statuses:
            self.console.print(f"  {num}. {name}")
        
        choice = Prompt.ask("選択（1-5）", choices=["1", "2", "3", "4", "5"])
        new_status = statuses[int(choice) - 1][2]
        
        # ステータス更新
        try:
            manager = ProjectManager()
            projects = manager.load_projects_as_models()
            
            for i, p in enumerate(projects):
                if p.id == project.id:
                    projects[i].status = new_status
                    from datetime import datetime
                    projects[i].updated_at = datetime.now()
                    break
            
            manager.save_projects_from_models(projects)
            
            self.console.print(f"[green]✅ ステータスを更新しました: {statuses[int(choice) - 1][1]}[/green]")
            
            # プロジェクトリストを再読み込み
            self._load_projects()
            
        except Exception as e:
            self.console.print(f"[red]❌ 更新に失敗しました: {str(e)}[/red]")
        
        return None
    
    def _handle_project_edit(self, project: Project) -> Optional[str]:
        """プロジェクト編集"""
        self.console.print(f"\\n[blue]📝 プロジェクト編集: {project.name}[/blue]")
        
        # 新しい名前
        new_name = Prompt.ask("プロジェクト名", default=project.name)
        if not new_name.strip():
            self.console.print("[yellow]編集をキャンセルしました[/yellow]")
            return None
        
        # 新しい説明
        new_description = Prompt.ask("説明", default=project.description or "")
        
        # タグ
        current_tags = ", ".join(project.tags) if project.tags else ""
        new_tags_str = Prompt.ask("タグ（カンマ区切り）", default=current_tags)
        new_tags = [tag.strip() for tag in new_tags_str.split(",") if tag.strip()] if new_tags_str else []
        
        # 更新
        try:
            manager = ProjectManager()
            projects = manager.load_projects_as_models()
            
            for i, p in enumerate(projects):
                if p.id == project.id:
                    projects[i].name = new_name.strip()
                    projects[i].description = new_description.strip() if new_description else None
                    projects[i].tags = new_tags
                    from datetime import datetime
                    projects[i].updated_at = datetime.now()
                    break
            
            manager.save_projects_from_models(projects)
            
            self.console.print(f"[green]✅ プロジェクトを更新しました: {new_name}[/green]")
            
            # プロジェクトリストを再読み込み
            self._load_projects()
            
        except Exception as e:
            self.console.print(f"[red]❌ 更新に失敗しました: {str(e)}[/red]")
        
        return None
    
    def _handle_open_folder(self) -> Optional[str]:
        """フォルダを開く"""
        if not self.filtered_projects or self.selected_index >= len(self.filtered_projects):
            return None
        
        selected_project = self.filtered_projects[self.selected_index]
        
        if not selected_project.folder_path:
            self.console.print("[yellow]このプロジェクトにはフォルダが設定されていません[/yellow]")
            return None
        
        try:
            import subprocess
            import os
            
            folder_path = selected_project.folder_path
            if not os.path.exists(folder_path):
                self.console.print(f"[red]フォルダが見つかりません: {folder_path}[/red]")
                return None
            
            # macOSの場合
            if os.name == 'posix':
                subprocess.run(['open', folder_path])
                self.console.print(f"[green]📁 フォルダを開きました: {folder_path}[/green]")
            else:
                self.console.print(f"[blue]📁 フォルダパス: {folder_path}[/blue]")
                
        except Exception as e:
            self.console.print(f"[red]❌ フォルダを開けませんでした: {str(e)}[/red]")
        
        return None
    
    def _handle_create_note(self, project: Project) -> Optional[str]:
        """メモを作成"""
        self.console.print(f"\\n[blue]📝 メモ作成: {project.name}[/blue]")
        
        note_title = Prompt.ask("メモのタイトル")
        if not note_title.strip():
            self.console.print("[yellow]メモ作成をキャンセルしました[/yellow]")
            return None
        
        content = Prompt.ask("メモの内容（複数行の場合は後で編集してください）")
        
        # メモを作成
        try:
            from ..tools.project import _create_project_note
            result = _create_project_note(project.name, note_title.strip(), content.strip())
            self.console.print(result)
            
        except Exception as e:
            self.console.print(f"[red]❌ メモの作成に失敗しました: {str(e)}[/red]")
        
        return None
    
    def _handle_list_files(self, project: Project) -> Optional[str]:
        """ファイル一覧表示"""
        self.console.print(f"\\n[blue]📁 ファイル一覧: {project.name}[/blue]")
        
        try:
            manager = ProjectManager()
            files = manager.get_project_files(project.id)
            
            if not files:
                self.console.print("[yellow]ファイルがありません[/yellow]")
                return None
            
            # ファイル一覧を表示
            table = Table(title=f"📁 {project.name} のファイル", show_header=True, header_style="bold cyan")
            table.add_column("パス", style="cyan", width=40)
            table.add_column("サイズ", style="white", width=10)
            table.add_column("更新日", style="dim", width=20)
            
            for file in files[:20]:  # 最大20件表示
                size_kb = f"{file['size']/1024:.1f}KB"
                modified = file['modified'][:19]  # 秒まで表示
                table.add_row(file['relative_path'], size_kb, modified)
            
            self.console.print(table)
            
            if len(files) > 20:
                self.console.print(f"[dim]... 他 {len(files)-20} 件のファイル[/dim]")
            
        except Exception as e:
            self.console.print(f"[red]❌ ファイル一覧の取得に失敗しました: {str(e)}[/red]")
        
        return None
    
    def _handle_project_delete(self, project: Project) -> Optional[str]:
        """プロジェクト削除"""
        self.console.print(f"\\n[red]🗑️ プロジェクト削除: {project.name}[/red]")
        
        if not Confirm.ask("このプロジェクトを削除しますか？"):
            self.console.print("[blue]削除をキャンセルしました[/blue]")
            return None
        
        try:
            manager = ProjectManager()
            projects = manager.load_projects_as_models()
            
            # プロジェクトを削除
            projects = [p for p in projects if p.id != project.id]
            manager.save_projects_from_models(projects)
            
            self.console.print(f"[green]✅ プロジェクトを削除しました: {project.name}[/green]")
            self.console.print("[yellow]⚠️ プロジェクトフォルダは手動で削除してください[/yellow]")
            
            # プロジェクトリストを再読み込み
            self._load_projects()
            
        except Exception as e:
            self.console.print(f"[red]❌ 削除に失敗しました: {str(e)}[/red]")
        
        return None
    
    def _handle_direct_project_creation(self) -> None:
        """直接プロジェクト作成"""
        self.console.print("\\n新しいプロジェクトを作成")
        
        # プロジェクト名の入力
        name = Prompt.ask("プロジェクト名")
        if not name.strip():
            self.console.print("[yellow]プロジェクトの作成をキャンセルしました[/yellow]")
            return
        
        # 基本情報の入力（オプション）
        description = Prompt.ask("説明（Enter でスキップ）", default="")
        tags = Prompt.ask("タグ（カンマ区切り、Enter でスキップ）", default="")
        
        # 新しいプロジェクトを作成
        try:
            from datetime import datetime
            
            new_project = Project(
                name=name.strip(),
                description=description.strip() if description else None,
                tags=[tag.strip() for tag in tags.split(",") if tag.strip()] if tags else [],
                status=ProjectStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # フォルダを作成
            manager = ProjectManager()
            folder_path = manager.create_project_folder(new_project)
            new_project.folder_path = folder_path
            
            # プロジェクトを保存
            projects = manager.load_projects_as_models()
            projects.append(new_project)
            manager.save_projects_from_models(projects)
            
            self.console.print(f"[green]✅ プロジェクトを作成しました: {name}[/green]")
            self.console.print(f"[dim]📁 フォルダ: {folder_path}[/dim]")
            
            # プロジェクトリストを再読み込み
            self._load_projects()
            
        except Exception as e:
            self.console.print(f"[red]❌ プロジェクトの作成に失敗しました: {str(e)}[/red]")
    
    def _handle_filter_selection(self) -> None:
        """フィルター選択"""
        self.console.print("\\nフィルター選択:")
        
        filters = [
            ("1", "すべて", "all"),
            ("2", "アクティブ", "active"),
            ("3", "計画中", "planning"),
            ("4", "保留中", "on_hold"),
            ("5", "完了済み", "completed")
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
[bold cyan]📁 プロジェクトセレクター ヘルプ[/bold cyan]

[bold]キーボード操作:[/bold]
• ↑/↓  - プロジェクト選択
• Enter - 操作メニューを開く
• n     - 新しいプロジェクトを作成（直接入力）
• f     - フィルター変更
• o     - プロジェクトフォルダを開く
• r     - プロジェクトリストを更新
• h     - このヘルプを表示
• q     - 終了

[bold]操作メニュー:[/bold]
• ステータス変更 - プロジェクトの状態を変更
• 詳細を編集    - プロジェクト情報の編集
• フォルダを開く - プロジェクトフォルダをFinderで開く
• メモを作成    - プロジェクトメモの作成
• ファイル一覧  - プロジェクト内ファイルの確認
• 削除         - プロジェクトの削除

[bold]フィルター:[/bold]
• すべて   - 全プロジェクトを表示
• アクティブ - アクティブなプロジェクトのみ
• 計画中   - 計画中のプロジェクトのみ
• 保留中   - 保留中のプロジェクトのみ
• 完了済み - 完了したプロジェクトのみ
"""
        
        panel = Panel(help_text.strip(), title="ヘルプ", border_style="cyan")
        self.console.print(panel)
        
        Prompt.ask("Enterキーで戻る", default="")
    
    def _display_project_details(self, project: Project) -> None:
        """プロジェクトの詳細を表示"""
        status_display = self._get_status_display_name(project.status.value)
        task_count = self._get_project_task_count(project.name)
        
        content = f"""
[bold]{project.name}[/bold]

{self._get_status_icon(project.status)} {status_display}

📄 説明: {project.description or '（なし）'}
📋 タスク数: {task_count}件
"""
        
        if project.due_date:
            content += f"📅 期限: {project.due_date.strftime('%Y-%m-%d')}\\n"
        
        if project.folder_path:
            content += f"📁 フォルダ: {project.folder_path}\\n"
        
        if project.tags:
            content += f"🏷️ タグ: {', '.join(project.tags)}\\n"
        
        content += f"\\n🆔 ID: {project.id[:8]}...\\n"
        content += f"📅 作成: {project.created_at.strftime('%Y-%m-%d %H:%M')}\\n"
        content += f"📅 更新: {project.updated_at.strftime('%Y-%m-%d %H:%M')}\\n"
        
        panel = Panel(content.strip(), title="📁 プロジェクト詳細", border_style="blue")
        self.console.print(panel)
    
    def _get_status_icon(self, status: ProjectStatus) -> str:
        """ステータスアイコンを取得"""
        icons = {
            ProjectStatus.PLANNING: "📋",
            ProjectStatus.ACTIVE: "🚀",
            ProjectStatus.ON_HOLD: "⏸️",
            ProjectStatus.COMPLETED: "✅",
            ProjectStatus.ARCHIVED: "📦"
        }
        return icons.get(status, "❓")
    
    def _get_status_display_name(self, status: str) -> str:
        """ステータス表示名を取得"""
        names = {
            "planning": "📋 計画中",
            "active": "🚀 アクティブ",
            "on_hold": "⏸️ 保留中",
            "completed": "✅ 完了",
            "archived": "📦 アーカイブ"
        }
        return names.get(status, status)
    
    def _get_project_task_count(self, project_name: str) -> int:
        """プロジェクトのタスク数を取得"""
        try:
            task_manager = TaskManager()
            tasks = task_manager.load_tasks_as_models()
            return len([t for t in tasks if t.project == project_name])
        except:
            return 0