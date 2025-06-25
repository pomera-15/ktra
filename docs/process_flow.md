# ktra 処理の流れドキュメント

## システム概要

ktra（カトレア）は OpenAI Agent SDK を使用したパーソナル AI エージェントです。タスク管理、プロジェクト管理、Web検索などの機能を提供し、ユーザーの生産性をサポートします。

## アーキテクチャ概要

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Interface │───▶│   AI Agent      │───▶│    Tools        │
│                 │    │                 │    │                 │
│ - User Input    │    │ - OpenAI Agent  │    │ - Task Mgmt     │
│ - Command Parse │    │ - SDK           │    │ - Project Mgmt  │
│ - Display       │    │ - Tool Routing  │    │ - Web Search    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Components │    │  Data Models    │    │   Storage       │
│                 │    │                 │    │                 │
│ - Task Selector │    │ - Pydantic      │    │ - JSON Files    │
│ - Project Sel.  │    │ - Task Model    │    │ - Project Dirs  │
│ - Action Sel.   │    │ - Project Model │    │ - Knowledge DB  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 起動フロー

### 1. アプリケーション初期化 (`main.py`)

```python
def main():
    # 1. UI初期化
    ui = KtraInterface()
    
    # 2. ウェルカム画面表示（3D ASCII アート）
    ui.show_welcome()
    
    # 3. API キー確認
    if not check_api_key():
        sys.exit(1)
    
    # 4. エージェント作成
    agent = create_ktra_agent()
    
    # 5. メインループ開始
    while True:
        user_input = ui.get_input()
        # ... 処理続行
```

### 2. エージェント作成 (`agent.py`)

```python
def create_ktra_agent(model: str = None) -> Agent:
    # 1. システムプロンプト読み込み
    system_prompt = _load_system_prompt()
    
    # 2. モデル設定
    if model is None:
        model = get_default_model()
    
    # 3. ツール登録（32個のツール）
    agent = Agent(
        name="ktra",
        instructions=system_prompt,
        tools=[
            # 基本タスク管理
            add_task, list_tasks, update_task, search_tasks, recommend_next_task,
            # システム関連
            execute_command, get_system_info,
            # モデル管理
            change_model, get_current_model,
            # 知識管理
            save_knowledge, search_knowledge, get_knowledge_stats, link_knowledge_to_task,
            # 分析機能
            analyze_productivity, find_task_patterns, predict_task_completion, generate_daily_summary,
            # コンテキスト管理
            update_work_context, get_current_context, start_focus_session, update_preferences, get_work_environment_suggestion,
            # プロジェクト管理
            create_project, list_projects, get_project_details, update_project_status, add_task_to_project, read_project_file, create_project_note, search_project_files,
            # Web検索
            web_search, search_news
        ],
        model=model
    )
    
    return agent
```

## メインループ処理

### 1. ユーザー入力処理 (`interface.py`)

```python
def get_input(self) -> str:
    # 1. ペンディングAIリクエストチェック
    if self.pending_ai_request:
        return self.pending_ai_request
    
    # 2. プロンプト表示（コマンド補完付き）
    user_input = prompt("❯ ", completer=self.completer).strip()
    
    return user_input
```

### 2. 特殊コマンド処理

```python
def handle_special_commands(self, user_input: str) -> bool:
    # /tasks コマンド -> TaskSelector起動
    # /projects コマンド -> ProjectSelector起動
    # /help, /clear, /quit など -> 各種操作
    # /models -> モデル選択画面
```

### 3. AI エージェント処理

ユーザー入力が特殊コマンドでない場合：

1. **エージェント実行**: `run_agent_with_monitoring(agent, user_input)`
2. **ツール選択**: AIエージェントが適切なツールを選択
3. **ツール実行**: 選択されたツールの実行
4. **結果返却**: ユーザーに結果を表示

## UIコンポーネント詳細

### 1. TaskSelector (`task_selector.py`)

```
┌─────────────────────────────────┐
│ タスク一覧                      │
├─────────────────────────────────┤
│ → 選択されたタスク              │
│   他のタスク1                   │
│   他のタスク2                   │
├─────────────────────────────────┤
│ ↑↓ 選択  Enter 操作  n 新規     │
└─────────────────────────────────┘
```

**操作フロー:**
1. タスク一覧表示
2. 矢印キーでタスク選択
3. Enter押下 → タスク詳細表示 + 操作メニュー
4. 操作選択（矢印キー選択）:
   - ステータス変更
   - 詳細編集
   - AIに相談
   - 削除

### 2. ProjectSelector (`project_selector.py`)

```
┌─────────────────────────────────┐
│ プロジェクト一覧                │
├─────────────────────────────────┤
│ → 選択されたプロジェクト (5タスク)│
│   他のプロジェクト1 (2タスク)    │
│   他のプロジェクト2 (0タスク)    │
├─────────────────────────────────┤
│ ↑↓ 選択  Enter 操作  n 新規     │
└─────────────────────────────────┘
```

**操作フロー:**
1. プロジェクト一覧表示（タスク数付き）
2. 矢印キーでプロジェクト選択
3. Enter押下 → プロジェクト詳細表示 + 操作メニュー
4. 操作選択:
   - ステータス変更
   - 詳細編集
   - フォルダを開く
   - メモ作成
   - ファイル一覧
   - 削除

## データ管理

### 1. タスクデータ (`TaskManager`)

**保存場所**: `memory/store.json`

**データ構造**:
```python
class Task(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: TaskStatus  # INBOX, NEXT, IN_PROGRESS, BLOCKED, DONE, ARCHIVED
    priority: TaskPriority  # URGENT_IMPORTANT, NOT_URGENT_IMPORTANT, etc.
    energy_required: EnergyLevel  # HIGH, MEDIUM, LOW
    estimated_minutes: int
    actual_minutes: Optional[int]
    project: Optional[str]
    tags: List[str]
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
```

### 2. プロジェクトデータ (`ProjectManager`)

**保存場所**: `memory/projects.json`

**フォルダ構造**:
```
projects/
├── プロジェクト名/
│   ├── notes/       # メモファイル
│   ├── documents/   # ドキュメント
│   └── references/  # 参考資料
```

**データ構造**:
```python
class Project(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: ProjectStatus  # PLANNING, ACTIVE, ON_HOLD, COMPLETED, ARCHIVED
    folder_path: Optional[str]
    tags: List[str]
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

## ツール実行フロー

### 1. タスク管理ツール

```python
# ユーザー: "明日までに資料作成"
# ↓ AIエージェントが解析
# ↓ add_task ツール選択
add_task(
    title="資料作成",
    description="",
    deadline="2024-01-XX",
    priority="medium"
)
# ↓ TaskManager.save_task()
# ↓ JSON ファイルに保存
```

### 2. Web検索ツール

```python
# ユーザー: "Pythonについて調べて"
# ↓ AIエージェントが解析
# ↓ web_search ツール選択
web_search(query="Python programming language")
# ↓ DuckDuckGo API呼び出し
# ↓ 結果整形・表示
```

### 3. プロジェクト管理ツール

```python
# ユーザー: "新しいプロジェクト作成"
# ↓ AIエージェントが解析
# ↓ create_project ツール選択
create_project(
    name="プロジェクト名",
    description="説明"
)
# ↓ ProjectManager.create_project_folder()
# ↓ フォルダ作成 + JSON保存
```

## エラーハンドリング

### 1. API キーエラー

```python
def check_api_key():
    # 1. 環境変数チェック
    # 2. フォーマット検証
    # 3. エラーメッセージ表示（設定方法案内）
```

### 2. ツール実行エラー

```python
try:
    # ツール実行
    result = tool.execute()
except Exception as e:
    # エラーログ記録
    # ユーザーフレンドリーなメッセージ表示
    return f"エラーが発生しました: {str(e)}"
```

### 3. ファイルI/Oエラー

```python
def save_tasks():
    try:
        # ファイル保存処理
    except PermissionError:
        return "ファイルの書き込み権限がありません"
    except Exception as e:
        return f"保存に失敗しました: {str(e)}"
```

## パフォーマンス考慮事項

### 1. ファイル読み込み最適化

- タスク・プロジェクトデータの遅延読み込み
- 必要時のみJSONファイルアクセス

### 2. UI応答性

- 重い処理は非同期実行
- プログレス表示（`show_thinking`）

### 3. メモリ管理

- 大量データの段階的読み込み
- 不要なオブジェクトの適切な破棄

## セキュリティ

### 1. コマンド実行制限

```python
DANGEROUS_COMMANDS = [
    'rm -rf', 'sudo', 'chmod 777', 'dd if=', ':(){ :|:& };:', 
    'wget', 'curl -X POST', 'curl -X PUT', 'curl -X DELETE'
]

ALLOWED_COMMANDS = [
    'ls', 'pwd', 'git status', 'git log', 'git diff', 
    'curl', 'ping', 'date', 'whoami', 'echo'
]
```

### 2. API キー保護

- 環境変数での管理
- ログ出力での秘匿化

### 3. ファイルアクセス制限

- プロジェクトディレクトリ内のみアクセス許可
- 重要システムファイルへのアクセス禁止

## 拡張性

### 1. 新ツール追加

```python
# 1. tools/ ディレクトリに新モジュール作成
# 2. @function_tool デコレータでツール化
# 3. agent.py でツール登録
```

### 2. 新UIコンポーネント

```python
# 1. ui/ ディレクトリに新クラス作成
# 2. prompt_toolkit Application使用
# 3. interface.py で統合
```

### 3. 新データモデル

```python
# 1. models.py に Pydantic モデル追加
# 2. 対応する Manager クラス作成
# 3. ツールで活用
```

このドキュメントは ktra の主要な処理フローと実装詳細を示しています。新機能追加や保守作業の際の参考資料として活用してください。