import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
from agents import function_tool

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