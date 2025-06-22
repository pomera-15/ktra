"""
プロジェクト管理ツール
プロジェクトの作成、管理、フォルダ操作、AI参照機能
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from agents import function_tool

from ..models import Project, ProjectStatus, Task
from .task import TaskManager


class ProjectManager:
    """プロジェクト管理クラス"""
    
    def __init__(self):
        self.project_dir = Path("memory/projects")
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.store_file = self.project_dir / "projects.json"
        self.project_folders_dir = Path("project_files")
        self.project_folders_dir.mkdir(parents=True, exist_ok=True)
    
    def load_projects(self) -> List[Dict[str, Any]]:
        """プロジェクトデータを読み込み"""
        if not self.store_file.exists():
            return []
        
        try:
            with open(self.store_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def save_projects(self, projects: List[Dict[str, Any]]) -> None:
        """プロジェクトデータを保存"""
        with open(self.store_file, 'w', encoding='utf-8') as f:
            json.dump(projects, f, ensure_ascii=False, indent=2, default=str)
    
    def load_projects_as_models(self) -> List[Project]:
        """プロジェクトをPydanticモデルとして読み込み"""
        projects_data = self.load_projects()
        projects = []
        
        for data in projects_data:
            try:
                project = Project(**data)
                projects.append(project)
            except:
                # 古い形式のデータは無視
                pass
        
        return projects
    
    def save_projects_from_models(self, projects: List[Project]) -> None:
        """Pydanticモデルからプロジェクトを保存"""
        projects_data = [project.model_dump() for project in projects]
        self.save_projects(projects_data)
    
    def create_project_folder(self, project: Project) -> str:
        """プロジェクトフォルダを作成"""
        folder_name = project.get_folder_name()
        folder_path = self.project_folders_dir / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # 基本的なフォルダ構造を作成
        (folder_path / "notes").mkdir(exist_ok=True)
        (folder_path / "documents").mkdir(exist_ok=True)
        (folder_path / "references").mkdir(exist_ok=True)
        
        # README.mdを作成
        readme_content = f"""# {project.name}

## 概要
{project.description or 'プロジェクトの説明を記載してください。'}

## フォルダ構成
- `notes/` - プロジェクトに関するメモ
- `documents/` - ドキュメントや資料
- `references/` - 参考資料やリンク

## プロジェクト情報
- ID: {project.id}
- 作成日: {project.created_at.strftime('%Y-%m-%d')}
- ステータス: {project.status.value}
"""
        
        with open(folder_path / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        return str(folder_path)
    
    def get_project_files(self, project_id: str) -> List[Dict[str, str]]:
        """プロジェクトのファイル一覧を取得"""
        projects = self.load_projects_as_models()
        project = next((p for p in projects if p.id == project_id), None)
        
        if not project or not project.folder_path:
            return []
        
        folder_path = Path(project.folder_path)
        if not folder_path.exists():
            return []
        
        files = []
        for root, dirs, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = Path(root) / filename
                relative_path = file_path.relative_to(folder_path)
                files.append({
                    'path': str(file_path),
                    'relative_path': str(relative_path),
                    'name': filename,
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return files
    
    def read_project_file(self, project_id: str, relative_path: str) -> Optional[str]:
        """プロジェクトファイルを読み込み"""
        projects = self.load_projects_as_models()
        project = next((p for p in projects if p.id == project_id), None)
        
        if not project or not project.folder_path:
            return None
        
        file_path = Path(project.folder_path) / relative_path
        if not file_path.exists() or not file_path.is_file():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return None


# AI用のツール関数

def _create_project(name: str, description: str = "", due_date: str = "", tags: str = "") -> str:
    """新しいプロジェクトを作成"""
    manager = ProjectManager()
    
    # 既存のプロジェクトを確認
    projects = manager.load_projects_as_models()
    if any(p.name.lower() == name.lower() for p in projects):
        return f"❌ プロジェクト「{name}」は既に存在します"
    
    # プロジェクトを作成
    project = Project(
        name=name,
        description=description if description else None,
        status=ProjectStatus.ACTIVE,
        tags=[tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
    )
    
    # 期限の設定
    if due_date:
        try:
            from dateutil import parser
            project.due_date = parser.parse(due_date)
        except:
            pass
    
    # フォルダを作成
    folder_path = manager.create_project_folder(project)
    project.folder_path = folder_path
    
    # プロジェクトを保存
    projects.append(project)
    manager.save_projects_from_models(projects)
    
    return f"✅ プロジェクト「{name}」を作成しました\n📁 フォルダ: {folder_path}"


def _list_projects(status_filter: str = "") -> str:
    """プロジェクト一覧を表示"""
    manager = ProjectManager()
    projects = manager.load_projects_as_models()
    
    if not projects:
        return "📝 プロジェクトがありません"
    
    # ステータスでフィルタリング
    if status_filter:
        try:
            status = ProjectStatus(status_filter.lower())
            projects = [p for p in projects if p.status == status]
        except:
            pass
    
    # プロジェクトごとのタスク数を取得
    task_manager = TaskManager()
    tasks = task_manager.load_tasks_as_models()
    
    result = []
    for project in projects:
        task_count = len([t for t in tasks if t.project == project.name])
        status_emoji = {
            ProjectStatus.PLANNING: "📋",
            ProjectStatus.ACTIVE: "🚀",
            ProjectStatus.ON_HOLD: "⏸️",
            ProjectStatus.COMPLETED: "✅",
            ProjectStatus.ARCHIVED: "📦"
        }.get(project.status, "❓")
        
        result.append(f"{status_emoji} **{project.name}** ({task_count}タスク)")
        if project.description:
            result.append(f"   {project.description}")
        if project.due_date:
            result.append(f"   📅 期限: {project.due_date.strftime('%Y-%m-%d')}")
        if project.tags:
            result.append(f"   🏷️ {', '.join(project.tags)}")
    
    return "\n".join(result)


def _get_project_details(project_name: str) -> str:
    """プロジェクトの詳細情報を取得"""
    manager = ProjectManager()
    projects = manager.load_projects_as_models()
    
    # プロジェクトを検索
    project = next((p for p in projects if p.name.lower() == project_name.lower()), None)
    if not project:
        return f"❌ プロジェクト「{project_name}」が見つかりません"
    
    # タスク情報を取得
    task_manager = TaskManager()
    tasks = task_manager.load_tasks_as_models()
    project_tasks = [t for t in tasks if t.project == project.name]
    
    # ファイル情報を取得
    files = manager.get_project_files(project.id)
    
    result = [
        f"# {project.name}",
        f"",
        f"## 基本情報",
        f"- ステータス: {project.status.value}",
        f"- 作成日: {project.created_at.strftime('%Y-%m-%d')}",
        f"- 更新日: {project.updated_at.strftime('%Y-%m-%d')}",
    ]
    
    if project.description:
        result.append(f"- 説明: {project.description}")
    
    if project.due_date:
        result.append(f"- 期限: {project.due_date.strftime('%Y-%m-%d')}")
    
    if project.tags:
        result.append(f"- タグ: {', '.join(project.tags)}")
    
    result.append(f"")
    result.append(f"## タスク ({len(project_tasks)}件)")
    
    if project_tasks:
        for task in project_tasks[:10]:  # 最大10件表示
            status_icon = {
                "inbox": "📥",
                "next": "⏭️",
                "in_progress": "🔄",
                "blocked": "🚫",
                "done": "✅",
                "archived": "📦"
            }.get(task.status.value, "❓")
            result.append(f"- {status_icon} {task.title}")
    
    result.append(f"")
    result.append(f"## ファイル ({len(files)}件)")
    
    if files:
        for file in files[:10]:  # 最大10件表示
            result.append(f"- {file['relative_path']} ({file['size']} bytes)")
    
    if project.folder_path:
        result.append(f"")
        result.append(f"📁 フォルダ: {project.folder_path}")
    
    return "\n".join(result)


def _update_project_status(project_name: str, status: str) -> str:
    """プロジェクトのステータスを更新"""
    manager = ProjectManager()
    projects = manager.load_projects_as_models()
    
    # プロジェクトを検索
    project = next((p for p in projects if p.name.lower() == project_name.lower()), None)
    if not project:
        return f"❌ プロジェクト「{project_name}」が見つかりません"
    
    # ステータスを更新
    try:
        new_status = ProjectStatus(status.lower())
        project.status = new_status
        project.updated_at = datetime.now()
        
        manager.save_projects_from_models(projects)
        
        return f"✅ プロジェクト「{project_name}」のステータスを「{new_status.value}」に更新しました"
    except:
        return f"❌ 無効なステータス: {status}\n使用可能: planning, active, on_hold, completed, archived"


def _add_task_to_project(task_title: str, project_name: str) -> str:
    """タスクをプロジェクトに追加"""
    # プロジェクトの確認
    manager = ProjectManager()
    projects = manager.load_projects_as_models()
    project = next((p for p in projects if p.name.lower() == project_name.lower()), None)
    
    if not project:
        return f"❌ プロジェクト「{project_name}」が見つかりません"
    
    # タスクの確認と更新
    task_manager = TaskManager()
    tasks = task_manager.load_tasks_as_models()
    
    task = None
    for t in tasks:
        if task_title.lower() in t.title.lower():
            task = t
            break
    
    if not task:
        return f"❌ タスク「{task_title}」が見つかりません"
    
    # タスクのプロジェクトを更新
    task.project = project.name
    task_manager.save_tasks_from_models(tasks)
    
    # プロジェクトのタスクIDリストを更新
    if task.id not in project.task_ids:
        project.task_ids.append(task.id)
        project.updated_at = datetime.now()
        manager.save_projects_from_models(projects)
    
    return f"✅ タスク「{task.title}」をプロジェクト「{project.name}」に追加しました"


def _read_project_file(project_name: str, file_path: str) -> str:
    """プロジェクトのファイルを読み込み"""
    manager = ProjectManager()
    projects = manager.load_projects_as_models()
    
    # プロジェクトを検索
    project = next((p for p in projects if p.name.lower() == project_name.lower()), None)
    if not project:
        return f"❌ プロジェクト「{project_name}」が見つかりません"
    
    # ファイルを読み込み
    content = manager.read_project_file(project.id, file_path)
    if content is None:
        return f"❌ ファイル「{file_path}」が見つかりません"
    
    return f"📄 {file_path}\n\n{content}"


def _create_project_note(project_name: str, note_title: str, content: str) -> str:
    """プロジェクトにメモを作成"""
    manager = ProjectManager()
    projects = manager.load_projects_as_models()
    
    # プロジェクトを検索
    project = next((p for p in projects if p.name.lower() == project_name.lower()), None)
    if not project or not project.folder_path:
        return f"❌ プロジェクト「{project_name}」が見つかりません"
    
    # ファイル名をサニタイズ
    import re
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', note_title)
    note_path = Path(project.folder_path) / "notes" / f"{safe_filename}.md"
    
    # メモを作成
    note_content = f"""# {note_title}

作成日: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

{content}
"""
    
    try:
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(note_content)
        
        return f"✅ メモ「{note_title}」を作成しました\n📄 {note_path.relative_to(Path(project.folder_path))}"
    except Exception as e:
        return f"❌ メモの作成に失敗しました: {str(e)}"


def _search_project_files(project_name: str, keyword: str) -> str:
    """プロジェクト内のファイルを検索"""
    manager = ProjectManager()
    projects = manager.load_projects_as_models()
    
    # プロジェクトを検索
    project = next((p for p in projects if p.name.lower() == project_name.lower()), None)
    if not project or not project.folder_path:
        return f"❌ プロジェクト「{project_name}」が見つかりません"
    
    folder_path = Path(project.folder_path)
    if not folder_path.exists():
        return f"❌ プロジェクトフォルダが見つかりません"
    
    results = []
    keyword_lower = keyword.lower()
    
    # ファイル内容を検索
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith(('.md', '.txt', '.json')):
                file_path = Path(root) / filename
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if keyword_lower in content.lower():
                            # マッチした行を取得
                            lines = content.split('\n')
                            matched_lines = []
                            for i, line in enumerate(lines):
                                if keyword_lower in line.lower():
                                    matched_lines.append(f"  L{i+1}: {line.strip()}")
                            
                            relative_path = file_path.relative_to(folder_path)
                            results.append(f"📄 {relative_path}")
                            results.extend(matched_lines[:3])  # 最大3行表示
                            if len(matched_lines) > 3:
                                results.append(f"  ... 他 {len(matched_lines)-3} 件")
                            results.append("")
                except:
                    pass
    
    if not results:
        return f"❌ 「{keyword}」を含むファイルが見つかりません"
    
    return f"🔍 検索結果: 「{keyword}」\n\n" + "\n".join(results)


# AIツールとして登録
create_project = function_tool(_create_project)
list_projects = function_tool(_list_projects)
get_project_details = function_tool(_get_project_details)
update_project_status = function_tool(_update_project_status)
add_task_to_project = function_tool(_add_task_to_project)
read_project_file = function_tool(_read_project_file)
create_project_note = function_tool(_create_project_note)
search_project_files = function_tool(_search_project_files)