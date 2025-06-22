"""
タスク分析ツール
生産性分析、パターン発見、改善提案機能を提供
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
from agents import function_tool

# Pydanticモデルをインポート
try:
    from ..models import Task, TaskStatus, TaskPriority, EnergyLevel, AnalysisReport
    from .task import TaskManager
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


def _analyze_productivity(
    period: str = "week",
    include_visualization: bool = False
) -> str:
    """
    生産性分析を実行
    
    Args:
        period: 分析期間 (day, week, month)
        include_visualization: 可視化データを含めるか
    
    Returns:
        分析結果の文字列
    """
    if not PYDANTIC_AVAILABLE:
        return "❌ この機能にはPydanticモデルが必要です。"
    
    try:
        manager = TaskManager()
        tasks = manager.load_tasks_as_models()
        
        # 期間の設定
        end_date = datetime.now()
        if period == "day":
            start_date = end_date - timedelta(days=1)
            period_name = "過去24時間"
        elif period == "week":
            start_date = end_date - timedelta(days=7)
            period_name = "過去1週間"
        elif period == "month":
            start_date = end_date - timedelta(days=30)
            period_name = "過去1ヶ月"
        else:
            start_date = end_date - timedelta(days=7)
            period_name = "過去1週間"
        
        # 完了タスクをフィルタリング
        completed_tasks = [
            task for task in tasks
            if (task.status == TaskStatus.DONE and
                task.completed_at and
                start_date <= task.completed_at <= end_date)
        ]
        
        if not completed_tasks:
            return f"📊 {period_name}に完了したタスクがありません。"
        
        # 基本統計
        total_completed = len(completed_tasks)
        total_time = sum(task.actual_minutes or task.estimated_minutes for task in completed_tasks)
        avg_time = total_time / total_completed if total_completed > 0 else 0
        
        # 時間見積もり精度
        estimation_errors = []
        for task in completed_tasks:
            if task.actual_minutes and task.estimated_minutes:
                error = abs(task.actual_minutes - task.estimated_minutes) / task.estimated_minutes
                estimation_errors.append(error)
        
        avg_estimation_error = sum(estimation_errors) / len(estimation_errors) if estimation_errors else 0
        
        # 優先度別分析
        priority_stats = Counter(task.priority.value for task in completed_tasks)
        
        # エネルギーレベル別分析
        energy_stats = Counter(task.energy_required.value for task in completed_tasks)
        
        # 時間帯別分析
        hourly_stats = defaultdict(int)
        for task in completed_tasks:
            if task.completed_at:
                hour = task.completed_at.hour
                hourly_stats[hour] += 1
        
        # 最も生産性の高い時間帯
        most_productive_hour = max(hourly_stats.items(), key=lambda x: x[1])[0] if hourly_stats else None
        
        # タグ別分析
        tag_stats = Counter()
        for task in completed_tasks:
            for tag in task.tags:
                tag_stats[tag] += 1
        
        # 結果の生成
        result = f"📊 生産性分析レポート - {period_name}\n"
        result += "=" * 40 + "\n\n"
        
        # 基本メトリクス
        result += "📈 基本メトリクス:\n"
        result += f"   • 完了タスク数: {total_completed}件\n"
        result += f"   • 総作業時間: {total_time}分 ({total_time//60}時間{total_time%60}分)\n"
        result += f"   • 平均作業時間: {avg_time:.1f}分/タスク\n"
        
        if estimation_errors:
            result += f"   • 時間見積もり精度: ±{avg_estimation_error*100:.1f}%\n"
        
        result += "\n"
        
        # 優先度分析
        if priority_stats:
            result += "🎯 優先度別完了数:\n"
            priority_names = {
                "urgent_important": "緊急・重要",
                "not_urgent_important": "重要・非緊急",
                "urgent_not_important": "緊急・非重要",
                "not_urgent_not_important": "非緊急・非重要"
            }
            for priority, count in priority_stats.most_common():
                name = priority_names.get(priority, priority)
                result += f"   • {name}: {count}件\n"
            result += "\n"
        
        # エネルギーレベル分析
        if energy_stats:
            result += "⚡ エネルギーレベル別:\n"
            energy_names = {"high": "高", "medium": "中", "low": "低"}
            for energy, count in energy_stats.most_common():
                name = energy_names.get(energy, energy)
                result += f"   • {name}エネルギー: {count}件\n"
            result += "\n"
        
        # 時間帯分析
        if most_productive_hour is not None:
            result += f"🕐 最も生産的な時間帯: {most_productive_hour}時台\n\n"
        
        # 人気タグ
        if tag_stats:
            result += "🏷️ 人気タグ TOP5:\n"
            for tag, count in tag_stats.most_common(5):
                result += f"   • {tag}: {count}件\n"
            result += "\n"
        
        # 改善提案
        result += "💡 改善提案:\n"
        
        if avg_estimation_error > 0.3:
            result += "   • 時間見積もりの精度向上が必要です\n"
        
        urgent_important = priority_stats.get("urgent_important", 0)
        total = sum(priority_stats.values())
        if urgent_important / total > 0.3:
            result += "   • 緊急タスクが多すぎます。計画性を向上させましょう\n"
        
        high_energy_tasks = energy_stats.get("high", 0)
        if high_energy_tasks / total < 0.2:
            result += "   • 高エネルギータスクが少ないです。挑戦的な課題に取り組みましょう\n"
        
        if not result.endswith("💡 改善提案:\n"):
            result += "   • 良いペースで進んでいます！この調子を維持しましょう\n"
        
        return result
        
    except Exception as e:
        return f"❌ 分析に失敗しました：{str(e)}"


analyze_productivity = function_tool(_analyze_productivity)


def _find_task_patterns(
    lookback_days: int = 30,
    min_frequency: int = 2
) -> str:
    """
    タスクパターンを発見
    
    Args:
        lookback_days: 分析する過去の日数
        min_frequency: パターンとして認識する最小頻度
    
    Returns:
        発見されたパターンの文字列
    """
    if not PYDANTIC_AVAILABLE:
        return "❌ この機能にはPydanticモデルが必要です。"
    
    try:
        manager = TaskManager()
        tasks = manager.load_tasks_as_models()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # 対象期間のタスク
        recent_tasks = [
            task for task in tasks
            if task.created_at >= start_date
        ]
        
        if not recent_tasks:
            return f"📈 過去{lookback_days}日間にタスクがありません。"
        
        result = f"🔍 タスクパターン分析（過去{lookback_days}日間）\n"
        result += "=" * 40 + "\n\n"
        
        # 1. 曜日別パターン
        weekday_counts = defaultdict(int)
        weekday_names = ['月', '火', '水', '木', '金', '土', '日']
        
        for task in recent_tasks:
            weekday = task.created_at.weekday()
            weekday_counts[weekday] += 1
        
        if weekday_counts:
            result += "📅 曜日別タスク作成パターン:\n"
            for day, count in sorted(weekday_counts.items()):
                if count >= min_frequency:
                    result += f"   • {weekday_names[day]}曜日: {count}件\n"
            result += "\n"
        
        # 2. 時間帯パターン
        hour_counts = defaultdict(int)
        for task in recent_tasks:
            hour = task.created_at.hour
            hour_counts[hour] += 1
        
        if hour_counts:
            result += "🕐 時間帯別パターン:\n"
            peak_hours = [(hour, count) for hour, count in hour_counts.items() if count >= min_frequency]
            peak_hours.sort(key=lambda x: x[1], reverse=True)
            
            for hour, count in peak_hours[:5]:
                result += f"   • {hour}時台: {count}件\n"
            result += "\n"
        
        # 3. タグ共起パターン
        tag_combinations = defaultdict(int)
        for task in recent_tasks:
            if len(task.tags) >= 2:
                tags = sorted(task.tags)
                for i in range(len(tags)):
                    for j in range(i+1, len(tags)):
                        combination = f"{tags[i]} + {tags[j]}"
                        tag_combinations[combination] += 1
        
        if tag_combinations:
            result += "🏷️ タグの組み合わせパターン:\n"
            for combo, count in tag_combinations.items():
                if count >= min_frequency:
                    result += f"   • {combo}: {count}回\n"
            result += "\n"
        
        # 4. プロジェクト活動パターン
        project_activity = defaultdict(list)
        for task in recent_tasks:
            if task.project:
                project_activity[task.project].append(task.created_at)
        
        if project_activity:
            result += "📁 プロジェクト活動パターン:\n"
            for project, dates in project_activity.items():
                if len(dates) >= min_frequency:
                    # 活動の分散を計算
                    dates.sort()
                    avg_interval = sum((dates[i+1] - dates[i]).days for i in range(len(dates)-1)) / (len(dates)-1) if len(dates) > 1 else 0
                    result += f"   • {project}: {len(dates)}件 (平均間隔: {avg_interval:.1f}日)\n"
            result += "\n"
        
        # 5. エネルギーレベルと時間帯の相関
        energy_time_pattern = defaultdict(lambda: defaultdict(int))
        for task in recent_tasks:
            hour_range = f"{task.created_at.hour//3*3}-{task.created_at.hour//3*3+2}時"
            energy_time_pattern[task.energy_required.value][hour_range] += 1
        
        if energy_time_pattern:
            result += "⚡ エネルギーレベルと時間帯の相関:\n"
            for energy, time_data in energy_time_pattern.items():
                if sum(time_data.values()) >= min_frequency:
                    peak_time = max(time_data.items(), key=lambda x: x[1])
                    result += f"   • {energy}エネルギータスク: {peak_time[0]}に多い ({peak_time[1]}件)\n"
            result += "\n"
        
        # インサイト
        result += "💡 発見されたインサイト:\n"
        
        if weekday_counts:
            most_active_day = max(weekday_counts.items(), key=lambda x: x[1])
            result += f"   • 最もアクティブな曜日: {weekday_names[most_active_day[0]]}曜日\n"
        
        if hour_counts:
            most_active_hour = max(hour_counts.items(), key=lambda x: x[1])
            result += f"   • 最もアクティブな時間帯: {most_active_hour[0]}時台\n"
        
        if len(project_activity) > 1:
            result += f"   • 並行して進行中のプロジェクト: {len(project_activity)}個\n"
        
        return result
        
    except Exception as e:
        return f"❌ パターン分析に失敗しました：{str(e)}"


find_task_patterns = function_tool(_find_task_patterns)


def _predict_task_completion(task_title: str) -> str:
    """
    タスク完了時間を予測
    
    Args:
        task_title: タスクのタイトル
    
    Returns:
        予測結果の文字列
    """
    if not PYDANTIC_AVAILABLE:
        return "❌ この機能にはPydanticモデルが必要です。"
    
    try:
        manager = TaskManager()
        tasks = manager.load_tasks_as_models()
        
        # 対象タスクを検索
        target_task = None
        for task in tasks:
            if task_title.lower() in task.title.lower():
                target_task = task
                break
        
        if not target_task:
            return f"❌ タスク「{task_title}」が見つかりませんでした。"
        
        # 類似タスクを検索（同じタグ、プロジェクト、エネルギーレベル）
        similar_completed_tasks = []
        
        for task in tasks:
            if (task.status == TaskStatus.DONE and 
                task.actual_minutes and
                task.id != target_task.id):
                
                similarity_score = 0
                
                # タグの一致度
                common_tags = set(task.tags) & set(target_task.tags)
                if common_tags:
                    similarity_score += len(common_tags) * 2
                
                # プロジェクトの一致
                if task.project == target_task.project and task.project:
                    similarity_score += 3
                
                # エネルギーレベルの一致
                if task.energy_required == target_task.energy_required:
                    similarity_score += 2
                
                # 優先度の一致
                if task.priority == target_task.priority:
                    similarity_score += 1
                
                if similarity_score > 0:
                    similar_completed_tasks.append((similarity_score, task))
        
        # 類似度でソート
        similar_completed_tasks.sort(key=lambda x: x[0], reverse=True)
        top_similar = similar_completed_tasks[:5]  # 上位5件
        
        if not top_similar:
            return f"🔮 予測: タスク「{target_task.title}」の類似タスクが見つからないため、推定時間 {target_task.estimated_minutes}分を参考にしてください。"
        
        # 予測計算
        actual_times = [task.actual_minutes for score, task in top_similar]
        estimated_times = [task.estimated_minutes for score, task in top_similar]
        
        avg_actual = sum(actual_times) / len(actual_times)
        avg_estimated = sum(estimated_times) / len(estimated_times)
        
        # 見積もり補正率
        correction_factor = avg_actual / avg_estimated if avg_estimated > 0 else 1.0
        
        # 予測時間
        predicted_time = target_task.estimated_minutes * correction_factor
        
        # 信頼度計算（類似タスク数と類似度に基づく）
        total_similarity = sum(score for score, task in top_similar)
        confidence = min(100, (len(top_similar) * 10) + (total_similarity * 2))
        
        result = f"🔮 タスク完了時間予測: {target_task.title}\n"
        result += "=" * 40 + "\n\n"
        
        result += f"📊 基本情報:\n"
        result += f"   • 推定時間: {target_task.estimated_minutes}分\n"
        result += f"   • 優先度: {target_task.priority.value}\n"
        result += f"   • エネルギーレベル: {target_task.energy_required.value}\n"
        if target_task.tags:
            result += f"   • タグ: {', '.join(target_task.tags)}\n"
        result += "\n"
        
        result += f"🎯 予測結果:\n"
        result += f"   • 予測完了時間: {predicted_time:.0f}分\n"
        result += f"   • 信頼度: {confidence:.0f}%\n"
        result += f"   • 類似タスク数: {len(top_similar)}件\n"
        result += "\n"
        
        if correction_factor > 1.2:
            result += "⚠️  類似タスクは見積もりより時間がかかる傾向があります\n"
        elif correction_factor < 0.8:
            result += "✅ 類似タスクは見積もりより早く完了する傾向があります\n"
        else:
            result += "📈 見積もりは適切と思われます\n"
        
        # 類似タスクの詳細
        if top_similar:
            result += "\n📚 参考にした類似タスク:\n"
            for i, (score, task) in enumerate(top_similar[:3], 1):
                result += f"   {i}. {task.title} (実際: {task.actual_minutes}分, 類似度: {score})\n"
        
        return result
        
    except Exception as e:
        return f"❌ 予測に失敗しました：{str(e)}"


predict_task_completion = function_tool(_predict_task_completion)


def _generate_daily_summary() -> str:
    """
    日次サマリーを生成
    
    Returns:
        日次サマリーの文字列
    """
    if not PYDANTIC_AVAILABLE:
        return "❌ この機能にはPydanticモデルが必要です。"
    
    try:
        manager = TaskManager()
        tasks = manager.load_tasks_as_models()
        
        today = datetime.now().date()
        
        # 今日のタスク
        today_tasks = [
            task for task in tasks
            if task.created_at.date() == today or 
               (task.completed_at and task.completed_at.date() == today)
        ]
        
        # 今日完了したタスク
        completed_today = [
            task for task in tasks
            if (task.status == TaskStatus.DONE and 
                task.completed_at and 
                task.completed_at.date() == today)
        ]
        
        # 今日作成されたタスク
        created_today = [
            task for task in tasks
            if task.created_at.date() == today
        ]
        
        # 明日期限のタスク
        tomorrow = today + timedelta(days=1)
        due_tomorrow = [
            task for task in tasks
            if (task.due_date and 
                task.due_date.date() == tomorrow and 
                task.status not in [TaskStatus.DONE, TaskStatus.ARCHIVED])
        ]
        
        result = f"📅 日次サマリー - {today.strftime('%Y年%m月%d日')}\n"
        result += "=" * 40 + "\n\n"
        
        # 今日の成果
        if completed_today:
            total_time = sum(task.actual_minutes or task.estimated_minutes for task in completed_today)
            result += f"✅ 今日の成果 ({len(completed_today)}件完了):\n"
            for task in completed_today:
                result += f"   • {task.title}\n"
            result += f"\n💪 総作業時間: {total_time}分 ({total_time//60}時間{total_time%60}分)\n\n"
        else:
            result += "📝 今日はまだタスクを完了していません。\n\n"
        
        # 今日作成されたタスク
        if created_today:
            result += f"📥 今日追加されたタスク ({len(created_today)}件):\n"
            for task in created_today:
                if task.status != TaskStatus.DONE:  # 完了済みは除く
                    status_icon = _get_status_icon(task.status.value)
                    priority_icon = _get_priority_icon(task.priority.value)
                    result += f"   • {status_icon} {priority_icon} {task.title}\n"
            result += "\n"
        
        # 明日期限のタスク
        if due_tomorrow:
            result += f"⏰ 明日期限のタスク ({len(due_tomorrow)}件):\n"
            for task in due_tomorrow:
                priority_icon = _get_priority_icon(task.priority.value)
                result += f"   • {priority_icon} {task.title}\n"
            result += "\n"
        
        # 進行中のタスク
        in_progress = [task for task in tasks if task.status == TaskStatus.IN_PROGRESS]
        if in_progress:
            result += f"🔄 進行中のタスク ({len(in_progress)}件):\n"
            for task in in_progress:
                result += f"   • {task.title}\n"
            result += "\n"
        
        # 次のアクション推奨
        next_tasks = [task for task in tasks if task.status == TaskStatus.NEXT]
        if next_tasks:
            # エネルギーレベルとタイムスタンプに基づいてソート
            next_tasks.sort(key=lambda t: (t.priority.value, t.created_at))
            result += "💡 明日の推奨アクション:\n"
            for task in next_tasks[:3]:
                priority_icon = _get_priority_icon(task.priority.value)
                energy_icon = _get_energy_icon(task.energy_required.value)
                result += f"   • {priority_icon} {energy_icon} {task.title}\n"
            result += "\n"
        
        # 統計情報
        active_tasks = [task for task in tasks if task.status not in [TaskStatus.DONE, TaskStatus.ARCHIVED]]
        result += f"📊 現在の状況:\n"
        result += f"   • アクティブなタスク: {len(active_tasks)}件\n"
        result += f"   • 今週完了予定: {len([t for t in active_tasks if t.due_date and t.due_date <= datetime.now() + timedelta(days=7)])}件\n"
        
        return result
        
    except Exception as e:
        return f"❌ サマリー生成に失敗しました：{str(e)}"


def _get_status_icon(status: str) -> str:
    """ステータスアイコンを取得"""
    icons = {
        "inbox": "📥", "next": "⏭️", "in_progress": "🔄",
        "blocked": "🚫", "done": "✅", "archived": "📦",
        "pending": "⏳", "completed": "✅"
    }
    return icons.get(status, "⏳")


def _get_priority_icon(priority: str) -> str:
    """優先度アイコンを取得"""
    icons = {
        "urgent_important": "🔴", "not_urgent_important": "🟡",
        "urgent_not_important": "🟠", "not_urgent_not_important": "🟢",
        "high": "🔴", "medium": "🟡", "low": "🟢"
    }
    return icons.get(priority, "🟡")


def _get_energy_icon(energy: str) -> str:
    """エネルギーレベルアイコンを取得"""
    icons = {"high": "⚡", "medium": "🔋", "low": "🪫"}
    return icons.get(energy, "🔋")


generate_daily_summary = function_tool(_generate_daily_summary)