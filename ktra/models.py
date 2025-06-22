"""
ktra - Pydantic Data Models
設計書に基づくデータモデル定義
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Literal
from enum import Enum
import uuid


class TaskPriority(str, Enum):
    """タスクの優先度（アイゼンハワーマトリックス）"""
    URGENT_IMPORTANT = "urgent_important"
    NOT_URGENT_IMPORTANT = "not_urgent_important"
    URGENT_NOT_IMPORTANT = "urgent_not_important"
    NOT_URGENT_NOT_IMPORTANT = "not_urgent_not_important"


class EnergyLevel(str, Enum):
    """必要なエネルギーレベル"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    """タスクの状態"""
    INBOX = "inbox"        # 受信箱（未整理）
    NEXT = "next"          # 次のアクション
    IN_PROGRESS = "in_progress"  # 実行中
    BLOCKED = "blocked"    # ブロック中
    DONE = "done"          # 完了
    ARCHIVED = "archived"  # アーカイブ


class Task(BaseModel):
    """タスクの基本データモデル"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., description="タスクのタイトル")
    description: Optional[str] = Field(None, description="詳細な説明")
    priority: TaskPriority = Field(TaskPriority.NOT_URGENT_IMPORTANT)
    status: TaskStatus = Field(TaskStatus.INBOX)
    energy_required: EnergyLevel = Field(EnergyLevel.MEDIUM)
    estimated_minutes: int = Field(30, ge=5, le=480, description="推定実行時間（分）")
    actual_minutes: Optional[int] = Field(None, description="実際の実行時間（分）")
    due_date: Optional[datetime] = Field(None, description="期限")
    tags: List[str] = Field(default_factory=list, description="タグリスト")
    project: Optional[str] = Field(None, description="所属プロジェクト")
    dependencies: List[str] = Field(default_factory=list, description="依存タスクID")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(None, description="完了日時")
    progress_log: List[Dict[str, str]] = Field(default_factory=list, description="進捗ログ")
    
    def model_post_init(self, __context) -> None:
        """モデル初期化後の処理"""
        self.updated_at = datetime.now()


class TaskCreationResult(BaseModel):
    """タスク作成エージェントの出力"""
    task: Task
    subtasks: List[Task] = Field(default_factory=list)
    suggested_schedule: Optional[datetime] = None
    reasoning: str = Field(..., description="タスク作成の理由と考慮事項")


class KnowledgeItem(BaseModel):
    """ナレッジアイテム"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(..., description="知識の内容")
    summary: str = Field(..., description="要約")
    tags: List[str] = Field(default_factory=list, description="タグリスト")
    source: str = Field(..., description="情報源")
    related_tasks: List[str] = Field(default_factory=list, description="関連タスクID")
    embeddings: Optional[List[float]] = Field(None, description="ベクトル埋め込み")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ProjectStatus(str, Enum):
    """プロジェクトの状態"""
    PLANNING = "planning"      # 計画中
    ACTIVE = "active"          # アクティブ
    ON_HOLD = "on_hold"        # 保留中
    COMPLETED = "completed"    # 完了
    ARCHIVED = "archived"      # アーカイブ


class Project(BaseModel):
    """プロジェクトのデータモデル"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="プロジェクト名")
    description: Optional[str] = Field(None, description="プロジェクトの説明")
    status: ProjectStatus = Field(ProjectStatus.PLANNING)
    folder_path: Optional[str] = Field(None, description="プロジェクトフォルダのパス")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    due_date: Optional[datetime] = Field(None, description="プロジェクトの期限")
    tags: List[str] = Field(default_factory=list, description="プロジェクトタグ")
    task_ids: List[str] = Field(default_factory=list, description="関連タスクのID")
    metadata: Dict[str, str] = Field(default_factory=dict, description="追加メタデータ")
    
    def get_folder_name(self) -> str:
        """フォルダ名を生成（名前をサニタイズ）"""
        import re
        # ファイルシステムで使えない文字を置換
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', self.name)
        return f"{safe_name}_{self.id[:8]}"


class WorkContext(BaseModel):
    """現在の作業コンテキスト"""
    current_time: datetime = Field(default_factory=datetime.now)
    energy_level: EnergyLevel = Field(EnergyLevel.MEDIUM)
    available_minutes: int = Field(60, ge=5, le=480, description="利用可能な時間（分）")
    active_project: Optional[str] = Field(None, description="アクティブなプロジェクト")
    recent_tasks: List[str] = Field(default_factory=list, description="最近のタスクID")
    location: Literal["home", "office", "mobile"] = Field("home", description="作業場所")
    interruption_risk: float = Field(0.3, ge=0, le=1, description="中断リスク")


class AnalysisReport(BaseModel):
    """分析レポート"""
    period: str = Field(..., description="分析期間")
    key_metrics: Dict[str, float] = Field(default_factory=dict, description="主要メトリクス")
    patterns: List[str] = Field(default_factory=list, description="発見されたパターン")
    bottlenecks: List[str] = Field(default_factory=list, description="ボトルネック")
    recommendations: List[str] = Field(default_factory=list, description="改善提案")
    visualizations: Optional[Dict[str, str]] = Field(None, description="可視化データ")
    generated_at: datetime = Field(default_factory=datetime.now)


class UserPreferences(BaseModel):
    """ユーザー設定"""
    default_energy_level: EnergyLevel = Field(EnergyLevel.MEDIUM)
    default_task_duration: int = Field(30, ge=5, le=480)
    preferred_work_hours: List[int] = Field(default_factory=lambda: list(range(9, 17)))
    focus_session_duration: int = Field(25, description="フォーカスセッション時間（分）")
    break_duration: int = Field(5, description="休憩時間（分）")
    notification_enabled: bool = Field(True)
    auto_suggest: bool = Field(True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# 後方互換性のための古いタスク形式から新しいTask形式への変換
def convert_legacy_task(legacy_task: Dict) -> Task:
    """既存のJSONタスクを新しいTaskモデルに変換"""
    return Task(
        id=legacy_task.get('id', str(uuid.uuid4())),
        title=legacy_task.get('title', ''),
        description=legacy_task.get('description', ''),
        # 既存の優先度をマッピング
        priority=_map_legacy_priority(legacy_task.get('priority', 'medium')),
        status=_map_legacy_status(legacy_task.get('status', 'pending')),
        estimated_minutes=30,  # デフォルト値
        created_at=datetime.fromisoformat(legacy_task.get('created_at', datetime.now().isoformat())),
        tags=legacy_task.get('tags', [])
    )


def _map_legacy_priority(legacy_priority: str) -> TaskPriority:
    """既存の優先度を新しい優先度にマッピング"""
    mapping = {
        'low': TaskPriority.NOT_URGENT_NOT_IMPORTANT,
        'medium': TaskPriority.NOT_URGENT_IMPORTANT,
        'high': TaskPriority.URGENT_IMPORTANT
    }
    return mapping.get(legacy_priority, TaskPriority.NOT_URGENT_IMPORTANT)


def _map_legacy_status(legacy_status: str) -> TaskStatus:
    """既存のステータスを新しいステータスにマッピング"""
    mapping = {
        'pending': TaskStatus.INBOX,
        'completed': TaskStatus.DONE,
        'in_progress': TaskStatus.IN_PROGRESS
    }
    return mapping.get(legacy_status, TaskStatus.INBOX)