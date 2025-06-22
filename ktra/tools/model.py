"""
Model management tools for ktra agent
"""

import os
import json
from agents import function_tool

def get_available_models() -> list:
    """利用可能なモデル一覧を取得します。"""
    return [
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini"
    ]

def get_default_model() -> str:
    """デフォルトモデルを取得します。設定ファイルまたは環境変数から読み込み。"""
    # 設定ファイルから読み込み
    model = _load_model_setting()
    if model and model in get_available_models():
        return model
    
    # 環境変数から読み込み
    env_model = os.getenv("KTRA_MODEL")
    if env_model and env_model in get_available_models():
        return env_model
    
    # デフォルト
    return "gpt-3.5-turbo"

def set_default_model(model: str) -> bool:
    """デフォルトモデルを設定ファイルに保存します。"""
    if model not in get_available_models():
        return False
    
    return _save_model_setting(model)

def _load_model_setting() -> str:
    """設定ファイルからモデル設定を読み込みます。"""
    try:
        home_dir = os.path.expanduser("~")
        config_path = os.path.join(home_dir, ".ktra", "config.json")
        
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("model")
    except Exception:
        pass
    return None

def _save_model_setting(model: str) -> bool:
    """設定ファイルにモデル設定を保存します。"""
    try:
        home_dir = os.path.expanduser("~")
        ktra_dir = os.path.join(home_dir, ".ktra")
        os.makedirs(ktra_dir, exist_ok=True)
        
        config_path = os.path.join(ktra_dir, "config.json")
        
        # 既存設定を読み込み
        config = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        
        # モデル設定を更新
        config["model"] = model
        
        # 保存
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception:
        return False

def _change_model(model_name: str) -> str:
    """
    モデルを変更します。
    
    Args:
        model_name: 変更したいモデル名
    
    Returns:
        変更結果のメッセージ
    """
    available_models = get_available_models()
    
    # モデル名の正規化（部分一致も含む）
    matched_model = None
    for model in available_models:
        if model_name.lower() in model.lower() or model.lower() in model_name.lower():
            matched_model = model
            break
    
    if not matched_model:
        available_list = "、".join(available_models)
        return f"❌ モデル '{model_name}' は見つかりませんでした。\n利用可能なモデル: {available_list}"
    
    current_model = get_default_model()
    if matched_model == current_model:
        return f"✅ 既に '{matched_model}' が選択されています。"
    
    if set_default_model(matched_model):
        return f"✅ モデルを '{matched_model}' に変更しました。\n💡 次回の起動から新しいモデルが使用されます。"
    else:
        return f"❌ モデルの変更に失敗しました。"

def _get_current_model() -> str:
    """
    現在のモデル設定を取得します。
    
    Returns:
        現在のモデル情報
    """
    current_model = get_default_model()
    available_models = get_available_models()
    
    model_descriptions = {
        "gpt-3.5-turbo": "高速で効率的、日常的なタスクに最適",
        "gpt-4": "高精度、複雑なタスクに適している", 
        "gpt-4-turbo": "GPT-4の高速版、バランスの取れた性能",
        "gpt-4o": "最新のGPT-4モデル、最高の性能",
        "gpt-4o-mini": "GPT-4oの軽量版、高速で効率的"
    }
    
    description = model_descriptions.get(current_model, "")
    
    result = f"🤖 現在のモデル: {current_model}\n📄 説明: {description}\n\n"
    result += "📋 利用可能なモデル:\n"
    
    for model in available_models:
        marker = "✓ " if model == current_model else "  "
        desc = model_descriptions.get(model, "")
        result += f"{marker}{model} - {desc}\n"
    
    result += "\n💡 モデルを変更するには「モデルを [モデル名] に変更して」と入力してください。"
    
    return result

# Function tools for agent
change_model = function_tool(_change_model)
get_current_model = function_tool(_get_current_model)