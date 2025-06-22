"""
作業コンテキスト管理ツール
現在の作業状況、エネルギーレベル、環境に基づく最適化機能を提供
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from agents import function_tool

# Pydanticモデルをインポート
try:
    from ..models import WorkContext, EnergyLevel, UserPreferences
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


class ContextManager:
    def __init__(self, store_path: str = None):
        if store_path is None:
            home_dir = os.path.expanduser("~")
            ktra_dir = os.path.join(home_dir, ".ktra")
            os.makedirs(ktra_dir, exist_ok=True)
            self.context_path = os.path.join(ktra_dir, "context.json")
            self.preferences_path = os.path.join(ktra_dir, "preferences.json")
        else:
            self.context_path = store_path
            self.preferences_path = store_path.replace("context.json", "preferences.json")
        
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        # コンテキストファイル
        if not os.path.exists(self.context_path):
            os.makedirs(os.path.dirname(self.context_path), exist_ok=True)
            default_context = {
                "current_time": datetime.now().isoformat(),
                "energy_level": "medium",
                "available_minutes": 60,
                "location": "home",
                "interruption_risk": 0.3,
                "active_project": None,
                "recent_tasks": []
            }
            with open(self.context_path, 'w', encoding='utf-8') as f:
                json.dump(default_context, f, ensure_ascii=False, indent=2)
        
        # 設定ファイル
        if not os.path.exists(self.preferences_path):
            default_preferences = {
                "default_energy_level": "medium",
                "default_task_duration": 30,
                "preferred_work_hours": list(range(9, 17)),
                "focus_session_duration": 25,
                "break_duration": 5,
                "notification_enabled": True,
                "auto_suggest": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            with open(self.preferences_path, 'w', encoding='utf-8') as f:
                json.dump(default_preferences, f, ensure_ascii=False, indent=2)
    
    def load_context(self) -> 'WorkContext':
        """現在のコンテキストを読み込み"""
        if not PYDANTIC_AVAILABLE:
            return None
        
        try:
            with open(self.context_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # datetime文字列をdatetimeオブジェクトに変換
            if 'current_time' in data and isinstance(data['current_time'], str):
                data['current_time'] = datetime.fromisoformat(data['current_time'])
            
            return WorkContext(**data)
        except Exception:
            # デフォルトコンテキストを返す
            return WorkContext()
    
    def save_context(self, context: 'WorkContext'):
        """コンテキストを保存"""
        if not PYDANTIC_AVAILABLE:
            return
        
        try:
            data = context.model_dump()
            # datetimeを文字列に変換
            if isinstance(data.get('current_time'), datetime):
                data['current_time'] = data['current_time'].isoformat()
            
            with open(self.context_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def load_preferences(self) -> 'UserPreferences':
        """ユーザー設定を読み込み"""
        if not PYDANTIC_AVAILABLE:
            return None
        
        try:
            with open(self.preferences_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # datetime文字列をdatetimeオブジェクトに変換
            for field in ['created_at', 'updated_at']:
                if field in data and isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
            
            return UserPreferences(**data)
        except Exception:
            return UserPreferences()
    
    def save_preferences(self, preferences: 'UserPreferences'):
        """ユーザー設定を保存"""
        if not PYDANTIC_AVAILABLE:
            return
        
        try:
            data = preferences.model_dump()
            # datetimeを文字列に変換
            for field in ['created_at', 'updated_at']:
                if isinstance(data.get(field), datetime):
                    data[field] = data[field].isoformat()
            
            with open(self.preferences_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def _update_work_context(
    energy_level: str = "",
    available_minutes: int = 0,
    location: str = "",
    active_project: str = "",
    interruption_risk: float = -1
) -> str:
    """
    現在の作業コンテキストを更新
    
    Args:
        energy_level: 現在のエネルギーレベル (high, medium, low)
        available_minutes: 利用可能時間（分）
        location: 作業場所 (home, office, mobile)
        active_project: アクティブなプロジェクト名
        interruption_risk: 中断リスク (0.0-1.0)
    
    Returns:
        更新結果のメッセージ
    """
    if not PYDANTIC_AVAILABLE:
        return "❌ この機能にはPydanticモデルが必要です。"
    
    try:
        manager = ContextManager()
        context = manager.load_context()
        
        # 値の更新
        if energy_level:
            try:
                context.energy_level = EnergyLevel(energy_level)
            except ValueError:
                return f"❌ 無効なエネルギーレベル: {energy_level} (high, medium, low から選択)"
        
        if available_minutes > 0:
            context.available_minutes = available_minutes
        
        if location:
            if location in ["home", "office", "mobile"]:
                context.location = location
            else:
                return f"❌ 無効な場所: {location} (home, office, mobile から選択)"
        
        if active_project:
            context.active_project = active_project if active_project != "none" else None
        
        if 0 <= interruption_risk <= 1:
            context.interruption_risk = interruption_risk
        
        # 現在時刻を更新
        context.current_time = datetime.now()
        
        manager.save_context(context)
        
        result = "✅ 作業コンテキストを更新しました:\n"
        result += f"   • エネルギーレベル: {context.energy_level.value}\n"
        result += f"   • 利用可能時間: {context.available_minutes}分\n"
        result += f"   • 作業場所: {context.location}\n"
        
        if context.active_project:
            result += f"   • アクティブプロジェクト: {context.active_project}\n"
        
        result += f"   • 中断リスク: {context.interruption_risk:.0%}\n"
        
        return result
        
    except Exception as e:
        return f"❌ コンテキスト更新に失敗しました：{str(e)}"


update_work_context = function_tool(_update_work_context)


def _get_current_context() -> str:
    """
    現在の作業コンテキストを取得
    
    Returns:
        現在のコンテキスト情報
    """
    if not PYDANTIC_AVAILABLE:
        return "❌ この機能にはPydanticモデルが必要です。"
    
    try:
        manager = ContextManager()
        context = manager.load_context()
        
        # 時刻ベースでエネルギーレベルを自動推定
        current_hour = datetime.now().hour
        auto_energy = _estimate_energy_by_time(current_hour)
        
        result = "🔍 現在の作業コンテキスト:\n"
        result += "=" * 30 + "\n\n"
        
        result += f"🕐 現在時刻: {context.current_time.strftime('%Y-%m-%d %H:%M')}\n"
        result += f"⚡ エネルギーレベル: {context.energy_level.value}"
        
        if auto_energy != context.energy_level.value:
            result += f" (時刻ベース推定: {auto_energy})"
        
        result += f"\n⏰ 利用可能時間: {context.available_minutes}分\n"
        result += f"📍 作業場所: {context.location}\n"
        
        if context.active_project:
            result += f"📁 アクティブプロジェクト: {context.active_project}\n"
        
        result += f"🚫 中断リスク: {context.interruption_risk:.0%}\n"
        
        if context.recent_tasks:
            result += f"\n📝 最近のタスク:\n"
            for task_id in context.recent_tasks[-3:]:  # 最新3件
                result += f"   • {task_id[:8]}...\n"
        
        # 作業提案
        result += "\n💡 作業提案:\n"
        
        if context.energy_level == EnergyLevel.HIGH:
            result += "   • 高エネルギータスクに集中する絶好の機会です\n"
            result += "   • 新しいプロジェクトの開始や創造的な作業がおすすめ\n"
        elif context.energy_level == EnergyLevel.MEDIUM:
            result += "   • ルーチンワークや計画的なタスクに適しています\n"
            result += "   • 中程度の集中力が必要なタスクがおすすめ\n"
        else:
            result += "   • 簡単なタスクや整理作業が適しています\n"
            result += "   • 休憩を取ることも考慮してください\n"
        
        if context.available_minutes < 30:
            result += "   • 短時間で完了できるタスクを選択してください\n"
        elif context.available_minutes > 120:
            result += "   • 大きなタスクに取り組む時間があります\n"
        
        if context.interruption_risk > 0.5:
            result += "   • 中断されやすい環境です。集中しやすいタスクを選んでください\n"
        
        return result
        
    except Exception as e:
        return f"❌ コンテキスト取得に失敗しました：{str(e)}"


get_current_context = function_tool(_get_current_context)


def _estimate_energy_by_time(hour: int) -> str:
    """時刻からエネルギーレベルを推定"""
    if 6 <= hour < 10:
        return "high"  # 朝
    elif 10 <= hour < 14:
        return "medium"  # 午前中〜昼
    elif 14 <= hour < 16:
        return "low"  # 午後の眠気
    elif 16 <= hour < 19:
        return "medium"  # 夕方
    else:
        return "low"  # 夜間


def _start_focus_session(
    session_type: str = "pomodoro",
    duration_minutes: int = 25,
    task_title: str = ""
) -> str:
    """
    フォーカスセッションを開始
    
    Args:
        session_type: セッションタイプ (pomodoro, deep_work, quick_task)
        duration_minutes: セッション時間（分）
        task_title: 対象タスクのタイトル
    
    Returns:
        セッション開始結果
    """
    if not PYDANTIC_AVAILABLE:
        return "❌ この機能にはPydanticモデルが必要です。"
    
    try:
        manager = ContextManager()
        context = manager.load_context()
        
        # セッション情報の記録
        session_info = {
            "type": session_type,
            "duration": duration_minutes,
            "start_time": datetime.now().isoformat(),
            "task_title": task_title,
            "initial_energy": context.energy_level.value
        }
        
        # フォーカスセッション用のコンテキスト更新
        context.current_time = datetime.now()
        context.available_minutes = duration_minutes
        context.interruption_risk = max(0, context.interruption_risk - 0.2)  # フォーカス時は中断リスクを下げる
        
        # セッション履歴に追加
        if not hasattr(context, 'focus_sessions'):
            context.focus_sessions = []
        
        manager.save_context(context)
        
        # セッション別の設定
        session_configs = {
            "pomodoro": {
                "name": "ポモドーロ",
                "break_after": 5,
                "description": "25分集中 + 5分休憩"
            },
            "deep_work": {
                "name": "ディープワーク",
                "break_after": 15,
                "description": "長時間集中セッション"
            },
            "quick_task": {
                "name": "クイックタスク",
                "break_after": 2,
                "description": "短時間タスク処理"
            }
        }
        
        config = session_configs.get(session_type, session_configs["pomodoro"])
        
        result = f"🎯 {config['name']}セッション開始\n"
        result += "=" * 30 + "\n\n"
        
        result += f"⏱️  セッション時間: {duration_minutes}分\n"
        result += f"📋 セッションタイプ: {config['description']}\n"
        
        if task_title:
            result += f"📝 対象タスク: {task_title}\n"
        
        result += f"⚡ 開始時エネルギー: {context.energy_level.value}\n"
        result += f"🚫 中断リスク: {context.interruption_risk:.0%}\n\n"
        
        result += "💡 フォーカスのコツ:\n"
        result += "   • 通知をオフにする\n"
        result += "   • 必要な資料を事前に準備\n"
        result += "   • 小さな目標を設定\n"
        result += f"   • {duration_minutes}分後に{config['break_after']}分の休憩\n\n"
        
        result += f"🕐 終了予定時刻: {(datetime.now() + timedelta(minutes=duration_minutes)).strftime('%H:%M')}\n"
        
        # タイマー終了の目安
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        result += f"\n⏰ {end_time.strftime('%H:%M')}にセッション終了です。頑張ってください！"
        
        return result
        
    except Exception as e:
        return f"❌ フォーカスセッション開始に失敗しました：{str(e)}"


start_focus_session = function_tool(_start_focus_session)


def _update_preferences(
    default_energy_level: str = "",
    default_task_duration: int = 0,
    focus_session_duration: int = 0,
    break_duration: int = 0,
    notification_enabled: bool = None,
    auto_suggest: bool = None
) -> str:
    """
    ユーザー設定を更新
    
    Args:
        default_energy_level: デフォルトエネルギーレベル
        default_task_duration: デフォルトタスク時間
        focus_session_duration: フォーカスセッション時間
        break_duration: 休憩時間
        notification_enabled: 通知有効化
        auto_suggest: 自動提案有効化
    
    Returns:
        更新結果のメッセージ
    """
    if not PYDANTIC_AVAILABLE:
        return "❌ この機能にはPydanticモデルが必要です。"
    
    try:
        manager = ContextManager()
        preferences = manager.load_preferences()
        
        # 設定の更新
        if default_energy_level:
            try:
                preferences.default_energy_level = EnergyLevel(default_energy_level)
            except ValueError:
                return f"❌ 無効なエネルギーレベル: {default_energy_level}"
        
        if default_task_duration > 0:
            preferences.default_task_duration = default_task_duration
        
        if focus_session_duration > 0:
            preferences.focus_session_duration = focus_session_duration
        
        if break_duration > 0:
            preferences.break_duration = break_duration
        
        if notification_enabled is not None:
            preferences.notification_enabled = notification_enabled
        
        if auto_suggest is not None:
            preferences.auto_suggest = auto_suggest
        
        preferences.updated_at = datetime.now()
        
        manager.save_preferences(preferences)
        
        result = "✅ ユーザー設定を更新しました:\n"
        result += f"   • デフォルトエネルギーレベル: {preferences.default_energy_level.value}\n"
        result += f"   • デフォルトタスク時間: {preferences.default_task_duration}分\n"
        result += f"   • フォーカスセッション時間: {preferences.focus_session_duration}分\n"
        result += f"   • 休憩時間: {preferences.break_duration}分\n"
        result += f"   • 通知: {'有効' if preferences.notification_enabled else '無効'}\n"
        result += f"   • 自動提案: {'有効' if preferences.auto_suggest else '無効'}\n"
        
        return result
        
    except Exception as e:
        return f"❌ 設定更新に失敗しました：{str(e)}"


update_preferences = function_tool(_update_preferences)


def _get_work_environment_suggestion() -> str:
    """
    現在の状況に基づく作業環境の提案
    
    Returns:
        作業環境提案の文字列
    """
    if not PYDANTIC_AVAILABLE:
        return "❌ この機能にはPydanticモデルが必要です。"
    
    try:
        manager = ContextManager()
        context = manager.load_context()
        preferences = manager.load_preferences()
        
        current_hour = datetime.now().hour
        
        result = "🏢 作業環境提案\n"
        result += "=" * 20 + "\n\n"
        
        # 時間帯別提案
        result += "⏰ 時間帯別提案:\n"
        if 6 <= current_hour < 9:
            result += "   • 朝の集中力を活かして重要タスクに取り組みましょう\n"
            result += "   • 静かな環境で深い思考が必要な作業がおすすめ\n"
        elif 9 <= current_hour < 12:
            result += "   • 午前中の高い生産性を活用しましょう\n"
            result += "   • クリエイティブな作業や新しいプロジェクトの開始に最適\n"
        elif 12 <= current_hour < 14:
            result += "   • 昼食後は軽めのタスクから始めましょう\n"
            result += "   • メールチェックや整理作業がおすすめ\n"
        elif 14 <= current_hour < 16:
            result += "   • 午後の眠気対策が重要です\n"
            result += "   • 立ちながらの作業や軽い運動を挟みましょう\n"
        elif 16 <= current_hour < 19:
            result += "   • 夕方のエネルギー回復を活用\n"
            result += "   • 一日の振り返りや明日の準備に適した時間です\n"
        else:
            result += "   • 夜間は無理をせず、軽いタスクに留めましょう\n"
            result += "   • リラックスや学習の時間として活用\n"
        
        result += "\n"
        
        # エネルギーレベル別環境提案
        result += f"⚡ エネルギーレベル別環境設定 (現在: {context.energy_level.value}):\n"
        
        if context.energy_level == EnergyLevel.HIGH:
            result += "   🔥 高エネルギーモード:\n"
            result += "     • 明るい照明で集中力を最大化\n"
            result += "     • アップテンポな音楽またはホワイトノイズ\n"
            result += "     • 立ちデスクでの作業を検討\n"
            result += "     • 25-30分の集中セッション\n"
        elif context.energy_level == EnergyLevel.MEDIUM:
            result += "   🔋 標準エネルギーモード:\n"
            result += "     • 自然光と適度な室内照明\n"
            result += "     • 環境音楽や軽いBGM\n"
            result += "     • 快適な座り心地の椅子\n"
            result += "     • 20-25分の作業 + 5分休憩\n"
        else:
            result += "   🪫 低エネルギーモード:\n"
            result += "     • 柔らかい照明でリラックス\n"
            result += "     • 静かな環境または自然音\n"
            result += "     • クッションやブランケットで快適性向上\n"
            result += "     • 15-20分の短いセッション\n"
        
        result += "\n"
        
        # 場所別提案
        result += f"📍 現在の場所別提案 (現在: {context.location}):\n"
        
        if context.location == "home":
            result += "   🏠 在宅環境最適化:\n"
            result += "     • 専用の作業スペースを確保\n"
            result += "     • 家族に作業時間を伝える\n"
            result += "     • スマートフォンは別の部屋に\n"
            result += "     • 定期的な換気で空気をリフレッシュ\n"
        elif context.location == "office":
            result += "   🏢 オフィス環境活用:\n"
            result += "     • 同僚とのコラボレーション時間を設定\n"
            result += "     • 会議室での集中作業も検討\n"
            result += "     • 共有リソースの活用\n"
            result += "     • 適度な雑談でリフレッシュ\n"
        else:  # mobile
            result += "   📱 モバイル環境対応:\n"
            result += "     • ノイズキャンセリングヘッドフォン必須\n"
            result += "     • バッテリー残量に注意\n"
            result += "     • 軽いタスクや読み物中心\n"
            result += "     • Wi-Fi環境の確認\n"
        
        result += "\n"
        
        # 中断リスク対策
        if context.interruption_risk > 0.3:
            result += "🚫 中断リスク対策:\n"
            result += "     • 「作業中」の表示を出す\n"
            result += "     • 通知をオフまたは最小限に\n"
            result += "     • 緊急時の連絡方法を事前に伝える\n"
            result += "     • 短いタスクに分割して取り組む\n\n"
        
        # カスタマイズ提案
        result += "🛠️  個人設定の活用:\n"
        result += f"   • 推奨フォーカス時間: {preferences.focus_session_duration}分\n"
        result += f"   • 推奨休憩時間: {preferences.break_duration}分\n"
        
        if preferences.auto_suggest:
            result += "   • 自動提案が有効です。最適なタスクが推奨されます\n"
        
        if preferences.notification_enabled:
            result += "   • 通知が有効です。重要な締切をお知らせします\n"
        
        return result
        
    except Exception as e:
        return f"❌ 環境提案の生成に失敗しました：{str(e)}"


get_work_environment_suggestion = function_tool(_get_work_environment_suggestion)