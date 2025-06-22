import pytest
from unittest.mock import patch, MagicMock
from tools.shell import _execute_command as execute_command, _get_system_info as get_system_info

class TestExecuteCommand:
    
    def test_dangerous_command_blocked(self):
        """危険なコマンドがブロックされることをテスト"""
        dangerous_commands = [
            "rm -rf /",
            "sudo rm file",
            "chmod 777 *",
            "mkfs.ext4 /dev/sda",
            "dd if=/dev/zero",
            "format c:"
        ]
        
        for cmd in dangerous_commands:
            result = execute_command(cmd)
            assert "❌ 危険なコマンドの実行は禁止されています。" in result
    
    def test_disallowed_command_blocked(self):
        """許可されていないコマンドがブロックされることをテスト"""
        disallowed_commands = [
            "python script.py",
            "node server.js",
            "rm file.txt",
            "mv file1 file2"
        ]
        
        for cmd in disallowed_commands:
            result = execute_command(cmd)
            assert "❌ コマンド" in result
            assert "は許可されていません。" in result
            assert "許可されたコマンド:" in result
    
    @patch('subprocess.run')
    def test_successful_command_execution(self, mock_run):
        """正常なコマンド実行のテスト"""
        # モックの戻り値を設定
        mock_result = MagicMock()
        mock_result.stdout = "file1.txt\nfile2.txt\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = execute_command("ls")
        
        assert "📤 出力:" in result
        assert "file1.txt" in result
        assert "📊 終了コード: 0" in result
        
        # subprocess.runが正しい引数で呼ばれたことを確認
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[1]['shell'] is True
        assert call_args[1]['capture_output'] is True
        assert call_args[1]['text'] is True
        assert call_args[1]['timeout'] == 30
    
    @patch('subprocess.run')
    def test_command_with_stderr(self, mock_run):
        """エラー出力があるコマンドのテスト"""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "Permission denied"
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        result = execute_command("ls /root")
        
        assert "⚠️ エラー:" in result
        assert "Permission denied" in result
        assert "📊 終了コード: 1" in result
    
    @patch('subprocess.run')
    def test_command_timeout(self, mock_run):
        """コマンドタイムアウトのテスト"""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("ls", 30)
        
        result = execute_command("ls")
        
        assert "❌ コマンドがタイムアウトしました（30秒制限）。" in result
    
    @patch('subprocess.run')
    def test_command_exception(self, mock_run):
        """コマンド実行例外のテスト"""
        mock_run.side_effect = Exception("予期しないエラー")
        
        result = execute_command("ls")
        
        assert "❌ コマンド実行エラー: 予期しないエラー" in result
    
    @patch('subprocess.run')
    @patch('os.getcwd')
    def test_working_directory(self, mock_getcwd, mock_run):
        """作業ディレクトリ指定のテスト"""
        mock_getcwd.return_value = "/current/dir"
        mock_result = MagicMock()
        mock_result.stdout = "success"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # 作業ディレクトリを指定してコマンド実行
        result = execute_command("pwd", working_directory="/test/dir")
        
        # subprocess.runのcwdパラメータが正しく設定されたことを確認
        call_args = mock_run.call_args
        assert call_args[1]['cwd'] == "/test/dir"
        
        # 作業ディレクトリを指定しない場合
        execute_command("pwd")
        call_args = mock_run.call_args
        assert call_args[1]['cwd'] == "/current/dir"

class TestGetSystemInfo:
    
    @patch('os.getcwd')
    @patch('os.path.exists')
    def test_system_info_without_git(self, mock_exists, mock_getcwd):
        """Gitリポジトリでない場合のシステム情報取得テスト"""
        mock_getcwd.return_value = "/test/directory"
        mock_exists.return_value = False
        
        result = get_system_info()
        
        assert "💻 システム情報:" in result
        assert "📁 現在のディレクトリ: /test/directory" in result
        assert "🔗 Gitリポジトリ: いいえ" in result
    
    @patch('os.getcwd')
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_system_info_with_git(self, mock_run, mock_exists, mock_getcwd):
        """Gitリポジトリでの場合のシステム情報取得テスト"""
        mock_getcwd.return_value = "/git/repository"
        mock_exists.return_value = True
        
        # git branch --show-current の戻り値をモック
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "main\n"
        mock_run.return_value = mock_result
        
        result = get_system_info()
        
        assert "💻 システム情報:" in result
        assert "📁 現在のディレクトリ: /git/repository" in result
        assert "🔗 Gitリポジトリ: はい" in result
        assert "🌿 ブランチ: main" in result
    
    @patch('os.getcwd')
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_system_info_git_error(self, mock_run, mock_exists, mock_getcwd):
        """Git情報取得でエラーが発生した場合のテスト"""
        mock_getcwd.return_value = "/git/repository"
        mock_exists.return_value = True
        
        # git コマンドがエラーを返す場合
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        result = get_system_info()
        
        assert "💻 システム情報:" in result
        assert "📁 現在のディレクトリ: /git/repository" in result
        assert "🔗 Gitリポジトリ: はい" in result
        # ブランチ情報は含まれない
        assert "🌿 ブランチ:" not in result
    
    @patch('os.getcwd')
    def test_system_info_exception(self, mock_getcwd):
        """システム情報取得で例外が発生した場合のテスト"""
        mock_getcwd.side_effect = Exception("ディレクトリエラー")
        
        result = get_system_info()
        
        assert "❌ システム情報取得エラー: ディレクトリエラー" in result

if __name__ == "__main__":
    pytest.main([__file__])