#!/usr/bin/env python3
"""
タスクCRUDコマンドライン インターフェース
/tasks コマンドでタスクの作成、読み取り、更新、削除を実行
"""

import argparse
import sys
import json
from datetime import datetime
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text

# Pydanticモデルをインポート
try:
    from ..models import Task, TaskStatus, TaskPriority, EnergyLevel, convert_legacy_task
    from ..tools.task import TaskManager
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

console = Console()


def create_task_interactive() -> Optional[dict]:
    """対話的にタスクを作成"""
    console.print("[bold green]新しいタスクを作成します[/bold green]")
    
    # タイトル
    title = Prompt.ask("📝 タスクのタイトル", default="")
    if not title.strip():
        console.print("[red]タイトルは必須です[/red]")
        return None
    
    # 説明
    description = Prompt.ask("📄 説明（オプション）", default="")
    
    # 優先度
    priority_choices = ["urgent_important", "not_urgent_important", "urgent_not_important", "not_urgent_not_important"]
    priority_display = {
        "urgent_important": "緊急・重要",
        "not_urgent_important": "重要・非緊急", 
        "urgent_not_important": "緊急・非重要",
        "not_urgent_not_important": "非緊急・非重要"
    }
    
    console.print("\n🎯 優先度を選択してください:")
    for i, choice in enumerate(priority_choices, 1):
        console.print(f"  {i}. {priority_display[choice]}")
    
    priority_num = Prompt.ask("選択（1-4）", choices=["1", "2", "3", "4"], default="2")
    priority = priority_choices[int(priority_num) - 1]
    
    # エネルギーレベル
    energy_choices = ["high", "medium", "low"]
    energy_display = {"high": "高", "medium": "中", "low": "低"}
    
    console.print("\n⚡ 必要エネルギーレベル:")
    for i, choice in enumerate(energy_choices, 1):
        console.print(f"  {i}. {energy_display[choice]}")
    
    energy_num = Prompt.ask("選択（1-3）", choices=["1", "2", "3"], default="2")
    energy_level = energy_choices[int(energy_num) - 1]
    
    # 推定時間
    estimated_minutes = Prompt.ask("⏱️  推定時間（分）", default="30")
    try:
        estimated_minutes = int(estimated_minutes)
        if estimated_minutes < 5 or estimated_minutes > 480:
            console.print("[yellow]推定時間は5-480分の範囲で設定してください[/yellow]")
            estimated_minutes = 30
    except ValueError:
        estimated_minutes = 30
    
    # タグ
    tags_input = Prompt.ask("🏷️  タグ（カンマ区切り、オプション）", default="")
    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
    
    # プロジェクト
    project = Prompt.ask("📁 プロジェクト（オプション）", default="")
    
    # 期限
    due_date_input = Prompt.ask("📅 期限（YYYY-MM-DD形式、オプション）", default="")
    due_date = None
    if due_date_input:
        try:
            due_date = datetime.strptime(due_date_input, "%Y-%m-%d")
        except ValueError:
            console.print("[yellow]期限の形式が正しくありません。スキップします[/yellow]")
    
    return {
        "title": title,
        "description": description,
        "priority": priority,
        "energy_level": energy_level,
        "estimated_minutes": estimated_minutes,
        "tags": tags,
        "project": project if project else None,
        "due_date": due_date
    }


def create_task(args) -> None:
    """タスクを作成"""
    if not PYDANTIC_AVAILABLE:
        console.print("[red]この機能にはPydanticモデルが必要です[/red]")
        return
    
    try:
        manager = TaskManager()
        
        if args.interactive:
            task_data = create_task_interactive()
            if not task_data:
                return
        else:
            # コマンドライン引数から作成
            if not args.title:
                console.print("[red]タイトルが必要です。--title を指定するか --interactive を使用してください[/red]")
                return
            
            # 優先度のマッピング
            priority_map = {
                "urgent_important": TaskPriority.URGENT_IMPORTANT,
                "not_urgent_important": TaskPriority.NOT_URGENT_IMPORTANT,
                "urgent_not_important": TaskPriority.URGENT_NOT_IMPORTANT,
                "not_urgent_not_important": TaskPriority.NOT_URGENT_NOT_IMPORTANT
            }
            
            # エネルギーレベルのマッピング
            energy_map = {
                "high": EnergyLevel.HIGH,
                "medium": EnergyLevel.MEDIUM,
                "low": EnergyLevel.LOW
            }
            
            task_data = {
                "title": args.title,
                "description": args.description or "",
                "priority": args.priority,
                "energy_level": args.energy,
                "estimated_minutes": args.time,
                "tags": args.tags.split(",") if args.tags else [],
                "project": args.project,
                "due_date": datetime.strptime(args.due_date, "%Y-%m-%d") if args.due_date else None
            }
        
        # Taskオブジェクトを作成
        task = Task(
            title=task_data["title"],
            description=task_data["description"],
            priority=TaskPriority(task_data["priority"]),
            energy_required=EnergyLevel(task_data["energy_level"]),
            estimated_minutes=task_data["estimated_minutes"],
            tags=task_data["tags"],
            project=task_data["project"],
            due_date=task_data["due_date"],
            status=TaskStatus.INBOX
        )
        
        # 保存
        existing_tasks = manager.load_tasks_as_models()
        existing_tasks.append(task)
        manager.save_tasks_from_models(existing_tasks)
        
        console.print(f"[green]✅ タスクを作成しました: {task.title}[/green]")
        _display_task_details(task)
        
    except Exception as e:
        console.print(f"[red]❌ タスク作成に失敗しました: {str(e)}[/red]")


def list_tasks(args) -> None:
    """タスク一覧を表示"""
    if not PYDANTIC_AVAILABLE:
        console.print("[red]この機能にはPydanticモデルが必要です[/red]")
        return
    
    try:
        manager = TaskManager()
        tasks = manager.load_tasks_as_models()
        
        # フィルタリング
        if args.status:
            tasks = [task for task in tasks if task.status.value == args.status]
        
        if args.priority:
            tasks = [task for task in tasks if task.priority.value == args.priority]
        
        if args.project:
            tasks = [task for task in tasks if task.project == args.project]
        
        if args.tag:
            tasks = [task for task in tasks if args.tag in task.tags]
        
        # ソート
        if args.sort == "created":
            tasks.sort(key=lambda t: t.created_at, reverse=args.reverse)
        elif args.sort == "priority":
            priority_order = [TaskPriority.URGENT_IMPORTANT, TaskPriority.NOT_URGENT_IMPORTANT, 
                            TaskPriority.URGENT_NOT_IMPORTANT, TaskPriority.NOT_URGENT_NOT_IMPORTANT]
            tasks.sort(key=lambda t: priority_order.index(t.priority), reverse=args.reverse)
        elif args.sort == "due_date":
            tasks.sort(key=lambda t: t.due_date or datetime.max, reverse=args.reverse)
        
        # 制限
        if args.limit:
            tasks = tasks[:args.limit]
        
        if not tasks:
            console.print("[yellow]該当するタスクがありません[/yellow]")
            return
        
        # 表示形式
        if args.format == "table":
            _display_tasks_table(tasks, args.verbose)
        elif args.format == "json":
            _display_tasks_json(tasks)
        else:
            _display_tasks_list(tasks, args.verbose)
        
        console.print(f"\n[dim]表示件数: {len(tasks)}件[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ タスク一覧の取得に失敗しました: {str(e)}[/red]")


def update_task(args) -> None:
    """タスクを更新"""
    if not PYDANTIC_AVAILABLE:
        console.print("[red]この機能にはPydanticモデルが必要です[/red]")
        return
    
    try:
        manager = TaskManager()
        tasks = manager.load_tasks_as_models()
        
        # タスクを検索
        target_task = None
        task_index = None
        
        for i, task in enumerate(tasks):
            if task.id == args.id or args.id.lower() in task.title.lower():
                target_task = task
                task_index = i
                break
        
        if not target_task:
            console.print(f"[red]❌ タスクが見つかりません: {args.id}[/red]")
            return
        
        console.print(f"[blue]📝 タスクを更新します: {target_task.title}[/blue]")
        
        # 更新項目の収集
        updates = {}
        
        if args.title:
            updates["title"] = args.title
        
        if args.description is not None:
            updates["description"] = args.description
        
        if args.status:
            try:
                updates["status"] = TaskStatus(args.status)
                if args.status == "done" and not target_task.completed_at:
                    updates["completed_at"] = datetime.now()
                elif args.status != "done" and target_task.completed_at:
                    updates["completed_at"] = None
            except ValueError:
                console.print(f"[red]❌ 無効なステータス: {args.status}[/red]")
                return
        
        if args.priority:
            try:
                updates["priority"] = TaskPriority(args.priority)
            except ValueError:
                console.print(f"[red]❌ 無効な優先度: {args.priority}[/red]")
                return
        
        if args.energy:
            try:
                updates["energy_required"] = EnergyLevel(args.energy)
            except ValueError:
                console.print(f"[red]❌ 無効なエネルギーレベル: {args.energy}[/red]")
                return
        
        if args.time:
            updates["estimated_minutes"] = args.time
        
        if args.actual_time:
            updates["actual_minutes"] = args.actual_time
        
        if args.tags is not None:
            updates["tags"] = args.tags.split(",") if args.tags else []
        
        if args.project is not None:
            updates["project"] = args.project if args.project else None
        
        if args.due_date is not None:
            if args.due_date:
                try:
                    updates["due_date"] = datetime.strptime(args.due_date, "%Y-%m-%d")
                except ValueError:
                    console.print(f"[red]❌ 無効な日付形式: {args.due_date}[/red]")
                    return
            else:
                updates["due_date"] = None
        
        if not updates:
            console.print("[yellow]更新する項目がありません[/yellow]")
            return
        
        # 更新の適用
        updates["updated_at"] = datetime.now()
        
        for key, value in updates.items():
            setattr(target_task, key, value)
        
        # 保存
        manager.save_tasks_from_models(tasks)
        
        console.print(f"[green]✅ タスクを更新しました[/green]")
        _display_task_details(target_task)
        
    except Exception as e:
        console.print(f"[red]❌ タスク更新に失敗しました: {str(e)}[/red]")


def delete_task(args) -> None:
    """タスクを削除"""
    if not PYDANTIC_AVAILABLE:
        console.print("[red]この機能にはPydanticモデルが必要です[/red]")
        return
    
    try:
        manager = TaskManager()
        tasks = manager.load_tasks_as_models()
        
        # タスクを検索
        target_task = None
        task_index = None
        
        for i, task in enumerate(tasks):
            if task.id == args.id or args.id.lower() in task.title.lower():
                target_task = task
                task_index = i
                break
        
        if not target_task:
            console.print(f"[red]❌ タスクが見つかりません: {args.id}[/red]")
            return
        
        # 確認
        if not args.force:
            console.print(f"[yellow]削除対象のタスク:[/yellow]")
            _display_task_details(target_task)
            
            if not Confirm.ask("このタスクを削除しますか？"):
                console.print("[blue]削除をキャンセルしました[/blue]")
                return
        
        # 削除
        tasks.pop(task_index)
        manager.save_tasks_from_models(tasks)
        
        console.print(f"[green]✅ タスクを削除しました: {target_task.title}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ タスク削除に失敗しました: {str(e)}[/red]")


def show_task(args) -> None:
    """タスク詳細を表示"""
    if not PYDANTIC_AVAILABLE:
        console.print("[red]この機能にはPydanticモデルが必要です[/red]")
        return
    
    try:
        manager = TaskManager()
        tasks = manager.load_tasks_as_models()
        
        # タスクを検索
        target_task = None
        
        for task in tasks:
            if task.id == args.id or args.id.lower() in task.title.lower():
                target_task = task
                break
        
        if not target_task:
            console.print(f"[red]❌ タスクが見つかりません: {args.id}[/red]")
            return
        
        _display_task_details(target_task, full=True)
        
    except Exception as e:
        console.print(f"[red]❌ タスク詳細の取得に失敗しました: {str(e)}[/red]")


def _display_tasks_table(tasks: List[Task], verbose: bool = False) -> None:
    """タスクをテーブル形式で表示"""
    table = Table(show_header=True, header_style="bold magenta")
    
    table.add_column("ID", width=8)
    table.add_column("ステータス", width=10)
    table.add_column("優先度", width=12)
    table.add_column("タイトル", min_width=20)
    table.add_column("エネルギー", width=10)
    table.add_column("時間", width=8)
    
    if verbose:
        table.add_column("プロジェクト", width=12)
        table.add_column("期限", width=10)
        table.add_column("タグ", width=15)
    
    for task in tasks:
        status_icon = _get_status_display(task.status)
        priority_icon = _get_priority_display(task.priority)
        energy_icon = _get_energy_display(task.energy_required)
        
        row = [
            task.id[:8] + "...",
            status_icon,
            priority_icon,
            task.title[:30] + "..." if len(task.title) > 30 else task.title,
            energy_icon,
            f"{task.estimated_minutes}分"
        ]
        
        if verbose:
            row.extend([
                task.project or "-",
                task.due_date.strftime("%m/%d") if task.due_date else "-",
                ",".join(task.tags[:2]) + ("..." if len(task.tags) > 2 else "") if task.tags else "-"
            ])
        
        table.add_row(*row)
    
    console.print(table)


def _display_tasks_list(tasks: List[Task], verbose: bool = False) -> None:
    """タスクをリスト形式で表示"""
    for i, task in enumerate(tasks, 1):
        status_icon = _get_status_display(task.status)
        priority_icon = _get_priority_display(task.priority)
        energy_icon = _get_energy_display(task.energy_required)
        
        title_line = f"{i}. {status_icon} {priority_icon} {energy_icon} {task.title}"
        
        if task.due_date:
            title_line += f" 📅{task.due_date.strftime('%m/%d')}"
        
        if task.project:
            title_line += f" 📁{task.project}"
        
        console.print(title_line)
        
        if verbose and task.description:
            console.print(f"   📄 {task.description}")
        
        if verbose and task.tags:
            console.print(f"   🏷️  {', '.join(task.tags)}")
        
        if verbose:
            console.print(f"   🆔 {task.id}")
        
        console.print()


def _display_tasks_json(tasks: List[Task]) -> None:
    """タスクをJSON形式で表示"""
    tasks_data = []
    for task in tasks:
        task_dict = task.model_dump()
        # datetimeを文字列に変換
        for key, value in task_dict.items():
            if isinstance(value, datetime):
                task_dict[key] = value.isoformat()
        tasks_data.append(task_dict)
    
    console.print(json.dumps(tasks_data, ensure_ascii=False, indent=2))


def _display_task_details(task: Task, full: bool = False) -> None:
    """タスクの詳細情報を表示"""
    status_display = _get_status_display(task.status)
    priority_display = _get_priority_display(task.priority)
    energy_display = _get_energy_display(task.energy_required)
    
    content = f"""
[bold]{task.title}[/bold]

{status_display} {priority_display} {energy_display}

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
📅 作成日時: {task.created_at.strftime('%Y-%m-%d %H:%M')}
📝 更新日時: {task.updated_at.strftime('%Y-%m-%d %H:%M')}
"""
        
        if task.completed_at:
            content += f"✅ 完了日時: {task.completed_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        if task.progress_log:
            content += "\n📊 進捗ログ:\n"
            for log in task.progress_log[-3:]:  # 最新3件
                content += f"   • {log.get('timestamp', '')}: {log.get('update', '')}\n"
    
    panel = Panel(content.strip(), title="📝 タスク詳細", border_style="blue")
    console.print(panel)


def _get_status_display(status: TaskStatus) -> str:
    """ステータス表示を取得"""
    icons = {
        TaskStatus.INBOX: "📥 受信箱",
        TaskStatus.NEXT: "⏭️  次のアクション",
        TaskStatus.IN_PROGRESS: "🔄 実行中",
        TaskStatus.BLOCKED: "🚫 ブロック中",
        TaskStatus.DONE: "✅ 完了",
        TaskStatus.ARCHIVED: "📦 アーカイブ"
    }
    return icons.get(status, "❓ 不明")


def _get_priority_display(priority: TaskPriority) -> str:
    """優先度表示を取得"""
    icons = {
        TaskPriority.URGENT_IMPORTANT: "🔴 緊急・重要",
        TaskPriority.NOT_URGENT_IMPORTANT: "🟡 重要・非緊急",
        TaskPriority.URGENT_NOT_IMPORTANT: "🟠 緊急・非重要",
        TaskPriority.NOT_URGENT_NOT_IMPORTANT: "🟢 非緊急・非重要"
    }
    return icons.get(priority, "❓ 不明")


def _get_energy_display(energy: EnergyLevel) -> str:
    """エネルギーレベル表示を取得"""
    icons = {
        EnergyLevel.HIGH: "⚡ 高エネルギー",
        EnergyLevel.MEDIUM: "🔋 中エネルギー",
        EnergyLevel.LOW: "🪫 低エネルギー"
    }
    return icons.get(energy, "❓ 不明")


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(description="タスク管理CRUD操作")
    subparsers = parser.add_subparsers(dest="command", help="利用可能なコマンド")
    
    # create コマンド
    create_parser = subparsers.add_parser("create", help="新しいタスクを作成")
    create_parser.add_argument("--title", "-t", help="タスクのタイトル")
    create_parser.add_argument("--description", "-d", help="タスクの説明")
    create_parser.add_argument("--priority", "-p", 
                             choices=["urgent_important", "not_urgent_important", "urgent_not_important", "not_urgent_not_important"],
                             default="not_urgent_important", help="優先度")
    create_parser.add_argument("--energy", "-e", choices=["high", "medium", "low"], default="medium", help="必要エネルギーレベル")
    create_parser.add_argument("--time", type=int, default=30, help="推定時間（分）")
    create_parser.add_argument("--tags", help="タグ（カンマ区切り）")
    create_parser.add_argument("--project", help="プロジェクト名")
    create_parser.add_argument("--due-date", help="期限（YYYY-MM-DD形式）")
    create_parser.add_argument("--interactive", "-i", action="store_true", help="対話的にタスクを作成")
    
    # list コマンド
    list_parser = subparsers.add_parser("list", help="タスク一覧を表示")
    list_parser.add_argument("--status", "-s", 
                           choices=["inbox", "next", "in_progress", "blocked", "done", "archived"],
                           help="ステータスでフィルタ")
    list_parser.add_argument("--priority", "-p",
                           choices=["urgent_important", "not_urgent_important", "urgent_not_important", "not_urgent_not_important"],
                           help="優先度でフィルタ")
    list_parser.add_argument("--project", help="プロジェクトでフィルタ")
    list_parser.add_argument("--tag", help="タグでフィルタ")
    list_parser.add_argument("--sort", choices=["created", "priority", "due_date"], default="created", help="ソート基準")
    list_parser.add_argument("--reverse", "-r", action="store_true", help="逆順ソート")
    list_parser.add_argument("--limit", "-l", type=int, help="表示件数制限")
    list_parser.add_argument("--format", "-f", choices=["list", "table", "json"], default="list", help="表示形式")
    list_parser.add_argument("--verbose", "-v", action="store_true", help="詳細表示")
    
    # update コマンド
    update_parser = subparsers.add_parser("update", help="タスクを更新")
    update_parser.add_argument("id", help="タスクIDまたはタイトルの一部")
    update_parser.add_argument("--title", "-t", help="新しいタイトル")
    update_parser.add_argument("--description", "-d", help="新しい説明")
    update_parser.add_argument("--status", "-s",
                             choices=["inbox", "next", "in_progress", "blocked", "done", "archived"],
                             help="新しいステータス")
    update_parser.add_argument("--priority", "-p",
                             choices=["urgent_important", "not_urgent_important", "urgent_not_important", "not_urgent_not_important"],
                             help="新しい優先度")
    update_parser.add_argument("--energy", "-e", choices=["high", "medium", "low"], help="新しいエネルギーレベル")
    update_parser.add_argument("--time", type=int, help="新しい推定時間（分）")
    update_parser.add_argument("--actual-time", type=int, help="実際の時間（分）")
    update_parser.add_argument("--tags", help="新しいタグ（カンマ区切り）")
    update_parser.add_argument("--project", help="新しいプロジェクト名")
    update_parser.add_argument("--due-date", help="新しい期限（YYYY-MM-DD形式、空文字で削除）")
    
    # delete コマンド
    delete_parser = subparsers.add_parser("delete", help="タスクを削除")
    delete_parser.add_argument("id", help="タスクIDまたはタイトルの一部")
    delete_parser.add_argument("--force", "-f", action="store_true", help="確認なしで削除")
    
    # show コマンド
    show_parser = subparsers.add_parser("show", help="タスク詳細を表示")
    show_parser.add_argument("id", help="タスクIDまたはタイトルの一部")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # コマンドの実行
    if args.command == "create":
        create_task(args)
    elif args.command == "list":
        list_tasks(args)
    elif args.command == "update":
        update_task(args)
    elif args.command == "delete":
        delete_task(args)
    elif args.command == "show":
        show_task(args)


if __name__ == "__main__":
    main()