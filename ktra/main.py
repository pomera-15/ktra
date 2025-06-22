#!/usr/bin/env python3
"""
ktra - Personal AI Agent
パーソナルAIエージェント「ktra（クトラ）」のメインエントリーポイント
"""

import sys
import os
import asyncio
from .agent import create_ktra_agent
from agents import Runner
from .ui.interface import KtraInterface
from .agent_monitor import create_enhanced_agent_runner

def check_api_key():
    """
    OpenAI API キーの存在をチェックし、設定方法を案内する
    
    Returns:
        bool: API キーが設定されている場合True、そうでなければFalse
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OpenAI API キーが設定されていません")
        print()
        print("📋 API キーの設定方法:")
        print("1️⃣ .envファイルを作成:")
        print("   echo 'OPENAI_API_KEY=your_api_key_here' > .env")
        print()
        print("2️⃣ または環境変数で設定:")
        print("   export OPENAI_API_KEY=your_api_key_here")
        print()
        print("3️⃣ OpenAI API キーの取得:")
        print("   https://platform.openai.com/api-keys")
        print()
        print("⚠️ API キーを設定後、再度実行してください。")
        return False
    
    if len(api_key.strip()) < 10:
        print("❌ 設定されているAPI キーが無効です（短すぎます）")
        print("💡 正しいOpenAI API キーを設定してください。")
        return False
    
    if not api_key.startswith(('sk-', 'sk-proj-')):
        print("❌ 設定されているAPI キーの形式が正しくありません")
        print("💡 OpenAI API キーは 'sk-' または 'sk-proj-' で始まります。")
        return False
    
    return True

def main():
    # Initialize enhanced UI
    ui = KtraInterface()
    
    # Show welcome screen
    ui.show_welcome()
    
    # OpenAI API キーの確認
    if not check_api_key():
        ui.display_response(
            "API キーの設定が必要です。設定後に再実行してください。", 
            "error"
        )
        sys.exit(1)
    
    # OpenAI Agent SDKを使用してエージェントを作成
    try:
        with ui.show_thinking("エージェントを初期化中..."):
            # イベントループを確保
            try:
                # 現在のイベントループをチェック
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # ランニングループがない場合、新しいイベントループを設定
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        raise RuntimeError("Event loop is closed")
                except (RuntimeError, AttributeError):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            
            agent = create_ktra_agent()
            # エージェント監視機能を作成
            run_agent_with_monitoring = create_enhanced_agent_runner(ui)
        
        ui.display_response("エージェントを正常に初期化しました", "system")
        
    except Exception as e:
        ui.display_response(
            f"エージェントの初期化に失敗しました: {str(e)}\n"
            "💡 API キーが正しく設定されているか確認してください。",
            "error"
        )
        sys.exit(1)
    
    # Main interaction loop
    while True:
        try:
            user_input = ui.get_input()
            
            if not user_input:
                continue
            
            # Handle special UI commands
            if ui.handle_special_commands(user_input):
                if user_input.lower() in ["/quit", "/exit", "quit", "exit"]:
                    break
                continue
            
            # Process with agent
            try:
                # イベントループを確保してから実行
                try:
                    # 現在のイベントループをチェック
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # ランニングループがない場合、既存のイベントループを使用
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_closed():
                            raise RuntimeError("Event loop is closed")
                    except (RuntimeError, AttributeError):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                
                # 監視機能付きでエージェントを実行
                result = run_agent_with_monitoring(agent, user_input)
                
                ui.display_response(result.final_output, "assistant")
                
            except Exception as e:
                ui.display_response(
                    f"エラーが発生しました: {str(e)}\n"
                    "💡 API キーの有効性やネットワーク接続を確認してください。",
                    "error"
                )
            
        except KeyboardInterrupt:
            ui.display_response("ktraを終了します。お疲れ様でした！", "system")
            break
        except Exception as e:
            ui.display_response(f"予期しないエラーが発生しました: {str(e)}", "error")

if __name__ == "__main__":
    main()