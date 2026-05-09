# ai/local_search.py — 本地记忆搜索引擎（无需 LLM，直接从记忆库检索答案）

import os
import re
import json
from config import MEMORY_ROOT


# ──────────────────────────────────────────────
# 智能整合：识别表格和关键信息
# ──────────────────────────────────────────────

def _extract_tables(text: str) -> list[dict]:
    """从文本中提取 Markdown 表格"""
    tables = []
    
    # 匹配表格块
    table_pattern = r'(\|.*\|\n)+'
    matches = re.finditer(table_pattern, text)
    
    for match in matches:
        table_text = match.group()
        lines = [line.strip() for line in table_text.split('\n') if line.strip()]
        
        if len(lines) < 2:
            continue
        
        # 解析表头
        header_line = lines[0]
        headers = [cell.strip() for cell in header_line.split('|')[1:-1]]
        
        # 解析数据行（跳过分隔行）
        data_rows = []
        for line in lines[1:]:
            if re.match(r'^\|[-\s:|]+\|$', line):  # 分隔行
                continue
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if len(cells) == len(headers):
                data_rows.append(cells)
        
        if data_rows:
            tables.append({
                'headers': headers,
                'rows': data_rows,
                'raw': table_text
            })
    
    return tables


def _format_table_summary(table: dict, keywords: list[str]) -> str:
    """格式化表格摘要，优先显示匹配关键词的行"""
    headers = table['headers']
    rows = table['rows']
    
    # 优先查找精确匹配的行（包含完整关键词）
    matched_rows = []
    for row in rows:
        row_text = ' '.join(row).lower()
        # 检查是否包含任何完整关键词
        if any(kw.lower() in row_text for kw in keywords):
            matched_rows.append(row)
    
    # 如果找到匹配的行，只显示这些行（最多5行）
    if matched_rows:
        # 构建表格
        lines = []
        lines.append('| ' + ' | '.join(headers) + ' |')
        lines.append('|' + '|'.join(['---'] * len(headers)) + '|')
        
        for row in matched_rows[:5]:
            lines.append('| ' + ' | '.join(row) + ' |')
        
        return '\n'.join(lines)
    
    # 如果没有匹配的行，返回空字符串（让其他逻辑处理）
    return ""


def _extract_key_info(text: str, keywords: list[str]) -> list[str]:
    """提取文本中的关键信息片段"""
    key_infos = []
    
    # 按段落分割
    paragraphs = _split_paragraphs(text)
    
    for para in paragraphs:
        # 检查是否包含关键词
        para_lower = para.lower()
        if any(kw.lower() in para_lower for kw in keywords):
            # 提取关键句（包含关键词的句子）
            sentences = re.split(r'[。！？\n]', para)
            for sent in sentences:
                sent = sent.strip()
                if sent and any(kw.lower() in sent.lower() for kw in keywords):
                    # 限制长度
                    if len(sent) <= 100:
                        key_infos.append(sent)
                    else:
                        key_infos.append(sent[:100] + '...')
                    if len(key_infos) >= 5:
                        break
        
        if len(key_infos) >= 5:
            break
    
    return key_infos


def _integrate_results(hits: list[tuple], keywords: list[str]) -> str:
    """整合搜索结果，提供简洁的总结"""
    lines = []
    
    # 1. 首先尝试提取表格（只显示有匹配的表格）
    table_summaries = []
    for score, para, fname, cat, urls in hits:
        tables = _extract_tables(para)
        for table in tables:
            summary = _format_table_summary(table, keywords)
            if summary.strip():  # 只添加有内容的表格
                source = f"{cat}/{fname}" if cat != "." else fname
                table_summaries.append((source, summary))
    
    if table_summaries:
        lines.append("📊 找到相关表格数据：\n")
        for source, summary in table_summaries[:2]:  # 最多显示2个表格
            lines.append(f"【{source}】")
            lines.append(summary)
            lines.append("")
    
    # 2. 提取关键信息（过滤时间戳和表格行）
    key_infos = []
    seen = set()
    for score, para, fname, cat, urls in hits:
        # 跳过 chat_history.json 的内容（避免重复显示搜索历史）
        if fname == "chat_history.json":
            continue
        
        infos = _extract_key_info(para, keywords)
        for info in infos:
            # 过滤时间戳格式的内容
            if info.startswith("time="):
                continue
            # 过滤表格行格式的内容（已在表格中显示）
            if info.startswith("|") and info.endswith("|"):
                continue
            # 去重
            info_key = info[:50]
            if info_key not in seen:
                key_infos.append(info)
                seen.add(info_key)
        
        if len(key_infos) >= 5:
            break
    
    if key_infos:
        lines.append("📌 关键信息：\n")
        for i, info in enumerate(key_infos, 1):
            lines.append(f"{i}. {info}")
        lines.append("")
    
    # 3. 如果表格和关键信息都很少，显示原始检索结果
    if not table_summaries and len(key_infos) < 3:
        lines.append("📋 详细检索结果：\n")
        lines.append("=" * 50)
        
        shown_paras = set()
        count = 0
        for score, para, fname, cat, urls in hits:
            # 跳过 chat_history.json
            if fname == "chat_history.json":
                continue
                
            para_key = para[:80]
            if para_key in shown_paras:
                continue
            shown_paras.add(para_key)
            
            count += 1
            source = f"{cat}/{fname}" if cat != "." else fname
            lines.append(f"\n▎来源：【{source}】（匹配度 ★{'★' * min(score // 3, 3)}）")
            display = para if len(para) <= 400 else para[:400] + "…"
            lines.append(f"{display}")
            
            if count >= 5:
                break
        
        lines.append(f"\n{'=' * 50}")
    
    return '\n'.join(lines)


# ──────────────────────────────────────────────
# 关键词提取（中英文混合，无外部依赖）
# ──────────────────────────────────────────────

# 无意义停用词
_STOP_WORDS = {
    "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "怎么", "什么", "哪", "为", "因为",
    "所以", "可以", "这个", "那个", "哪个", "如何", "为什么", "怎么样",
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
}


def _extract_keywords(text: str) -> list[str]:
    """
    从提问中提取关键词。
    - 中文：提取连续汉字块，再拆成 2-4 字 n-gram（确保能匹配记忆库中的短词）
    - 英文/数字：直接提取
    - 过滤停用词和纯标点
    """
    tokens = []

    # 1. 中文 n-gram 拆分
    for m in re.finditer(r'[\u4e00-\u9fff]+', text):
        block = m.group()
        n = len(block)
        # 短块直接保留
        if n <= 5:
            tokens.append(block)
        # 2-gram
        for i in range(n - 1):
            tokens.append(block[i:i+2])
        # 3-gram
        if n >= 3:
            for i in range(n - 2):
                tokens.append(block[i:i+3])
        # 4-gram
        if n >= 4:
            for i in range(n - 3):
                tokens.append(block[i:i+4])

    # 2. 英文/数字
    for m in re.finditer(r'[a-zA-Z0-9_.]+', text):
        token = m.group().lower().strip('.')
        if token:
            tokens.append(token)

    # 3. 去停用词、去重
    seen = set()
    result = []
    for t in tokens:
        t_lower = t.lower()
        if t_lower in _STOP_WORDS or t_lower in seen:
            continue
        if not any(c.isalpha() or '\u4e00' <= c <= '\u9fff' for c in t):
            continue
        seen.add(t_lower)
        result.append(t)

    return result


# ──────────────────────────────────────────────
# 记忆文件扫描
# ──────────────────────────────────────────────

def _scan_memory_files() -> list[dict]:
    """递归扫描所有记忆文件，返回内容列表。"""
    files = []
    if not os.path.exists(MEMORY_ROOT):
        return files
    for root, dirs, filenames in os.walk(MEMORY_ROOT):
        if "backup" in root.split(os.sep):
            continue
        for fname in filenames:
            if not fname.endswith((".md", ".json", ".txt")):
                continue
            path = os.path.join(root, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw = f.read()
                category = os.path.relpath(root, MEMORY_ROOT)
                if fname.endswith(".json"):
                    try:
                        data = json.loads(raw)
                        raw = _json_to_text(data)
                    except json.JSONDecodeError:
                        pass
                files.append({
                    "path":     path,
                    "filename": fname,
                    "category": category,
                    "content":  raw,
                })
            except Exception:
                pass
    return files


def _json_to_text(data) -> str:
    """把 JSON 数据转成适合搜索的纯文本。"""
    if isinstance(data, dict):
        parts = []
        for k, v in data.items():
            parts.append(f"{k}: {v}")
        return "\n".join(parts)
    if isinstance(data, list):
        parts = []
        for item in data:
            if isinstance(item, dict):
                parts.append(", ".join(f"{k}={v}" for k, v in item.items()))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(data)


# ──────────────────────────────────────────────
# 片段评分与检索
# ──────────────────────────────────────────────

def _split_paragraphs(text: str) -> list[str]:
    """将文本按标题 / 空行拆分为段落。"""
    blocks = re.split(r'\n(?=#{1,3}\s)', text)
    result = []
    for block in blocks:
        block = block.strip()
        if not block or len(block) < 10:
            continue
        if len(block) > 500:
            sub = [s.strip() for s in block.split("\n\n") if len(s.strip()) >= 10]
            result.extend(sub)
        else:
            result.append(block)
    return result


def _score_paragraph(paragraph: str, keywords: list[str]) -> int:
    """根据关键词命中情况打分。标题命中权重更高。"""
    text_lower = paragraph.lower()
    score = 0
    for kw in keywords:
        count = text_lower.count(kw.lower())
        if count > 0:
            if paragraph.startswith("#") and kw.lower() in paragraph.split("\n")[0].lower():
                score += count * 5
            else:
                score += count * 2
    return score


def _find_urls(text: str) -> list[str]:
    """提取文本中的 URL。"""
    urls = re.findall(r'https?://[^\s\n\)\]】]+', text)
    return urls[:5]


# ──────────────────────────────────────────────
# 主搜索函数
# ──────────────────────────────────────────────

def search(question: str, top_k: int = 8) -> str:
    """在本地记忆库中搜索与问题最相关的内容。"""
    keywords = _extract_keywords(question)
    if not keywords:
        return (
            "📭 未能从你的问题中提取到有效关键词。\n"
            "请尝试使用更具体的词语提问，例如：\n"
            "· 「符咒怎么做」\n"
            "· 「做装底材怎么选」\n"
            "· 「0.5赛季有什么新机制」"
        )

    files = _scan_memory_files()
    if not files:
        return "📭 记忆库为空，请先运行爬虫同步资讯，或在悬浮窗中手动喂养内容。"

    # 对每个文件的每个段落打分
    all_hits = []
    for f in files:
        paragraphs = _split_paragraphs(f["content"])
        for para in paragraphs:
            s = _score_paragraph(para, keywords)
            if s > 0:
                urls = _find_urls(para)
                all_hits.append((s, para, f["filename"], f["category"], urls))

    if not all_hits:
        return _no_match_response(question, keywords)

    all_hits.sort(reverse=True, key=lambda x: x[0])

    # 使用智能整合功能
    integrated = _integrate_results(all_hits, keywords)
    
    # 添加标题和提示
    lines = [f'🔍 本地记忆库检索结果 — 关键词：{" ".join(keywords[:8])}\n']
    lines.append("=" * 50)
    lines.append("")
    lines.append(integrated)
    lines.append("")
    lines.append("=" * 50)
    lines.append(
        "💡 以上内容来自本地记忆库搜索。\n"
        "   配置 LLM API Key（config.py）后可获得更智能的整合回答。\n"
        "   你也可以通过「记录：<内容>」指令手动喂养新知识。"
    )
    return "\n".join(lines)


def _no_match_response(question: str, keywords: list[str]) -> str:
    """无匹配时的友好提示。"""
    return (
        f'📭 本地记忆库中未找到与 "{question[:40]}" 相关的内容。\n\n'
        "可能的原因：\n"
        "1. 记忆库尚未同步 —— 点击悬浮窗「立即爬取」按钮同步资讯\n"
        "2. 相关资讯未被收录 —— 用「记录：<你的发现>」手动喂养\n"
        "3. 问题关键词不够精确 —— 尝试换一种问法\n\n"
        f"已提取关键词：{'、'.join(keywords[:8])}\n\n"
        "💡 提示：如果配置了 LLM API Key（config.py），AI 可以直接联网推理回答。"
    )


# ──────────────────────────────────────────────
# 快捷入口
# ──────────────────────────────────────────────

def quick_answer(question: str) -> str:
    """给 llm_engine 调用的快捷接口。"""
    return search(question)
