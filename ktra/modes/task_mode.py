"""
タスクモードインターフェース
/tasks コマンドで呼び出されるタスク管理専用モード
"""

from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
from datetime import datetime

# Pydanticモデルをインポート
try:
    from ..models import Task, TaskStatus, TaskPriority, EnergyLevel
    from ..tools.task import TaskManager
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

console = Console()


class TaskMode:
    """タスクモード管理クラス"""
    
    def __init__(self):
        self.console = console
        self.running = True
        
    def run(self) -> None:
        """タスクモードのメインループ"""
        self.show_welcome()
        
        while self.running:
            try:
                command = self.get_command()
                if not command:
                    continue
                    
                if command.lower() in ['exit', 'quit', '/exit', '/quit']:
                    self.running = False
                    break
                    
                self.execute_command(command)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]タスクモードを終了します[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]エラー: {str(e)}[/red]")
    
    def show_welcome(self) -> None:
        """ウェルカムメッセージを表示"""
        welcome_text = """
[bold cyan]📝 タスクモードへようこそ！[/bold cyan]

利用可能なコマンド:
• [bold]list[/bold] / [bold]ls[/bold]     - タスク一覧を表示
• [bold]create[/bold] / [bold]new[/bold]  - 新しいタスクを作成
• [bold]show <id>[/bold]    - タスク詳細を表示
• [bold]update <id>[/bold]  - タスクを更新
• [bold]delete <id>[/bold]  - タスクを削除
• [bold]search <query>[/bold] - タスクを検索
• [bold]filter[/bold]       - フィルタ表示
• [bold]stats[/bold]        - 統計情報
• [bold]help[/bold]         - ヘルプを表示
• [bold]exit[/bold] / [bold]quit[/bold] - タスクモードを終了

💡 IDの代わりにタスクタイトルの一部も使用できます
"""
        panel = Panel(welcome_text.strip(), title="🚀 タスクモード", border_style="cyan")
        self.console.print(panel)
    
    def get_command(self) -> str:
        """コマンドを取得"""
        return Prompt.ask("[cyan]tasks>[/cyan]", default="").strip()
    
    def execute_command(self, command: str) -> None:
        """コマンドを実行"""
        parts = command.split()
        if not parts:
            return
            
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd in ['list', 'ls']:
            self.cmd_list(args)
        elif cmd in ['create', 'new']:
            self.cmd_create()
        elif cmd == 'show':
            self.cmd_show(args)
        elif cmd == 'update':
            self.cmd_update(args)
        elif cmd == 'delete':
            self.cmd_delete(args)
        elif cmd == 'search':
            self.cmd_search(args)
        elif cmd == 'filter':
            self.cmd_filter()
        elif cmd == 'stats':
            self.cmd_stats()
        elif cmd == 'help':
            self.show_welcome()
        else:
            self.console.print(f"[red]不明なコマンド: {cmd}[/red]")
            self.console.print("[yellow]'help' でコマンド一覧を確認してください[/yellow]")
    
    def cmd_list(self, args: List[str]) -> None:
        """タスク一覧を表示"""
        if not PYDANTIC_AVAILABLE:
            self.console.print("[red]この機能にはPydanticモデルが必要です[/red]")
            return
        
        try:
            manager = TaskManager()
            tasks = manager.load_tasks_as_models()
            
            if not tasks:
                self.console.print("[yellow]タスクがありません[/yellow]")
                return
            
            # 引数でのフィルタリング
            if args:
                if args[0] in ['pending', 'inbox', 'next', 'in_progress', 'blocked', 'done', 'archived']:
                    tasks = [task for task in tasks if task.status.value == args[0]]
                elif args[0] in ['high', 'medium', 'low']:
                    tasks = [task for task in tasks if task.energy_required.value == args[0]]
            
            self._display_tasks_table(tasks)
            
        except Exception as e:
            self.console.print(f"[red]エラー: {str(e)}[/red]")
    
    def cmd_create(self) -> None:
        """新しいタスクを作成"""
        if not PYDANTIC_AVAILABLE:
            self.console.print("[red]この機能にはPydanticモデルが必要です[/red]")
            return
        
        try:
            self.console.print("[bold green]📝 新しいタスクを作成します[/bold green]")
            
            # タイトル
            title = Prompt.ask("タスクのタイトル")
            if not title.strip():
                self.console.print("[red]タイトルは必須です[/red]")
                return
            
            # 説明
            description = Prompt.ask("説明（オプション）", default="")
            
            # 優先度
            priorities = [
                ("1", "緊急・重要", TaskPriority.URGENT_IMPORTANT),
                ("2", "重要・非緊急", TaskPriority.NOT_URGENT_IMPORTANT),
                ("3", "緊急・非重要", TaskPriority.URGENT_NOT_IMPORTANT),
                ("4", "非緊急・非重要", TaskPriority.NOT_URGENT_NOT_IMPORTANT)
            ]
            
            self.console.print("\n🎯 優先度:")
            for num, name, _ in priorities:
                self.console.print(f"  {num}. {name}")
            
            priority_choice = Prompt.ask("選択（1-4）", choices=["1", "2", "3", "4"], default="2")
            priority = priorities[int(priority_choice) - 1][2]
            
            # エネルギーレベル
            energies = [
                ("1", "高", EnergyLevel.HIGH),
                ("2", "中", EnergyLevel.MEDIUM),
                ("3", "低", EnergyLevel.LOW)
            ]
            
            self.console.print("\n⚡ エネルギーレベル:")
            for num, name, _ in energies:
                self.console.print(f"  {num}. {name}")
            
            energy_choice = Prompt.ask("選択（1-3）", choices=["1", "2", "3"], default="2")
            energy_level = energies[int(energy_choice) - 1][2]
            
            # 推定時間
            estimated_minutes = Prompt.ask("⏱️ 推定時間（分）", default="30")
            try:
                estimated_minutes = max(5, min(480, int(estimated_minutes)))
            except ValueError:
                estimated_minutes = 30
            
            # タグ
            tags_input = Prompt.ask("🏷️ タグ（カンマ区切り、オプション）", default="")
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
            
            # プロジェクト
            project = Prompt.ask("📁 プロジェクト（オプション）", default="")
            
            # タスク作成
            task = Task(
                title=title,
                description=description,
                priority=priority,
                energy_required=energy_level,
                estimated_minutes=estimated_minutes,
                tags=tags,
                project=project if project else None,
                status=TaskStatus.INBOX
            )
            
            # 保存
            manager = TaskManager()
            existing_tasks = manager.load_tasks_as_models()
            existing_tasks.append(task)
            manager.save_tasks_from_models(existing_tasks)
            
            self.console.print(f"[green]✅ タスクを作成しました: {task.title}[/green]")
            self._display_task_details(task)
            
        except Exception as e:
            self.console.print(f"[red]エラー: {str(e)}[/red]")
    
    def cmd_show(self, args: List[str]) -> None:
        """タスク詳細を表示"""
        if not args:
            self.console.print("[red]タスクIDまたはタイトルを指定してください[/red]")
            return
        
        task = self._find_task(" ".join(args))
        if not task:
            return
        
        self._display_task_details(task, full=True)
    
    def cmd_update(self, args: List[str]) -> None:
        """タスクを更新"""
        if not args:
            self.console.print("[red]タスクIDまたはタイトルを指定してください[/red]")
            return
        
        if not PYDANTIC_AVAILABLE:
            self.console.print("[red]この機能にはPydanticモデルが必要です[/red]")
            return
        
        try:
            manager = TaskManager()
            tasks = manager.load_tasks_as_models()
            
            # タスクを検索
            search_term = " ".join(args)
            target_task = None
            task_index = None
            
            for i, task in enumerate(tasks):
                if task.id == search_term or search_term.lower() in task.title.lower():
                    target_task = task
                    task_index = i
                    break
            
            if not target_task:
                self.console.print(f"[red]タスクが見つかりません: {search_term}[/red]")
                return
            
            self.console.print(f"[blue]📝 タスクを更新: {target_task.title}[/blue]")
            
            # 更新項目を対話的に選択
            updates = {}
            
            # ステータス
            if Confirm.ask("ステータスを変更しますか？", default=False):
                statuses = [
                    ("1", "受信箱", TaskStatus.INBOX),
                    ("2", "次のアクション", TaskStatus.NEXT),
                    ("3", "実行中", TaskStatus.IN_PROGRESS),
                    ("4", "ブロック中", TaskStatus.BLOCKED),
                    ("5", "完了", TaskStatus.DONE),
                    ("6", "アーカイブ", TaskStatus.ARCHIVED)
                ]
                
                self.console.print("新しいステータス:")
                for num, name, _ in statuses:
                    self.console.print(f"  {num}. {name}")
                
                status_choice = Prompt.ask("選択（1-6）", choices=["1", "2", "3", "4", "5", "6"])
                new_status = statuses[int(status_choice) - 1][2]
                updates["status"] = new_status
                
                if new_status == TaskStatus.DONE and not target_task.completed_at:
                    updates["completed_at"] = datetime.now()
            
            # 実際時間（完了時）
            if updates.get("status") == TaskStatus.DONE:
                actual_time = Prompt.ask("実際にかかった時間（分）", default=str(target_task.estimated_minutes))
                try:
                    updates["actual_minutes"] = int(actual_time)
                except ValueError:
                    pass
            
            # 優先度
            if Confirm.ask("優先度を変更しますか？", default=False):
                priorities = [
                    ("1", "緊急・重要", TaskPriority.URGENT_IMPORTANT),
                    ("2", "重要・非緊急", TaskPriority.NOT_URGENT_IMPORTANT),
                    ("3", "緊急・非重要", TaskPriority.URGENT_NOT_IMPORTANT),
                    ("4", "非緊急・非重要", TaskPriority.NOT_URGENT_NOT_IMPORTANT)
                ]
                
                self.console.print("新しい優先度:")
                for num, name, _ in priorities:
                    self.console.print(f"  {num}. {name}")
                
                priority_choice = Prompt.ask("選択（1-4）", choices=["1", "2", "3", "4"])
                updates["priority"] = priorities[int(priority_choice) - 1][2]
            
            if not updates:
                self.console.print("[yellow]更新する項目がありません[/yellow]")
                return
            
            # 更新の適用
            updates["updated_at"] = datetime.now()
            
            for key, value in updates.items():
                setattr(target_task, key, value)
            
            # 保存
            manager.save_tasks_from_models(tasks)
            
            self.console.print(f"[green]✅ タスクを更新しました[/green]")
            self._display_task_details(target_task)
            
        except Exception as e:
            self.console.print(f"[red]エラー: {str(e)}[/red]")
    
    def cmd_delete(self, args: List[str]) -> None:
        """タスクを削除"""
        if not args:
            self.console.print("[red]タスクIDまたはタイトルを指定してください[/red]")
            return
        
        task = self._find_task(" ".join(args))
        if not task:
            return
        
        # 確認
        self.console.print(f"[yellow]削除対象のタスク:[/yellow]")
        self._display_task_details(task)
        
        if not Confirm.ask("このタスクを削除しますか？"):
            self.console.print("[blue]削除をキャンセルしました[/blue]")
            return
        
        try:
            manager = TaskManager()
            tasks = manager.load_tasks_as_models()
            
            # タスクを削除
            tasks = [t for t in tasks if t.id != task.id]
            manager.save_tasks_from_models(tasks)
            
            self.console.print(f"[green]✅ タスクを削除しました: {task.title}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]エラー: {str(e)}[/red]")
    
    def cmd_search(self, args: List[str]) -> None:
        """タスクを検索"""
        if not args:
            self.console.print("[red]検索キーワードを指定してください[/red]")
            return
        
        if not PYDANTIC_AVAILABLE:
            self.console.print("[red]この機能にはPydanticモデルが必要です[/red]")
            return
        
        try:
            manager = TaskManager()
            tasks = manager.load_tasks_as_models()
            
            query = " ".join(args).lower()
            filtered_tasks = []
            
            for task in tasks:
                if (query in task.title.lower() or 
                    query in (task.description or "").lower() or
                    any(query in tag.lower() for tag in task.tags) or
                    (task.project and query in task.project.lower())):
                    filtered_tasks.append(task)
            
            if not filtered_tasks:
                self.console.print(f"[yellow]'{query}' に一致するタスクが見つかりませんでした[/yellow]")
                return
            
            self.console.print(f"[cyan]🔍 検索結果: '{query}' ({len(filtered_tasks)}件)[/cyan]")
            self._display_tasks_table(filtered_tasks)
            
        except Exception as e:
            self.console.print(f"[red]エラー: {str(e)}[/red]")
    
    def cmd_filter(self) -> None:
        """フィルタ表示"""
        if not PYDANTIC_AVAILABLE:
            self.console.print("[red]この機能にはPydanticモデルが必要です[/red]")
            return
        
        try:
            manager = TaskManager()
            tasks = manager.load_tasks_as_models()
            
            if not tasks:
                self.console.print("[yellow]タスクがありません[/yellow]")
                return
            
            # フィルタ選択
            filter_options = [
                ("1", "ステータス別"),
                ("2", "優先度別"),
                ("3", "エネルギーレベル別"),
                ("4", "プロジェクト別"),
                ("5", "期限別")
            ]
            
            self.console.print("📊 フィルタオプション:")
            for num, name in filter_options:
                self.console.print(f"  {num}. {name}")
            
            choice = Prompt.ask("選択（1-5）", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":  # ステータス別
                status_groups = {}
                for task in tasks:
                    status = task.status.value
                    if status not in status_groups:
                        status_groups[status] = []
                    status_groups[status].append(task)
                
                for status, group_tasks in status_groups.items():
                    self.console.print(f"\n[bold]{self._get_status_display_name(status)} ({len(group_tasks)}件)[/bold]")
                    self._display_tasks_table(group_tasks, compact=True)
            
            elif choice == "2":  # 優先度別
                priority_groups = {}
                for task in tasks:
                    priority = task.priority.value
                    if priority not in priority_groups:
                        priority_groups[priority] = []
                    priority_groups[priority].append(task)
                
                priority_order = ["urgent_important", "not_urgent_important", "urgent_not_important", "not_urgent_not_important"]
                for priority in priority_order:
                    if priority in priority_groups:
                        group_tasks = priority_groups[priority]
                        self.console.print(f"\n[bold]{self._get_priority_display_name(priority)} ({len(group_tasks)}件)[/bold]")
                        self._display_tasks_table(group_tasks, compact=True)
            
        except Exception as e:
            self.console.print(f"[red]エラー: {str(e)}[/red]")
    
    def cmd_stats(self) -> None:
        """統計情報を表示"""
        if not PYDANTIC_AVAILABLE:
            self.console.print("[red]この機能にはPydanticモデルが必要です[/red]")
            return
        
        try:
            manager = TaskManager()
            tasks = manager.load_tasks_as_models()
            
            if not tasks:
                self.console.print("[yellow]タスクがありません[/yellow]")
                return
            
            # 基本統計
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == TaskStatus.DONE])
            in_progress_tasks = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
            blocked_tasks = len([t for t in tasks if t.status == TaskStatus.BLOCKED])
            
            # 統計表示
            stats_text = f"""
[bold cyan]📊 タスク統計情報[/bold cyan]

📝 全体:
  • 総タスク数: {total_tasks}件
  • 完了: {completed_tasks}件 ({completed_tasks/total_tasks*100:.1f}%)
  • 実行中: {in_progress_tasks}件
  • ブロック中: {blocked_tasks}件

⚡ エネルギーレベル別:
"""
            
            # エネルギーレベル別統計
            energy_stats = {}
            for task in tasks:
                energy = task.energy_required.value
                energy_stats[energy] = energy_stats.get(energy, 0) + 1
            
            for energy, count in energy_stats.items():
                stats_text += f"  • {energy}: {count}件\n"
            
            # プロジェクト別統計
            project_stats = {}
            for task in tasks:
                project = task.project or "未分類"
                project_stats[project] = project_stats.get(project, 0) + 1
            
            if len(project_stats) > 1:
                stats_text += "\n📁 プロジェクト別:\n"
                for project, count in sorted(project_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
                    stats_text += f"  • {project}: {count}件\n"
            
            panel = Panel(stats_text.strip(), title="📈 統計", border_style="green")
            self.console.print(panel)
            
        except Exception as e:
            self.console.print(f"[red]エラー: {str(e)}[/red]")
    
    def _find_task(self, search_term: str) -> Optional[Task]:
        """タスクを検索"""
        if not PYDANTIC_AVAILABLE:
            return None
        
        try:
            manager = TaskManager()
            tasks = manager.load_tasks_as_models()
            
            for task in tasks:
                if task.id == search_term or search_term.lower() in task.title.lower():
                    return task
            
            self.console.print(f"[red]タスクが見つかりません: {search_term}[/red]")
            return None
            
        except Exception as e:
            self.console.print(f"[red]エラー: {str(e)}[/red]")
            return None
    
    def _display_tasks_table(self, tasks: List[Task], compact: bool = False) -> None:
        """タスクをテーブル形式で表示"""
        if not tasks:
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        
        if compact:
            table.add_column("ステータス", width=8)
            table.add_column("タイトル", min_width=30)
            table.add_column("時間", width=8)
        else:
            table.add_column("ID", width=8)
            table.add_column("ステータス", width=10)
            table.add_column("優先度", width=12)
            table.add_column("タイトル", min_width=25)
            table.add_column("エネルギー", width=10)
            table.add_column("時間", width=8)
            table.add_column("プロジェクト", width=12)
        
        for task in tasks:
            if compact:
                table.add_row(
                    self._get_status_icon(task.status),
                    task.title[:40] + "..." if len(task.title) > 40 else task.title,
                    f"{task.estimated_minutes}分"
                )
            else:
                table.add_row(
                    task.id[:8] + "...",
                    self._get_status_icon(task.status),
                    self._get_priority_icon(task.priority),
                    task.title[:30] + "..." if len(task.title) > 30 else task.title,
                    self._get_energy_icon(task.energy_required),
                    f"{task.estimated_minutes}分",
                    task.project[:10] + "..." if task.project and len(task.project) > 10 else (task.project or "-")
                )
        
        self.console.print(table)
        self.console.print(f"[dim]表示件数: {len(tasks)}件[/dim]")
    
    def _display_task_details(self, task: Task, full: bool = False) -> None:
        """タスクの詳細情報を表示"""
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
        
        if full:
            content += f"""
🆔 ID: {task.id}
📅 作成: {task.created_at.strftime('%Y-%m-%d %H:%M')}
📝 更新: {task.updated_at.strftime('%Y-%m-%d %H:%M')}
"""
            
            if task.completed_at:
                content += f"✅ 完了: {task.completed_at.strftime('%Y-%m-%d %H:%M')}\n"
        
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