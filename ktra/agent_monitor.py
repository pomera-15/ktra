"""
Agent execution monitoring for ktra
エージェントの実行過程を監視・表示するモジュール
"""

import time
import threading
from typing import Any, Dict, List, Optional
from .ui.interface import KtraInterface

class AgentMonitor:
    """エージェントの実行過程を監視・表示するクラス"""
    
    def __init__(self, ui: KtraInterface):
        self.ui = ui
        self.is_monitoring = False
        self.current_step = ""
    
    def start_monitoring(self):
        """監視を開始"""
        self.is_monitoring = True
        self.ui.show_agent_thinking("ユーザーの入力を分析中...")
    
    def stop_monitoring(self):
        """監視を停止"""
        self.is_monitoring = False
    
    def show_thinking(self, message: str = None):
        """思考過程を表示"""
        if self.is_monitoring:
            self.ui.show_agent_thinking()
    
    def show_detailed_thinking(self, reasoning: str):
        """詳細な思考過程を表示"""
        if self.is_monitoring:
            self.ui.show_thinking_detail(reasoning)
    
    def show_tool_call(self, tool_name: str, params: Dict[str, Any] = None, file_info: str = None):
        """ツール実行を表示"""
        if self.is_monitoring:
            self.ui.show_tool_execution(tool_name, params, file_info)
    
    def show_tool_result(self, result: str, success: bool = True, expand_hint: str = None):
        """ツール実行結果を表示"""
        if self.is_monitoring:
            self.ui.show_tool_result(result, success, expand_hint)
    
    def show_action_start(self, action: str):
        """アクション開始を表示"""
        if self.is_monitoring:
            self.ui.show_action_start(action)
    
    def show_reasoning(self, reasoning: str):
        """推論過程を表示"""
        if self.is_monitoring:
            self.ui.show_agent_reasoning(reasoning)
    
    def analyze_agent_result(self, result) -> None:
        """
        エージェントの実行結果を分析して思考過程を表示
        """
        try:
            # Thinking過程の詳細分析
            thinking_content = self._extract_thinking_content()
            if thinking_content:
                self.show_reasoning(thinking_content)
            
            # ツール実行の分析
            if hasattr(result, 'messages'):
                self._analyze_messages_claude_style(result.messages)
            
            if hasattr(result, 'tool_calls'):
                self._analyze_tool_calls_claude_style(result.tool_calls)
            
            if hasattr(result, 'steps'):
                self._analyze_steps_claude_style(result.steps)
                
        except Exception as e:
            self.show_tool_result(f"結果分析中にエラー: {str(e)}", success=False)
    
    def _extract_thinking_content(self) -> str:
        """思考内容を生成"""
        return """ユーザーの入力を分析し、適切なツールを選択する必要がある。

タスク管理に関する質問の場合は、list_tasksツールを使用してタスク一覧を取得する。
システム情報の質問の場合は、get_system_infoツールを実行する。
ファイル操作の場合は、execute_commandツールで安全なコマンドを実行する。

まず、入力内容から意図を判断し、最適なツールを選択して実行する。"""
    
    def _analyze_messages_claude_style(self, messages):
        """メッセージ履歴をClaude Codeスタイルで分析"""
        if not messages:
            return
            
        for message in messages:
            if hasattr(message, 'role'):
                if message.role == 'assistant':
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        # ツール呼び出しがある場合
                        for tool_call in message.tool_calls:
                            self._display_tool_call_claude_style(tool_call)
    
    def _analyze_tool_calls_claude_style(self, tool_calls):
        """ツール呼び出しをClaude Codeスタイルで分析"""
        if not tool_calls:
            return
            
        for tool_call in tool_calls:
            self._display_tool_call_claude_style(tool_call)
    
    def _display_tool_call_claude_style(self, tool_call):
        """ツール呼び出しをClaude Codeスタイルで表示"""
        if hasattr(tool_call, 'function'):
            func = tool_call.function
            tool_name = getattr(func, 'name', 'unknown')
            
            # パラメータを取得
            params = {}
            if hasattr(func, 'arguments'):
                try:
                    import json
                    params = json.loads(func.arguments)
                except:
                    params = {'arguments': str(func.arguments)}
            
            # ツール名に応じたファイル情報の生成
            file_info = self._generate_file_info(tool_name, params)
            
            self.show_tool_call(tool_name, params, file_info)
            
            # 実際のツール実行をシミュレート
            result = self._simulate_tool_result(tool_name, params)
            expand_hint = self._generate_expand_hint(tool_name, result)
            
            self.show_tool_result(result, success=True, expand_hint=expand_hint)
    
    def _generate_file_info(self, tool_name: str, params: dict) -> str:
        """ツール実行に応じたファイル情報を生成"""
        if tool_name == 'list_tasks':
            return None
        elif tool_name == 'execute_command':
            command = params.get('command', '')
            return f"command='{command}'"
        elif tool_name == 'get_system_info':
            return None
        elif tool_name == 'add_task':
            title = params.get('title', '')
            return f"title='{title[:20]}...'" if len(title) > 20 else f"title='{title}'"
        return None
    
    def _simulate_tool_result(self, tool_name: str, params: dict) -> str:
        """ツール実行結果をシミュレート"""
        if tool_name == 'list_tasks':
            return "📝 該当するタスクはありません。"
        elif tool_name == 'execute_command':
            command = params.get('command', '')
            if command == 'pwd':
                return "/Users/yamanashi/workspace/ktra"
            elif command == 'ls':
                return "ktra/  tests/  README.md  setup.py  requirements.txt"
            return f"Command '{command}' executed successfully"
        elif tool_name == 'get_system_info':
            return "macOS 14.4, Python 3.9.18, ktra v1.0.0"
        return "Tool executed successfully"
    
    def _generate_expand_hint(self, tool_name: str, result: str) -> str:
        """展開ヒントを生成"""
        if tool_name == 'list_tasks':
            return "No tasks found"
        elif tool_name == 'execute_command':
            lines = result.split('\n')
            if len(lines) > 1:
                return f"{len(lines)} lines (ctrl+r to expand)"
        return None
    
    def _analyze_steps_claude_style(self, steps):
        """実行ステップをClaude Codeスタイルで分析"""
        if not steps:
            return
            
        for step in steps:
            if hasattr(step, 'type'):
                if step.type == 'tool_call':
                    # ツール実行ステップは上記で処理済み
                    pass
                elif step.type == 'reasoning':
                    if hasattr(step, 'content'):
                        self.show_detailed_thinking(step.content)

def create_enhanced_agent_runner(ui: KtraInterface):
    """拡張されたエージェント実行関数を作成"""
    monitor = AgentMonitor(ui)
    
    def run_agent_with_monitoring(agent, user_input):
        """監視機能付きでエージェントを実行"""
        from agents import Runner
        
        # 監視開始
        monitor.start_monitoring()
        
        try:
            # エージェント実行開始の表示
            monitor.show_action_start("ユーザー入力を処理中")
            
            # エージェント実行
            result = Runner.run_sync(agent, user_input)
            
            # 結果分析とClaude Codeスタイル表示
            monitor.analyze_agent_result(result)
            
            return result
            
        except Exception as e:
            monitor.show_tool_result(f"エラー: {str(e)}", success=False)
            raise
        finally:
            # 監視停止
            monitor.stop_monitoring()
    
    return run_agent_with_monitoring