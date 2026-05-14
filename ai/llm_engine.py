# ai/llm_engine.py — AI 对话核心（调用 LLM，结合当前版本记忆回答）

import os
import json
import urllib.request
import urllib.error
from config import LLM_PROVIDER, LLM_CONFIG


# ──────────────────────────────────────────────
# LLM 调用（兼容 OpenAI 接口格式）
# ──────────────────────────────────────────────

def _has_valid_api_key() -> bool:
    """检查是否已配置有效的 API Key。"""
    cfg = LLM_CONFIG.get(LLM_PROVIDER, {})
    api_key = cfg.get("api_key", "")
    return bool(api_key) and not api_key.startswith("YOUR_")


def _llm_call(prompt: str) -> str:
    """
    调用 LLM 接口。支持 DeepSeek / 通义千问 / OpenAI（均兼容 OpenAI 格式）。
    注意：调用方应先通过 _has_valid_api_key() 判断再调用。
    """
    cfg = LLM_CONFIG.get(LLM_PROVIDER, {})
    api_key  = cfg.get("api_key", "")
    base_url = cfg.get("base_url", "")
    model    = cfg.get("model", "")
    max_tok  = cfg.get("max_tokens", 1500)

    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tok,
        "temperature": 0.7,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"LLM HTTP {e.code}：{body[:200]}")
    except Exception as e:
        raise RuntimeError(f"LLM 调用异常：{e}")


# ──────────────────────────────────────────────
# Prompt 构建
# ──────────────────────────────────────────────

def _build_prompt(question: str, ctx: dict) -> str:
    ver = ctx.get("version", "0.5")
    return f"""你是 POE2 全版本专属 AI 游戏助手，可适配所有版本，当前适配版本：{ver}。
优先参考用户个人总结的该版本细节，再结合当前版本实时资讯、官方做装指南、编年史数据，给出具体可操作的建议。
语言接地气，符合 POE 玩家交流习惯，区分国服/国际服差异。

【用户个人总结的 {ver} 赛季细节（最高优先级）】
{ctx.get("user_version_info") or "暂无个人总结，参考官方版本细节"}

【用户个人笔记 / 经验】
{ctx.get("user_notes") or "暂无"}

【当前版本官方机制】
{ctx.get("version_info") or "暂无"}

【通用机制 / 职业信息】
{ctx.get("common_mechanic", "")}
{ctx.get("new_classes", "")}

【做装攻略】
· 抖音 Ace 最新做装：{ctx.get("ace_craft") or "暂无"}
· POE2 官网正统指南：{ctx.get("official_craft") or "暂无"}
· POE2 编年史数据：{ctx.get("chronicles_craft") or "暂无"}
· 底材选择：{ctx.get("base_select") or "暂无"}
· 词缀优先级：{ctx.get("prefix_suffix") or "暂无"}
· 用户做装心得：{ctx.get("craft_notes") or "暂无"}

【当前版本热门 BD（POE2 Ninja）】
{ctx.get("top_builds") or "暂无"}

【当前版本物价趋势】
{ctx.get("price_trend") or "暂无"}

【社区资讯】
· 暗黑核：{ctx.get("darkcore") or "暂无"}
· 踩蘑菇：{ctx.get("caimogu") or "暂无"}

【用户收藏 BD】
{ctx.get("favorite_builds") or "暂无"}

用户问题：{question}

回答要求：
1. 优先结合用户个人总结的细节（若有），再补充当前版本实时资讯；
2. 区分国服/国际服差异，给出对应建议；
3. 语言简洁，重点突出，优先给具体操作建议；
4. 若询问历史版本内容，准确回复并注明版本；
5. 涉及做装，优先官网正统教程 + 编年史数据，补充 Ace 实操技巧。"""


# ──────────────────────────────────────────────
# 对外接口
# ──────────────────────────────────────────────

def _fetch_from_web(question: str) -> str | None:
    """
    优先从网上获取最新信息，根据问题意图返回有意义的答案
    返回：获取到的信息（字符串），如果获取失败或无相关信息则返回 None
    """
    try:
        from crawler.poe2_chronicles_crawler import search_equipment, search_skill, get_base_items
        
        # 分析问题意图
        intent = _analyze_question_intent(question)
        
        if intent == "base_items":
            # 用户想了解装备底材列表
            return _get_base_items_info(question)
            
        elif intent == "equipment_detail":
            # 用户想了解特定装备详情
            result = search_equipment(question)
            if result and "未找到" not in result:
                return f"🌐 装备查询结果：\n\n{_format_equipment_result(result, question)}"
        
        elif intent == "skill_info":
            # 用户想了解技能/天赋
            result = search_skill(question)
            if result and "未找到" not in result:
                return f"🌐 技能查询结果：\n\n{result}"
        
        elif intent == "crafting_info":
            # 用户想了解做装相关
            return _get_crafting_info(question)
        
        # 默认：尝试通用搜索
        if "底材" in question or "装备" in question or "基底" in question:
            result = search_equipment(question)
            if result and "未找到" not in result:
                return f"🌐 搜索结果：\n\n{_format_search_result(result, question)}"
        
        if "技能" in question or "天赋" in question:
            result = search_skill(question)
            if result and "未找到" not in result:
                return f"🌐 搜索结果：\n\n{result}"
        
    except Exception as e:
        print(f"⚠️ 网络搜索失败：{e}")
    
    return None


def _analyze_question_intent(question: str) -> str:
    """分析问题意图"""
    # 底材列表相关
    if any(kw in question for kw in ["底材列表", "有什么底材", "底材有哪些", "获取底材", "装备底材"]):
        return "base_items"
    
    # 装备详情相关
    if any(kw in question for kw in ["装备详情", "装备属性", "装备介绍", "装备数据"]):
        return "equipment_detail"
    
    # 技能/天赋相关
    if any(kw in question for kw in ["技能介绍", "技能属性", "天赋树", "天赋点"]):
        return "skill_info"
    
    # 做装相关
    if any(kw in question for kw in ["做装", "打造", "工艺", "词缀"]):
        return "crafting_info"
    
    return "general"


def _get_base_items_info(question: str) -> str:
    """获取装备底材信息"""
    # 提取关键词
    keywords = []
    if "剑" in question:
        keywords.append("剑")
    elif "法杖" in question:
        keywords.append("法杖")
    elif "护甲" in question:
        keywords.append("护甲")
    elif "首饰" in question:
        keywords.append("首饰")
    elif "武器" in question:
        keywords.append("武器")
    
    # 构建底材信息
    base_items_info = {
        "剑": {
            "类别": "武器",
            "常见底材": ["长剑", "双手剑", "细剑", "巨剑", "军刀"],
            "属性特点": "高物理伤害，中等攻速",
            "适用BD": "近战物理、流血、暴击",
        },
        "法杖": {
            "类别": "武器",
            "常见底材": ["法杖", "长杖", "权杖", "魔杖"],
            "属性特点": "高法术伤害，低攻速",
            "适用BD": "元素法术、召唤、诅咒",
        },
        "护甲": {
            "类别": "防具",
            "常见底材": ["胸甲", "头盔", "手套", "靴子", "腰带"],
            "属性特点": "提供防御、抗性、生命",
            "适用BD": "所有BD，尤其生存向",
        },
        "首饰": {
            "类别": "饰品",
            "常见底材": ["戒指", "项链", "护身符"],
            "属性特点": "提供多种属性加成",
            "适用BD": "所有BD",
        },
        "武器": {
            "类别": "武器",
            "常见底材": ["剑", "斧", "锤", "弓", "匕首", "爪", "长矛"],
            "属性特点": "提供攻击伤害",
            "适用BD": "近战、远程、法术",
        },
    }
    
    if keywords:
        key = keywords[0]
        if key in base_items_info:
            info = base_items_info[key]
            return f"## {key}底材信息\n\n" \
                   f"**类别**: {info['类别']}\n\n" \
                   f"**常见底材**:\n" \
                   + "\n".join(f"- {item}" for item in info['常见底材']) + "\n\n" \
                   f"**属性特点**: {info['属性特点']}\n\n" \
                   f"**适用BD**: {info['适用BD']}\n\n" \
                   f"🔗 详细数据：https://poe2db.tw/us/Items"
    else:
        # 返回所有底材概览
        result = "## 装备底材分类概览\n\n"
        for category, info in base_items_info.items():
            result += f"### {category}\n"
            result += f"- 类别: {info['类别']}\n"
            result += f"- 常见底材: {', '.join(info['常见底材'][:3])}...\n\n"
        result += "🔗 完整数据请访问：https://poe2db.tw/us/Items"
        return result


def _format_search_result(result: str, question: str) -> str:
    """格式化搜索结果，使其更有意义"""
    # 如果结果太简短，添加更多上下文
    lines = [line for line in result.split('\n') if line.strip()]
    
    # 如果结果只是简单列表，添加解释
    if len(lines) <= 10 and all(line.startswith('- ') for line in lines[1:]):
        return f"根据你的问题「{question}」，找到以下相关信息：\n\n" + result + "\n\n💡 提示：如需更详细的信息，可以问具体的装备名称或类型。"
    
    return result


def _format_equipment_result(result: str, question: str) -> str:
    """格式化装备搜索结果"""
    return result + "\n\n💡 提示：你可以进一步询问该装备的属性、获取方式或配装建议。"


def answer_question(question: str) -> str:
    """
    核心对话函数：
    - 优先从网上获取最新信息
    - 有 LLM → 检索记忆 → 构建 Prompt → 调用 LLM
    - 无 LLM → 直接从本地记忆库搜索相关内容回答
    """
    from ai.memory_retriever import retrieve_context
    from utils.memory_manager import save_chat_history

    # ── 优先：从网上获取最新信息 ──
    web_result = _fetch_from_web(question)
    if web_result:
        save_chat_history(question, web_result)
        return web_result

    # ── 离线模式：用本地搜索引擎直接回答 ──
    if not _has_valid_api_key():
        try:
            from ai.local_search import quick_answer
            response = quick_answer(question)
        except Exception as e:
            response = f"❌ 本地搜索失败：{e}"
        save_chat_history(question, response)
        return response

    # ── 在线模式：走 LLM ──
    ctx = retrieve_context(question)
    prompt = _build_prompt(question, ctx)
    try:
        response = _llm_call(prompt)
    except Exception as e:
        # LLM 调用失败时也降级到本地搜索
        try:
            from ai.local_search import quick_answer
            response = (
                f"⚠️ LLM 调用失败（{e}），已自动切换为本地记忆库搜索：\n\n"
                f"{quick_answer(question)}"
            )
        except Exception:
            response = f"❌ LLM 调用失败且本地搜索不可用：{e}"

    save_chat_history(question, response)
    return response


# 为了向后兼容，添加别名 ask_ai
ask_ai = answer_question


def handle_special_command(text: str) -> str | None:
    """
    识别并处理特殊指令（无需调用 LLM）：
      - "初始化[版本号]赛季总结：内容"
      - "收藏BD：内容"
      - "做装心得：内容"
      - "查价 <装备名称>"
    返回处理结果字符串，若非指令则返回 None。
    """
    from utils.memory_manager import (
        init_user_version_memory, add_favorite_build,
        add_craft_note, add_user_note
    )
    from ai.memory_retriever import get_current_version
    from config import LLM_CONFIG, LLM_PROVIDER

    # 模型信息查询（宽松匹配）
    if "版本" in text:
        # 检查是否是询问模型/助手版本
        if ("你" in text or "助手" in text or "模型" in text or "AI" in text):
            llm_config = LLM_CONFIG.get(LLM_PROVIDER, {})
            return (
                f"🎮 当前配置：\n"
                f"· 模型: {LLM_PROVIDER}\n"
                f"· 具体型号: {llm_config.get('model', '未知')}\n"
                f"· 支持版本: {get_current_version()}\n"
                f"· 状态: {'已配置API Key' if llm_config.get('api_key', '').strip() and not llm_config.get('api_key', '').startswith('YOUR_') else '未配置API Key'}"
            )

    if text.startswith("初始化") and "赛季总结：" in text:
        parts   = text.split("赛季总结：", 1)
        version = parts[0].replace("初始化", "").strip().lstrip("v").strip()
        content = parts[1].strip()
        init_user_version_memory(version=version, content=content)
        return f"✅ 已将 {version} 赛季个人总结存入专属记忆"

    if text.startswith("收藏BD："):
        build = text[len("收藏BD："):].strip()
        add_favorite_build(build)
        return "✅ 已将 BD 收藏到你的专属列表"

    if text.startswith("做装心得："):
        note = text[len("做装心得："):].strip()
        add_craft_note(note)
        return "✅ 已将做装心得存入个人记忆"

    if text.startswith("记录：") or text.startswith("笔记："):
        note = text.split("：", 1)[1].strip()
        add_user_note(note, version=get_current_version())
        return "✅ 已将你的新发现存入个人记忆"

    # 查价指令
    if text.startswith("查价 ") or text.startswith("价格 ") or text.startswith("price "):
        item_name = text.split(" ", 1)[1].strip()
        if not item_name:
            return "❌ 请输入装备名称，例如：查价 Exalted Orb"
        
        try:
            from price_checker.trade_api import quick_check
            return quick_check(item_name)
        except ImportError:
            return "❌ 查价器模块未加载"
        except Exception as e:
            return f"❌ 查价失败：{e}"

    return None


# ── 对话历史管理 ──────────────────────────────
_chat_history: list = []
_MAX_HISTORY = 10

def clear_chat_history():
    """清空多轮对话历史"""
    global _chat_history
    _chat_history = []
