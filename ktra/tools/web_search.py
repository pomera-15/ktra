"""
Web検索ツール
"""

import requests
from typing import List, Dict, Any
from agents import function_tool


def _web_search(query: str, num_results: int = 5) -> str:
    """
    Web検索を実行し、結果を返す
    
    Args:
        query: 検索クエリ
        num_results: 取得する結果数（デフォルト: 5）
    
    Returns:
        str: 検索結果のテキスト
    """
    try:
        # DuckDuckGo Instant Answer APIを使用（無料で利用可能）
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 結果をフォーマット
        results = []
        
        # Abstract（要約）があれば追加
        if data.get("Abstract"):
            results.append(f"📄 要約: {data['Abstract']}")
            if data.get("AbstractURL"):
                results.append(f"🔗 参照: {data['AbstractURL']}")
        
        # Answer（即答）があれば追加
        if data.get("Answer"):
            results.append(f"💡 回答: {data['Answer']}")
        
        # Definition（定義）があれば追加
        if data.get("Definition"):
            results.append(f"📖 定義: {data['Definition']}")
            if data.get("DefinitionURL"):
                results.append(f"🔗 出典: {data['DefinitionURL']}")
        
        # RelatedTopics（関連トピック）があれば追加
        if data.get("RelatedTopics"):
            results.append(f"\n🔍 関連トピック:")
            for i, topic in enumerate(data["RelatedTopics"][:num_results]):
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(f"  {i+1}. {topic['Text']}")
                    if topic.get("FirstURL"):
                        results.append(f"     🔗 {topic['FirstURL']}")
        
        if not results:
            return f"❌ '{query}' の検索結果が見つかりませんでした。\n💡 より具体的なキーワードで検索してみてください。"
        
        return "\n".join(results)
        
    except requests.exceptions.RequestException as e:
        return f"❌ Web検索中にエラーが発生しました: {str(e)}\n💡 インターネット接続を確認してください。"
    except Exception as e:
        return f"❌ 検索処理中にエラーが発生しました: {str(e)}"


def _search_news(query: str, num_results: int = 3) -> str:
    """
    ニュース検索を実行する
    
    Args:
        query: 検索クエリ
        num_results: 取得する結果数（デフォルト: 3）
    
    Returns:
        str: ニュース検索結果のテキスト
    """
    try:
        # DuckDuckGoでニュース検索（簡易版）
        url = "https://api.duckduckgo.com/"
        params = {
            "q": f"{query} site:news.yahoo.co.jp OR site:www3.nhk.or.jp OR site:mainichi.jp",
            "format": "json",
            "no_html": "1"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        results = [f"📰 '{query}' に関するニュース検索結果:"]
        
        if data.get("RelatedTopics"):
            for i, topic in enumerate(data["RelatedTopics"][:num_results]):
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(f"\n{i+1}. {topic['Text']}")
                    if topic.get("FirstURL"):
                        results.append(f"   🔗 {topic['FirstURL']}")
        else:
            results.append(f"❌ '{query}' に関するニュースが見つかりませんでした。")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ ニュース検索中にエラーが発生しました: {str(e)}"


# OpenAI Agent SDK用のツール関数を作成
web_search = function_tool(_web_search)
search_news = function_tool(_search_news)