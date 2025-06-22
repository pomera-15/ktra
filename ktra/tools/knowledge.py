"""
知識管理ツール
ナレッジの保存、検索、管理機能を提供
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
from agents import function_tool

# Pydanticモデルをインポート
try:
    from ..models import KnowledgeItem
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


class KnowledgeManager:
    def __init__(self, store_path: str = None):
        if store_path is None:
            home_dir = os.path.expanduser("~")
            ktra_dir = os.path.join(home_dir, ".ktra")
            os.makedirs(ktra_dir, exist_ok=True)
            self.store_path = os.path.join(ktra_dir, "knowledge.json")
        else:
            self.store_path = store_path
        self._ensure_store_exists()
    
    def _ensure_store_exists(self):
        if not os.path.exists(self.store_path):
            os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
            with open(self.store_path, 'w', encoding='utf-8') as f:
                json.dump({"knowledge_items": []}, f, ensure_ascii=False, indent=2)
    
    def _load_knowledge(self) -> List[Dict[str, Any]]:
        with open(self.store_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("knowledge_items", [])
    
    def _save_knowledge(self, items: List[Dict[str, Any]]):
        with open(self.store_path, 'w', encoding='utf-8') as f:
            json.dump({"knowledge_items": items}, f, ensure_ascii=False, indent=2)
    
    def load_knowledge_as_models(self) -> List['KnowledgeItem']:
        """ナレッジをPydanticモデルとして読み込み"""
        if not PYDANTIC_AVAILABLE:
            return []
        
        legacy_items = self._load_knowledge()
        items = []
        
        for legacy_item in legacy_items:
            try:
                # datetime文字列をdatetimeオブジェクトに変換
                if 'created_at' in legacy_item and isinstance(legacy_item['created_at'], str):
                    legacy_item['created_at'] = datetime.fromisoformat(legacy_item['created_at'])
                if 'updated_at' in legacy_item and isinstance(legacy_item['updated_at'], str):
                    legacy_item['updated_at'] = datetime.fromisoformat(legacy_item['updated_at'])
                
                items.append(KnowledgeItem(**legacy_item))
            except Exception:
                continue
        
        return items
    
    def save_knowledge_from_models(self, items: List['KnowledgeItem']):
        """PydanticモデルからJSONに保存"""
        if not PYDANTIC_AVAILABLE:
            return
        
        item_dicts = [item.model_dump() for item in items]
        # datetimeを文字列に変換
        for item_dict in item_dicts:
            for key, value in item_dict.items():
                if isinstance(value, datetime):
                    item_dict[key] = value.isoformat()
        
        self._save_knowledge(item_dicts)


def _save_knowledge(
    content: str,
    summary: str,
    tags: str = "",
    source: str = "user_input",
    related_task_ids: str = ""
) -> str:
    """
    新しい知識を保存
    
    Args:
        content: 知識の内容
        summary: 知識の要約
        tags: タグ（カンマ区切り）
        source: 情報源
        related_task_ids: 関連タスクID（カンマ区切り）
    
    Returns:
        保存結果のメッセージ
    """
    manager = KnowledgeManager()
    
    if PYDANTIC_AVAILABLE:
        try:
            # タグとタスクIDの解析
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            task_id_list = [task_id.strip() for task_id in related_task_ids.split(",") if task_id.strip()]
            
            knowledge_item = KnowledgeItem(
                content=content,
                summary=summary,
                tags=tag_list,
                source=source,
                related_tasks=task_id_list
            )
            
            existing_items = manager.load_knowledge_as_models()
            existing_items.append(knowledge_item)
            manager.save_knowledge_from_models(existing_items)
            
            return f"📚 知識を保存しました：「{summary}」（タグ：{', '.join(tag_list) if tag_list else 'なし'}）"
            
        except Exception as e:
            return f"❌ 知識の保存に失敗しました：{str(e)}"
    
    # フォールバック（従来方式）
    items = manager._load_knowledge()
    
    item = {
        "id": str(uuid.uuid4()),
        "content": content,
        "summary": summary,
        "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
        "source": source,
        "related_tasks": [task_id.strip() for task_id in related_task_ids.split(",") if task_id.strip()],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    items.append(item)
    manager._save_knowledge(items)
    
    return f"📚 知識を保存しました：「{summary}」"


save_knowledge = function_tool(_save_knowledge)


def _search_knowledge(
    query: str = "",
    tags: str = "",
    source: str = "",
    limit: int = 5
) -> str:
    """
    知識を検索
    
    Args:
        query: 検索キーワード
        tags: タグフィルター（カンマ区切り）
        source: 情報源フィルター
        limit: 最大表示件数
    
    Returns:
        検索結果の文字列
    """
    manager = KnowledgeManager()
    
    if PYDANTIC_AVAILABLE:
        try:
            items = manager.load_knowledge_as_models()
            
            # フィルタリング
            filtered_items = []
            search_tags = [tag.strip().lower() for tag in tags.split(",") if tag.strip()] if tags else []
            
            for item in items:
                # クエリ検索
                if query:
                    query_lower = query.lower()
                    if (query_lower not in item.content.lower() and 
                        query_lower not in item.summary.lower()):
                        continue
                
                # タグフィルター
                if search_tags:
                    item_tags_lower = [tag.lower() for tag in item.tags]
                    if not any(tag in item_tags_lower for tag in search_tags):
                        continue
                
                # ソースフィルター
                if source and item.source != source:
                    continue
                
                filtered_items.append(item)
            
            # 更新日時順でソート（新しい順）
            filtered_items.sort(key=lambda x: x.updated_at, reverse=True)
            filtered_items = filtered_items[:limit]
            
            if not filtered_items:
                return "🔍 検索条件に一致する知識が見つかりませんでした。"
            
            # 結果の表示
            result = f"🔍 知識検索結果 ({len(filtered_items)}件):\n\n"
            
            for i, item in enumerate(filtered_items, 1):
                result += f"{i}. 📚 {item.summary}\n"
                result += f"   📅 {item.created_at.strftime('%Y-%m-%d %H:%M')}"
                
                if item.tags:
                    result += f" 🏷️ {', '.join(item.tags)}"
                
                if item.source != "user_input":
                    result += f" 📍 {item.source}"
                
                result += "\n"
                
                # 内容のプレビュー
                content_preview = item.content[:200]
                if len(item.content) > 200:
                    content_preview += "..."
                result += f"   💭 {content_preview}\n\n"
            
            return result
            
        except Exception as e:
            pass
    
    # フォールバック
    items = manager._load_knowledge()
    
    if not items:
        return "📚 保存された知識がありません。"
    
    result = "📚 知識一覧:\n"
    for i, item in enumerate(items[:limit], 1):
        result += f"{i}. {item.get('summary', 'タイトルなし')}\n"
        if item.get('tags'):
            result += f"   🏷️ {', '.join(item['tags'])}\n"
    
    return result


search_knowledge = function_tool(_search_knowledge)


def _get_knowledge_stats() -> str:
    """
    知識ベースの統計情報を取得
    
    Returns:
        統計情報の文字列
    """
    manager = KnowledgeManager()
    
    if PYDANTIC_AVAILABLE:
        try:
            items = manager.load_knowledge_as_models()
            
            if not items:
                return "📊 知識ベースは空です。"
            
            # 統計計算
            total_items = len(items)
            
            # タグ別集計
            tag_counts = {}
            for item in items:
                for tag in item.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # ソース別集計
            source_counts = {}
            for item in items:
                source_counts[item.source] = source_counts.get(item.source, 0) + 1
            
            # 作成日別集計（過去30日）
            from collections import defaultdict
            daily_counts = defaultdict(int)
            
            for item in items:
                if item.created_at:
                    date_key = item.created_at.strftime('%Y-%m-%d')
                    daily_counts[date_key] += 1
            
            # 結果の生成
            result = f"📊 知識ベース統計:\n\n"
            result += f"📚 総知識数: {total_items}件\n\n"
            
            if tag_counts:
                result += "🏷️ 人気タグ TOP5:\n"
                sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
                for tag, count in sorted_tags[:5]:
                    result += f"   • {tag}: {count}件\n"
                result += "\n"
            
            if source_counts:
                result += "📍 情報源別:\n"
                for source, count in source_counts.items():
                    result += f"   • {source}: {count}件\n"
                result += "\n"
            
            # 最近の活動
            recent_items = sorted(items, key=lambda x: x.created_at, reverse=True)[:3]
            if recent_items:
                result += "🕒 最近追加された知識:\n"
                for item in recent_items:
                    result += f"   • {item.summary} ({item.created_at.strftime('%m/%d %H:%M')})\n"
            
            return result
            
        except Exception as e:
            pass
    
    # フォールバック
    items = manager._load_knowledge()
    return f"📊 知識ベース: {len(items)}件の知識が保存されています。"


get_knowledge_stats = function_tool(_get_knowledge_stats)


def _link_knowledge_to_task(knowledge_id: str, task_id: str) -> str:
    """
    知識とタスクを関連付け
    
    Args:
        knowledge_id: 知識ID
        task_id: タスクID
    
    Returns:
        関連付け結果のメッセージ
    """
    manager = KnowledgeManager()
    
    if PYDANTIC_AVAILABLE:
        try:
            items = manager.load_knowledge_as_models()
            
            # 指定された知識を検索
            target_item = None
            for item in items:
                if item.id == knowledge_id:
                    target_item = item
                    break
            
            if not target_item:
                return f"❌ 知識ID「{knowledge_id}」が見つかりませんでした。"
            
            # タスクIDを追加（重複チェック）
            if task_id not in target_item.related_tasks:
                target_item.related_tasks.append(task_id)
                target_item.updated_at = datetime.now()
                
                manager.save_knowledge_from_models(items)
                return f"🔗 知識「{target_item.summary}」をタスクに関連付けました。"
            else:
                return f"ℹ️ 知識「{target_item.summary}」は既にそのタスクに関連付けられています。"
                
        except Exception as e:
            return f"❌ 関連付けに失敗しました：{str(e)}"
    
    return "❌ この機能にはPydanticモデルが必要です。"


link_knowledge_to_task = function_tool(_link_knowledge_to_task)