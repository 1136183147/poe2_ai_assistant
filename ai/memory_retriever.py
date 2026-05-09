# ai/memory_retriever.py — 记忆检索（自动匹配当前版本 + 个人专属记忆）

from config import CURRENT_VERSION

_current_version = CURRENT_VERSION   # 运行时版本，可动态切换


def get_current_version() -> str:
    return _current_version


def set_version_priority(version: str):
    global _current_version
    _current_version = version
    print(f"✅ 记忆检索已切换至 {version} 版本优先")


def retrieve_context(question: str) -> dict:
    """
    根据当前版本，从记忆库中检索所有相关上下文，
    返回字典供 llm_engine 组装 Prompt 使用。
    """
    from utils.memory_manager import load_memory

    ver = _current_version

    # 1. 版本记忆
    version_info      = load_memory("core", f"version_{ver}.md",      version=ver)
    user_version_info = load_memory("core", f"user_version_{ver}.md", version=ver)
    common_mechanic   = load_memory("core", "common_mechanic.md")
    new_classes       = load_memory("core", "new_classes_all.md")

    # 2. 做装记忆
    ace_craft        = load_memory("craft", "ace_craft_guide.md")
    official_craft   = load_memory("craft", "offical_craft_guide.md")
    chronicles_craft = load_memory("craft", "chronicles_craft_data.md")
    base_select      = load_memory("craft", "base_select.md")
    prefix_suffix    = load_memory("craft", "prefix_suffix.md")

    # 3. Meta 资讯
    top_builds   = load_memory("meta", "top_builds.json")
    price_trend  = load_memory("meta", "price_trend.json")
    darkcore     = load_memory("meta", "darkcore_guides.md")
    caimogu      = load_memory("meta", "caimogu_discuss.md")

    # 4. 个人专属
    user_notes      = load_memory("user", "version_notes.md")
    craft_notes     = load_memory("user", "craft_notes.md")
    favorite_builds = load_memory("user", "favorite_builds.md")

    # 5. 关键字匹配——仅返回与问题相关的片段（减少 Token）
    def _clip(text, limit=800):
        return str(text)[:limit] if text else ""

    return {
        "version":           ver,
        "version_info":      _clip(version_info,      2000),
        "user_version_info": _clip(user_version_info, 2000),
        "common_mechanic":   _clip(common_mechanic,    500),
        "new_classes":       _clip(new_classes,        500),
        "ace_craft":         _clip(ace_craft,         1000),
        "official_craft":    _clip(official_craft,     800),
        "chronicles_craft":  _clip(chronicles_craft,   800),
        "base_select":       _clip(base_select,        400),
        "prefix_suffix":     _clip(prefix_suffix,      400),
        "top_builds":        _clip(top_builds,         500),
        "price_trend":       _clip(price_trend,        300),
        "darkcore":          _clip(darkcore,           400),
        "caimogu":           _clip(caimogu,            400),
        "user_notes":        _clip(user_notes,         600),
        "craft_notes":       _clip(craft_notes,        400),
        "favorite_builds":   _clip(favorite_builds,    300),
    }
