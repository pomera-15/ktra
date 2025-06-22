import pytest
import json
import os
import tempfile
import shutil
from unittest.mock import patch
from tools.task import _add_task as add_task, _list_tasks as list_tasks, _update_task as update_task, TaskManager

class TestTaskManager:
    def setup_method(self):
        """各テストの前に実行される setup"""
        self.test_dir = tempfile.mkdtemp()
        self.store_path = os.path.join(self.test_dir, "test_store.json")
        self.manager = TaskManager(self.store_path)
    
    def teardown_method(self):
        """各テストの後に実行される cleanup"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_ensure_store_exists(self):
        """ストアファイルが正しく作成されることをテスト"""
        assert os.path.exists(self.store_path)
        
        with open(self.store_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert data == {"tasks": []}
    
    def test_load_and_save_tasks(self):
        """タスクの読み込みと保存のテスト"""
        test_tasks = [
            {
                "id": "test-1",
                "title": "テストタスク",
                "description": "テスト用のタスクです",
                "status": "pending"
            }
        ]
        
        self.manager._save_tasks(test_tasks)
        loaded_tasks = self.manager._load_tasks()
        
        assert len(loaded_tasks) == 1
        assert loaded_tasks[0]["title"] == "テストタスク"

class TestTaskFunctions:
    def setup_method(self):
        """各テストの前に実行される setup"""
        self.test_dir = tempfile.mkdtemp()
        self.store_path = os.path.join(self.test_dir, "test_store.json")
        # TaskManagerクラスのstore_pathをモック
        self.patcher = patch('tools.task.TaskManager')
        self.mock_manager_class = self.patcher.start()
        self.mock_manager = self.mock_manager_class.return_value
    
    def teardown_method(self):
        """各テストの後に実行される cleanup"""
        self.patcher.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_add_task_basic(self):
        """基本的なタスク追加のテスト"""
        self.mock_manager._load_tasks.return_value = []
        
        result = add_task("新しいタスク")
        
        assert "✅ タスクを登録しました：「新しいタスク」" in result
        assert "（優先度：medium）" in result
        self.mock_manager._save_tasks.assert_called_once()
    
    def test_add_task_with_options(self):
        """オプション付きタスク追加のテスト"""
        self.mock_manager._load_tasks.return_value = []
        
        result = add_task(
            title="重要なタスク",
            description="説明付きタスク", 
            deadline="明日",
            priority="high"
        )
        
        assert "✅ タスクを登録しました：「重要なタスク」" in result
        assert "（優先度：high）" in result
        
        # 保存されたタスクの内容を確認
        call_args = self.mock_manager._save_tasks.call_args[0][0]
        saved_task = call_args[0]
        assert saved_task["title"] == "重要なタスク"
        assert saved_task["description"] == "説明付きタスク"
        assert saved_task["deadline"] == "明日"
        assert saved_task["priority"] == "high"
        assert saved_task["status"] == "pending"
    
    def test_list_tasks_empty(self):
        """空のタスクリストのテスト"""
        self.mock_manager._load_tasks.return_value = []
        
        result = list_tasks()
        
        assert "📝 該当するタスクはありません。" in result
    
    def test_list_tasks_with_data(self):
        """タスクがある場合のリスト表示テスト"""
        test_tasks = [
            {
                "id": "1",
                "title": "タスク1",
                "description": "説明1",
                "priority": "high",
                "status": "pending",
                "deadline": "明日"
            },
            {
                "id": "2", 
                "title": "タスク2",
                "description": "",
                "priority": "low",
                "status": "completed",
                "deadline": None
            }
        ]
        
        self.mock_manager._load_tasks.return_value = test_tasks
        
        result = list_tasks()
        
        assert "📝 タスク一覧:" in result
        assert "タスク1" in result
        assert "タスク2" in result
        assert "明日" in result
    
    def test_list_tasks_with_filter(self):
        """フィルタ付きリスト表示のテスト"""
        test_tasks = [
            {"id": "1", "title": "完了タスク", "status": "completed", "priority": "medium"},
            {"id": "2", "title": "未完了タスク", "status": "pending", "priority": "high"}
        ]
        
        self.mock_manager._load_tasks.return_value = test_tasks
        
        # ステータスフィルタ
        result = list_tasks(status="completed")
        assert "完了タスク" in result
        
        # 優先度フィルタ  
        result = list_tasks(priority="high")
        assert "未完了タスク" in result
    
    def test_update_task_found(self):
        """タスク更新成功のテスト"""
        test_tasks = [
            {
                "id": "test-id",
                "title": "元のタスク",
                "status": "pending",
                "description": "",
                "deadline": None,
                "priority": "medium"
            }
        ]
        
        self.mock_manager._load_tasks.return_value = test_tasks
        
        result = update_task("元のタスク", status="completed")
        
        assert "✅ タスク「元のタスク」を更新しました" in result
        assert "（ステータス：completed）" in result
        self.mock_manager._save_tasks.assert_called_once()
    
    def test_update_task_not_found(self):
        """タスク更新失敗（タスクが見つからない）のテスト"""
        self.mock_manager._load_tasks.return_value = []
        
        result = update_task("存在しないタスク", status="completed")
        
        assert "❌ タスク「存在しないタスク」が見つかりませんでした。" in result
        self.mock_manager._save_tasks.assert_not_called()

if __name__ == "__main__":
    pytest.main([__file__])