import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
from agents import function_tool

# Pydanticモデルをインポート
try:
    from ..models import Task, TaskPriority, TaskStatus, EnergyLevel, convert_legacy_task
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

class TaskManager:
    def __init__(self, store_path: str = None):
        if store_path is None:
            # デフォルトのメモリ保存場所を設定
            import os
            home_dir = os.path.expanduser("~")
            ktra_dir = os.path.join(home_dir, ".ktra")
            os.makedirs(ktra_dir, exist_ok=True)
            self.store_path = os.path.join(ktra_dir, "store.json")
        else:
            self.store_path = store_path
        self._ensure_store_exists()
    
    def _ensure_store_exists(self):
        if not os.path.exists(self.store_path):
            os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
            with open(self.store_path, 'w', encoding='utf-8') as f:
                json.dump({"tasks": []}, f, ensure_ascii=False, indent=2)
    
    def _load_tasks(self) -> List[Dict[str, Any]]:
        with open(self.store_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("tasks", [])
    
    def _save_tasks(self, tasks: List[Dict[str, Any]]):
        with open(self.store_path, 'w', encoding='utf-8') as f:
            json.dump({"tasks": tasks}, f, ensure_ascii=False, indent=2)
    
    def load_tasks_as_models(self) -> List['Task']:
        """タスクをPydanticモデルとして読み込み（後方互換性あり）"""
        if not PYDANTIC_AVAILABLE:
            return []
        
        legacy_tasks = self._load_tasks()
        tasks = []
        
        for legacy_task in legacy_tasks:
            try:
                # 新形式の場合はそのままTask作成、旧形式は変換
                if 'energy_required' in legacy_task:
                    tasks.append(Task(**legacy_task))
                else:
                    tasks.append(convert_legacy_task(legacy_task))
            except Exception:
                # 変換に失敗した場合はスキップ
                continue
        
        return tasks
    
    def save_tasks_from_models(self, tasks: List['Task']):
        """PydanticモデルからJSONに保存"""
        if not PYDANTIC_AVAILABLE:
            return
        
        task_dicts = [task.model_dump() for task in tasks]
        # datetimeを文字列に変換
        for task_dict in task_dicts:
            for key, value in task_dict.items():
                if isinstance(value, datetime):
                    task_dict[key] = value.isoformat()
        
        self._save_tasks(task_dicts)

def _add_task(title: str, description: str = "", deadline: Optional[str] = None, priority: str = "medium") -> str:
    """
    新しいタスクを追加します。
    
    Args:
        title: タスクのタイトル
        description: タスクの説明（オプション）
        deadline: 期限（例：「明日」「2024-01-15」）
        priority: 優先度（low, medium, high）
    
    Returns:
        タスクが正常に追加されたことを示すメッセージ
    """
    manager = TaskManager()
    
    if PYDANTIC_AVAILABLE:
        # 新しいPydanticモデルを使用
        try:
            # 優先度のマッピング
            priority_mapping = {
                'low': TaskPriority.NOT_URGENT_NOT_IMPORTANT,
                'medium': TaskPriority.NOT_URGENT_IMPORTANT,
                'high': TaskPriority.URGENT_IMPORTANT
            }
            
            # 期限の解析
            due_date = None
            if deadline:
                try:
                    # 簡単な日付解析（今後改善可能）
                    if deadline.lower() == "明日":
                        due_date = datetime.now().replace(hour=23, minute=59, second=59)
                        due_date = due_date.replace(day=due_date.day + 1)
                    else:
                        due_date = datetime.fromisoformat(deadline)
                except:
                    pass  # 解析に失敗した場合はNone
            
            task = Task(
                title=title,
                description=description or "",
                priority=priority_mapping.get(priority, TaskPriority.NOT_URGENT_IMPORTANT),
                due_date=due_date,
                status=TaskStatus.INBOX
            )
            
            existing_tasks = manager.load_tasks_as_models()
            existing_tasks.append(task)
            manager.save_tasks_from_models(existing_tasks)
            
            return f"✅ タスクを登録しました：「{title}」（優先度：{priority}、エネルギー：{task.energy_required.value}）"
            
        except Exception as e:
            # Pydanticモデル使用に失敗した場合、従来方式にフォールバック
            pass
    
    # 従来方式（後方互換性）
    tasks = manager._load_tasks()
    
    task = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "deadline": deadline,
        "priority": priority,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    tasks.append(task)
    manager._save_tasks(tasks)
    
    return f"✅ タスクを登録しました：「{title}」（優先度：{priority}）"

add_task = function_tool(_add_task)

def _list_tasks(status: Optional[str] = None, priority: Optional[str] = None) -> str:
    """
    タスク一覧を表示します。
    
    Args:
        status: フィルタリング用ステータス（pending, completed）
        priority: フィルタリング用優先度（low, medium, high）
    
    Returns:
        タスク一覧の文字列
    """
    manager = TaskManager()
    tasks = manager._load_tasks()
    
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    if priority:
        tasks = [t for t in tasks if t.get("priority") == priority]
    
    if not tasks:
        return "📝 該当するタスクはありません。"
    
    # 優先度順でソート
    priority_order = {"high": 0, "medium": 1, "low": 2}
    tasks.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 1))
    
    result = "📝 タスク一覧:\n"
    for i, task in enumerate(tasks, 1):
        status_icon = "✅" if task.get("status") == "completed" else "⏳"
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.get("priority", "medium"), "🟡")
        deadline_text = f"（期限：{task.get('deadline')}）" if task.get("deadline") else ""
        
        result += f"{i}. {status_icon} {priority_icon} {task['title']} {deadline_text}\n"
        if task.get("description"):
            result += f"   📄 {task['description']}\n"
    
    return result

list_tasks = function_tool(_list_tasks)

def _update_task(task_identifier: str, status: Optional[str] = None, title: Optional[str] = None, 
                description: Optional[str] = None, deadline: Optional[str] = None, 
                priority: Optional[str] = None) -> str:
    """
    タスクを更新します。
    
    Args:
        task_identifier: タスクのIDまたはタイトルの一部
        status: 新しいステータス（pending, completed）
        title: 新しいタイトル
        description: 新しい説明
        deadline: 新しい期限
        priority: 新しい優先度
    
    Returns:
        更新結果のメッセージ
    """
    manager = TaskManager()
    tasks = manager._load_tasks()
    
    # タスクを検索
    found_task = None
    for task in tasks:
        if (task["id"] == task_identifier or 
            task_identifier.lower() in task["title"].lower()):
            found_task = task
            break
    
    if not found_task:
        return f"❌ タスク「{task_identifier}」が見つかりませんでした。"
    
    # タスクを更新
    if status:
        found_task["status"] = status
    if title:
        found_task["title"] = title
    if description:
        found_task["description"] = description
    if deadline:
        found_task["deadline"] = deadline
    if priority:
        found_task["priority"] = priority
    
    found_task["updated_at"] = datetime.now().isoformat()
    
    manager._save_tasks(tasks)
    
    status_text = f"（ステータス：{status}）" if status else ""
    return f"✅ タスク「{found_task['title']}」を更新しました {status_text}"

update_task = function_tool(_update_task)


# 高度なタスク検索機能
def _search_tasks(
    query: str = "",
    status: Optional[str] = None,
    priority: Optional[str] = None,
    project: Optional[str] = None,
    tags: Optional[str] = None,
    energy_level: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    高度なタスク検索機能
    
    Args:
        query: タイトルや説明での検索キーワード
        status: ステータスフィルター (inbox, next, in_progress, blocked, done, archived)
        priority: 優先度フィルター (urgent_important, not_urgent_important, etc.)
        project: プロジェクトフィルター
        tags: タグでのフィルター（カンマ区切り）
        energy_level: 必要エネルギーレベル (high, medium, low)
        limit: 最大表示件数
    
    Returns:
        検索結果の文字列
    """
    manager = TaskManager()
    
    if PYDANTIC_AVAILABLE:
        try:
            tasks = manager.load_tasks_as_models()
            
            # フィルタリング
            filtered_tasks = []
            for task in tasks:
                # クエリ検索
                if query:
                    query_lower = query.lower()
                    if (query_lower not in task.title.lower() and 
                        query_lower not in (task.description or "").lower()):
                        continue
                
                # ステータスフィルター
                if status and task.status.value != status:
                    continue
                
                # 優先度フィルター
                if priority and task.priority.value != priority:
                    continue
                
                # プロジェクトフィルター
                if project and task.project != project:
                    continue
                
                # タグフィルター
                if tags:
                    search_tags = [tag.strip() for tag in tags.split(",")]
                    if not any(tag in task.tags for tag in search_tags):
                        continue
                
                # エネルギーレベルフィルター
                if energy_level and task.energy_required.value != energy_level:
                    continue
                
                filtered_tasks.append(task)
            
            # 結果の制限
            filtered_tasks = filtered_tasks[:limit]
            
            if not filtered_tasks:
                return "🔍 検索条件に一致するタスクが見つかりませんでした。"
            
            # 結果の表示
            result = f"🔍 検索結果 ({len(filtered_tasks)}件):\n"
            
            for i, task in enumerate(filtered_tasks, 1):
                status_icon = _get_status_icon(task.status.value)
                priority_icon = _get_priority_icon(task.priority.value)
                energy_icon = _get_energy_icon(task.energy_required.value)
                
                result += f"{i}. {status_icon} {priority_icon} {energy_icon} {task.title}"
                
                if task.due_date:
                    result += f" 📅{task.due_date.strftime('%m/%d')}"
                
                if task.project:
                    result += f" 📁{task.project}"
                
                if task.tags:
                    result += f" 🏷️{','.join(task.tags[:3])}"
                
                result += "\n"
                
                if task.description:
                    result += f"   📄 {task.description[:100]}{'...' if len(task.description) > 100 else ''}\n"
            
            return result
            
        except Exception as e:
            # エラー時は従来方式にフォールバック
            pass
    
    # 従来方式のフォールバック
    return _list_tasks(status, priority)


def _get_status_icon(status: str) -> str:
    """ステータスアイコンを取得"""
    icons = {
        "inbox": "📥",
        "next": "⏭️",
        "in_progress": "🔄",
        "blocked": "🚫",
        "done": "✅",
        "archived": "📦",
        "pending": "⏳",
        "completed": "✅"
    }
    return icons.get(status, "⏳")


def _get_priority_icon(priority: str) -> str:
    """優先度アイコンを取得"""
    icons = {
        "urgent_important": "🔴",
        "not_urgent_important": "🟡",
        "urgent_not_important": "🟠",
        "not_urgent_not_important": "🟢",
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢"
    }
    return icons.get(priority, "🟡")


def _get_energy_icon(energy: str) -> str:
    """エネルギーレベルアイコンを取得"""
    icons = {
        "high": "⚡",
        "medium": "🔋",
        "low": "🪫"
    }
    return icons.get(energy, "🔋")


search_tasks = function_tool(_search_tasks)


# タスク推奨機能
def _recommend_next_task(
    current_energy: str = "medium",
    available_minutes: int = 60,
    context: str = "general"
) -> str:
    """
    現在の状況に基づいてタスクを推奨
    
    Args:
        current_energy: 現在のエネルギーレベル (high, medium, low)
        available_minutes: 利用可能時間（分）
        context: 作業コンテキスト (work, home, mobile)
    
    Returns:
        推奨タスクの情報
    """
    manager = TaskManager()
    
    if PYDANTIC_AVAILABLE:
        try:
            tasks = manager.load_tasks_as_models()
            
            # アクティブなタスクをフィルタリング
            active_tasks = [
                task for task in tasks 
                if task.status in [TaskStatus.INBOX, TaskStatus.NEXT]
            ]
            
            if not active_tasks:
                return "🎉 お疲れ様です！現在、実行可能なタスクがありません。"
            
            # スコアリングシステム
            scored_tasks = []
            
            for task in active_tasks:
                score = 0
                
                # エネルギーレベルマッチング
                energy_match = {
                    "high": {"high": 3, "medium": 1, "low": 0},
                    "medium": {"high": 1, "medium": 3, "low": 2},
                    "low": {"high": 0, "medium": 1, "low": 3}
                }
                score += energy_match.get(current_energy, {}).get(task.energy_required.value, 1)
                
                # 時間マッチング
                if task.estimated_minutes <= available_minutes:
                    score += 3
                elif task.estimated_minutes <= available_minutes * 1.2:
                    score += 1
                
                # 優先度
                priority_scores = {
                    TaskPriority.URGENT_IMPORTANT: 5,
                    TaskPriority.NOT_URGENT_IMPORTANT: 3,
                    TaskPriority.URGENT_NOT_IMPORTANT: 2,
                    TaskPriority.NOT_URGENT_NOT_IMPORTANT: 1
                }
                score += priority_scores.get(task.priority, 1)
                
                # 期限の近さ
                if task.due_date:
                    days_until_due = (task.due_date - datetime.now()).days
                    if days_until_due <= 1:
                        score += 3
                    elif days_until_due <= 3:
                        score += 2
                    elif days_until_due <= 7:
                        score += 1
                
                scored_tasks.append((score, task))
            
            # スコア順でソート
            scored_tasks.sort(key=lambda x: x[0], reverse=True)
            
            # トップ3を推奨
            result = f"💡 現在の状況（⚡{current_energy}, ⏰{available_minutes}分）に基づく推奨タスク:\n\n"
            
            for i, (score, task) in enumerate(scored_tasks[:3], 1):
                status_icon = _get_status_icon(task.status.value)
                priority_icon = _get_priority_icon(task.priority.value)
                energy_icon = _get_energy_icon(task.energy_required.value)
                
                result += f"{i}. {priority_icon} {energy_icon} {task.title}"
                result += f" (推奨度: {score}点, 推定時間: {task.estimated_minutes}分)\n"
                
                if task.description:
                    result += f"   📄 {task.description[:80]}{'...' if len(task.description) > 80 else ''}\n"
                
                result += "\n"
            
            return result
            
        except Exception as e:
            pass
    
    # フォールバック
    return "📝 利用可能なタスクを確認するには、タスク一覧を表示してください。"


recommend_next_task = function_tool(_recommend_next_task)