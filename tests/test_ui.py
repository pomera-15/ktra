import pytest
from unittest.mock import patch, MagicMock
from ui.interface import KtraInterface

class TestKtraInterface:
    def setup_method(self):
        """テスト前の初期化"""
        self.ui = KtraInterface()
    
    def test_interface_initialization(self):
        """UIの初期化テスト"""
        assert self.ui.console is not None
        assert self.ui.history is not None
        assert self.ui.completer is not None
        
        # 候補リストの確認
        assert len(self.ui.task_examples) > 0
        assert len(self.ui.shell_examples) > 0
        assert len(self.ui.help_commands) > 0
    
    def test_special_commands_handling(self):
        """特別なコマンドの処理テスト"""
        
        # ヘルプコマンド
        assert self.ui.handle_special_commands("/help") == True
        assert self.ui.handle_special_commands("/commands") == True
        assert self.ui.handle_special_commands("/examples") == True
        assert self.ui.handle_special_commands("/clear") == True
        
        # 終了コマンド
        assert self.ui.handle_special_commands("/quit") == True
        assert self.ui.handle_special_commands("quit") == True
        assert self.ui.handle_special_commands("exit") == True
        
        # 通常の入力
        assert self.ui.handle_special_commands("普通のメッセージ") == False
        assert self.ui.handle_special_commands("タスクを追加") == False
    
    @patch('ui.interface.Confirm.ask')
    def test_confirm_action(self, mock_confirm):
        """確認ダイアログのテスト"""
        mock_confirm.return_value = True
        
        result = self.ui.confirm_action("続行しますか？")
        
        assert result == True
        mock_confirm.assert_called_once_with("続行しますか？")
    
    def test_response_formatting(self, capsys):
        """レスポンスの表示形式テスト"""
        
        # 正常なレスポンス
        self.ui.display_response("✅ タスクを登録しました", "assistant")
        captured = capsys.readouterr()
        assert "タスクを登録しました" in captured.out
        
        # エラーレスポンス
        self.ui.display_response("❌ エラーが発生しました", "error")
        captured = capsys.readouterr()
        assert "エラーが発生しました" in captured.out
        
        # システムメッセージ
        self.ui.display_response("システムメッセージ", "system")
        captured = capsys.readouterr()
        assert "システムメッセージ" in captured.out
    
    def test_status_display(self, capsys):
        """ステータス表示のテスト"""
        status_info = {
            "Active Tasks": 5,
            "Completed": 12,
            "Agent Status": "Ready"
        }
        
        self.ui.show_status(status_info)
        captured = capsys.readouterr()
        
        assert "Active Tasks" in captured.out
        assert "5" in captured.out
        assert "Completed" in captured.out
        assert "12" in captured.out
    
    def test_help_display(self, capsys):
        """ヘルプ表示のテスト"""
        self.ui.show_help()
        captured = capsys.readouterr()
        
        # ヘルプテーブルの内容確認
        assert "/help" in captured.out
        assert "/commands" in captured.out
        assert "/examples" in captured.out
        assert "タスク管理の例" in captured.out
    
    def test_commands_display(self, capsys):
        """コマンド一覧表示のテスト"""
        self.ui.show_commands()
        captured = capsys.readouterr()
        
        # コマンドテーブルの内容確認
        assert "ls" in captured.out
        assert "pwd" in captured.out
        assert "git status" in captured.out
        assert "利用可能なシェルコマンド" in captured.out
    
    def test_examples_display(self, capsys):
        """使用例表示のテスト"""
        self.ui.show_examples()
        captured = capsys.readouterr()
        
        # 使用例の内容確認
        assert "明日までに請求書" in captured.out
        assert "タスク管理:" in captured.out
        assert "情報確認:" in captured.out
        assert "対話例:" in captured.out
    
    def test_welcome_display(self, capsys):
        """ウェルカム画面のテスト"""
        self.ui.show_welcome()
        captured = capsys.readouterr()
        
        # ウェルカム画面の内容確認
        assert "ktra" in captured.out
        assert "Personal AI Agent" in captured.out
        assert "Quick Start" in captured.out
        assert "/help でコマンド一覧" in captured.out
        # ASCII art確認
        assert "██" in captured.out
    
    def test_detailed_thinking_display(self, capsys):
        """詳細な思考過程表示のテスト"""
        steps = [
            "ユーザーの入力を分析中...",
            "適切なツールを選択中...",
            "回答を生成中..."
        ]
        
        self.ui.show_detailed_thinking(steps)
        captured = capsys.readouterr()
        
        # 思考過程の内容確認
        assert "🧠 エージェントの思考過程" in captured.out
        assert "🔄 ユーザーの入力を分析中..." in captured.out
        assert "🔄 適切なツールを選択中..." in captured.out
        assert "🔄 回答を生成中..." in captured.out
    
    def test_agent_action_display(self, capsys):
        """エージェントアクション表示のテスト"""
        self.ui.show_agent_action("タスクリストを取得", "現在のタスクを確認しています")
        captured = capsys.readouterr()
        
        # アクション表示の内容確認
        assert "🎯 タスクリストを取得" in captured.out
        assert "💡 現在のタスクを確認しています" in captured.out
        assert "Agent Action" in captured.out

if __name__ == "__main__":
    pytest.main([__file__])