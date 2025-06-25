import pytest
import sys
from unittest.mock import patch, MagicMock
from ktra.main import check_api_key, main

class TestCheckApiKey:
    """API キーチェック機能のテスト"""
    
    @patch('os.getenv')
    def test_api_key_not_set(self, mock_getenv, capsys):
        """API キーが設定されていない場合のテスト"""
        mock_getenv.return_value = None
        
        result = check_api_key()
        
        assert result is False
        captured = capsys.readouterr()
        assert "❌ OpenAI API キーが設定されていません" in captured.out
        assert "📋 API キーの設定方法:" in captured.out
        assert "https://platform.openai.com/api-keys" in captured.out
    
    @patch('os.getenv')
    def test_api_key_empty(self, mock_getenv, capsys):
        """空のAPI キーが設定されている場合のテスト"""
        mock_getenv.return_value = ""
        
        result = check_api_key()
        
        assert result is False
        captured = capsys.readouterr()
        assert "❌ OpenAI API キーが設定されていません" in captured.out
    
    @patch('os.getenv')
    def test_api_key_too_short(self, mock_getenv, capsys):
        """短すぎるAPI キーが設定されている場合のテスト"""
        mock_getenv.return_value = "sk-123"
        
        result = check_api_key()
        
        assert result is False
        captured = capsys.readouterr()
        assert "❌ 設定されているAPI キーが無効です（短すぎます）" in captured.out
    
    @patch('os.getenv')
    def test_api_key_wrong_format(self, mock_getenv, capsys):
        """間違った形式のAPI キーが設定されている場合のテスト"""
        mock_getenv.return_value = "invalid-api-key-format-123456789"
        
        result = check_api_key()
        
        assert result is False
        captured = capsys.readouterr()
        assert "❌ 設定されているAPI キーの形式が正しくありません" in captured.out
        assert "OpenAI API キーは 'sk-' または 'sk-proj-' で始まります" in captured.out
    
    @patch('os.getenv')
    def test_api_key_valid_sk_format(self, mock_getenv):
        """正しい形式のAPI キー（sk-形式）のテスト"""
        mock_getenv.return_value = "sk-1234567890abcdef1234567890abcdef"
        
        result = check_api_key()
        
        assert result is True
    
    @patch('os.getenv')
    def test_api_key_valid_sk_proj_format(self, mock_getenv):
        """正しい形式のAPI キー（sk-proj-形式）のテスト"""
        mock_getenv.return_value = "sk-proj-1234567890abcdef1234567890abcdef"
        
        result = check_api_key()
        
        assert result is True
    
    @patch('os.getenv')
    def test_api_key_with_whitespace(self, mock_getenv):
        """前後に空白があるAPI キーのテスト"""
        mock_getenv.return_value = "  sk-1234567890abcdef1234567890abcdef  "
        
        result = check_api_key()
        
        assert result is True

class TestMain:
    """main関数のテスト"""
    
    @patch('main.check_api_key')
    @patch('sys.exit')
    def test_main_no_api_key(self, mock_exit, mock_check_api_key, capsys):
        """API キーが設定されていない場合のmain関数テスト"""
        mock_check_api_key.return_value = False
        
        main()
        
        mock_exit.assert_called_once_with(1)
        captured = capsys.readouterr()
        assert "❌ API キーの設定が必要です" in captured.out
    
    @patch('main.check_api_key')
    @patch('main.create_ktra_agent')
    @patch('sys.exit')
    def test_main_agent_creation_failure(self, mock_exit, mock_create_agent, mock_check_api_key, capsys):
        """エージェント作成に失敗した場合のテスト"""
        mock_check_api_key.return_value = True
        mock_create_agent.side_effect = Exception("API connection failed")
        
        main()
        
        mock_exit.assert_called_once_with(1)
        captured = capsys.readouterr()
        assert "❌ エージェントの初期化に失敗しました" in captured.out
        assert "API connection failed" in captured.out
    
    @patch('main.check_api_key')
    @patch('main.create_ktra_agent')
    @patch('builtins.input')
    def test_main_successful_exit(self, mock_input, mock_create_agent, mock_check_api_key, capsys):
        """正常な終了のテスト"""
        mock_check_api_key.return_value = True
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent
        mock_input.return_value = "exit"
        
        main()
        
        captured = capsys.readouterr()
        assert "✅ エージェントを正常に初期化しました" in captured.out
        assert "👋 ktraを終了します。お疲れ様でした！" in captured.out
    
    @patch('main.check_api_key')
    @patch('main.create_ktra_agent')
    @patch('builtins.input')
    def test_main_keyboard_interrupt(self, mock_input, mock_create_agent, mock_check_api_key, capsys):
        """キーボード割り込みのテスト"""
        mock_check_api_key.return_value = True
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent
        mock_input.side_effect = KeyboardInterrupt()
        
        main()
        
        captured = capsys.readouterr()
        assert "✅ エージェントを正常に初期化しました" in captured.out
        assert "👋 ktraを終了します。お疲れ様でした！" in captured.out

if __name__ == "__main__":
    pytest.main([__file__])