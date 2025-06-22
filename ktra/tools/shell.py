import subprocess
import os
from typing import Dict, Any
from agents import function_tool

def _execute_command(command: str, working_directory: str = None) -> str:
    """
    シェルコマンドを実行します。
    
    Args:
        command: 実行するコマンド
        working_directory: コマンドを実行するディレクトリ（オプション）
    
    Returns:
        コマンドの実行結果
    """
    try:
        # セキュリティのため、危険なコマンドをブロック
        dangerous_commands = ['rm -rf', 'sudo', 'chmod 777', 'mkfs', 'dd if=', 'format']
        if any(dangerous in command.lower() for dangerous in dangerous_commands):
            return "❌ 危険なコマンドの実行は禁止されています。"
        
        # 許可されたコマンドのみ実行
        allowed_commands = ['ls', 'pwd', 'git status', 'git log', 'git diff', 'curl', 'ping', 'date', 'whoami', 'echo']
        if not any(command.startswith(allowed) for allowed in allowed_commands):
            return f"❌ コマンド '{command}' は許可されていません。\n許可されたコマンド: {', '.join(allowed_commands)}"
        
        # 作業ディレクトリの設定
        cwd = working_directory if working_directory else os.getcwd()
        
        # コマンド実行
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30
        )
        
        output = ""
        if result.stdout:
            output += f"📤 出力:\n{result.stdout}\n"
        if result.stderr:
            output += f"⚠️ エラー:\n{result.stderr}\n"
        
        output += f"📊 終了コード: {result.returncode}"
        
        return output
        
    except subprocess.TimeoutExpired:
        return "❌ コマンドがタイムアウトしました（30秒制限）。"
    except Exception as e:
        return f"❌ コマンド実行エラー: {str(e)}"

execute_command = function_tool(_execute_command)

def _get_system_info() -> str:
    """
    システム情報を取得します。
    
    Returns:
        システム情報の文字列
    """
    try:
        # 現在のディレクトリ
        current_dir = os.getcwd()
        
        # 基本的なシステム情報を収集
        info = f"💻 システム情報:\n"
        info += f"📁 現在のディレクトリ: {current_dir}\n"
        
        # Gitリポジトリかどうかチェック
        if os.path.exists(os.path.join(current_dir, '.git')):
            info += "🔗 Gitリポジトリ: はい\n"
            
            # Git情報を取得
            try:
                branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                             capture_output=True, text=True)
                if branch_result.returncode == 0:
                    info += f"🌿 ブランチ: {branch_result.stdout.strip()}\n"
            except:
                pass
        else:
            info += "🔗 Gitリポジトリ: いいえ\n"
        
        return info
        
    except Exception as e:
        return f"❌ システム情報取得エラー: {str(e)}"

get_system_info = function_tool(_get_system_info)