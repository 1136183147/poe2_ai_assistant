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


def _extract_category_info(text: str, keywords: list[str]) -> str:
    """从爬虫数据中提取分类信息（如装备分类列表）"""
    # 查找包含关键词的章节
    sections = re.split(r'\n## ', text)
    
    for section in sections:
        section_lower = section.lower()
        if any(kw.lower() in section_lower for kw in keywords):
            # 提取该章节的内容
            lines = section.split('\n')
            result_lines = []
            
            # 提取标题
            if lines:
                result_lines.append(f"## {lines[0].strip()}")
            
            # 提取列表项（以 - 或 * 开头，或只有一行文字）
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                # 跳过噪音行
                if len(line) < 3:
                    continue
                # 检查是否是导航垃圾
                if line.lower() in {'wiki', 'edit', 'content', 'available', 'under', 'cc', 'by-nc-sa', 'unless', 'otherwise', 'noted'}:
                    continue
                # 添加到结果
                if line.startswith(('-', '*', '•')) or (any(c.isalpha() for c in line) and len(line) >= 3):
                    result_lines.append(line)
            
            if len(result_lines) > 1:
                return '\n'.join(result_lines)
    
    return ""


def _integrate_results(hits: list[tuple], keywords: list[str]) -> str:
    """整合搜索结果，提供简洁精准的总结"""
    lines = []
    
    # 1. 优先查找 craft 目录下的底材信息（高优先级）
    craft_results = []
    for score, para, fname, cat, urls in hits:
        if cat == "craft" and ("chronicles" in fname or "base" in fname):
            # 提取表格
            tables = _extract_tables(para)
            for table in tables:
                summary = _format_table_summary(table, keywords)
                if summary.strip():
                    source = f"{cat}/{fname}"
                    craft_results.append(('table', source, summary))
            
            # 提取分类信息
            category_info = _extract_category_info(para, keywords)
            if category_info:
                craft_results.append(('category', f"{cat}/{fname}", category_info))
    
    # 2. 如果找到 craft 相关结果，优先显示
    if craft_results:
        for result_type, source, content in craft_results:
            if result_type == 'table':
                lines.append("📊 底材数据：")
                lines.append(f"【{source}】")
                lines.append(content)
                lines.append("")
            elif result_type == 'category':
                lines.append("� 分类信息：")
                lines.append(content)
                lines.append("")
        
        return '\n'.join(lines)
    
    # 3. 如果没有 craft 结果，查找核心机制中的相关表格
    core_tables = []
    for score, para, fname, cat, urls in hits:
        if cat == "core" and fname == "common_mechanic.md":
            tables = _extract_tables(para)
            for table in tables:
                # 只有表格内容包含关键词时才显示
                all_text = ' '.join(table['headers'] + [' '.join(row) for row in table['rows']]).lower()
                if any(kw.lower() in all_text for kw in keywords):
                    summary = _format_table_summary(table, keywords)
                    if summary.strip():
                        core_tables.append(summary)
    
    if core_tables:
        lines.append("📊 相关数据：")
        lines.append("【core/common_mechanic.md】")
        lines.append(core_tables[0])
        return '\n'.join(lines)
    
    # 4. 如果都没有找到，返回简洁提示
    return "暂无相关信息，请尝试其他关键词或配置 LLM API Key 获取更智能的回答。"



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

def _search_equipment(keywords: list[str]) -> list[dict]:
    """搜索装备库中的装备数据"""
    try:
        from memory.equipment_storage import EquipmentStorage
        storage = EquipmentStorage()
        results = []
        
        # 对每个关键词进行搜索
        for kw in keywords:
            equip_list = storage.search_equipment(kw)
            for equip in equip_list:
                if equip not in results:
                    results.append(equip)
        
        return results
    except Exception:
        return []


def _get_price_info(item_name: str, affixes: list = None) -> str:
    """获取装备价格信息"""
    try:
        from price_checker.trade_api import PriceChecker
        
        checker = PriceChecker()
        message, prices = checker.check_price(item_name, affixes=affixes)
        
        if prices and len(prices) > 0:
            # 按价格从低到高排序
            sorted_prices = sorted(prices, key=lambda x: float(x.get('price', float('inf'))))
            
            lines = []
            lines.append("     📊 当前市场价格（从低到高）：")
            
            # 显示前5个最低价格
            for i, price in enumerate(sorted_prices[:5], 1):
                p = price.get('price', 'N/A')
                c = price.get('currency', 'Chaos')
                l = price.get('listing', '')
                lines.append(f"       {i}. {p} {c} - {l}")
            
            return '\n'.join(lines)
        else:
            return f"     ⚠️ 未找到价格数据 - {message}"
    except Exception as e:
        return f"     ⚠️ 价格查询失败: {str(e)[:50]}"


def _format_equipment_results(equipment_list: list[dict]) -> str:
    """格式化装备搜索结果"""
    if not equipment_list:
        return ""
    
    lines = []
    lines.append("🔧 装备库检索结果：\n")
    
    for equip in equipment_list[:3]:  # 最多显示3个
        lines.append(f"【ID: {equip['id']}】{equip['name']}")
        lines.append(f"  ├─ 类型: {equip['type']}")
        lines.append(f"  ├─ 等级: {equip['level']}")
        lines.append(f"  ├─ 稀有度: {equip['rarity']}")
        
        all_affixes = []
        if equip['prefixes']:
            all_affixes.extend(equip['prefixes'])
            lines.append(f"  ├─ 前缀词缀: {', '.join(equip['prefixes'])}")
        if equip['suffixes']:
            all_affixes.extend(equip['suffixes'])
            lines.append(f"  ├─ 后缀词缀: {', '.join(equip['suffixes'])}")
        if equip['properties']:
            props = ', '.join([f"{k}: {v}" for k, v in equip['properties'].items()])
            lines.append(f"  ├─ 属性: {props}")
        
        lines.append(f"  └─ 保存时间: {equip['created_at'][:19]}")
        
        # 添加价格查询结果
        if equip['name']:
            price_info = _get_price_info(equip['name'], all_affixes)
            lines.append(price_info)
        
        lines.append("")
    
    return '\n'.join(lines)


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
    
    # 搜索装备库
    equip_results = _search_equipment(keywords)

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
    
    # 格式化装备库结果
    equip_result_text = _format_equipment_results(equip_results)
    
    # 添加标题和提示
    lines = [f'🔍 本地记忆库检索结果 — 关键词：{" ".join(keywords[:8])}\n']
    lines.append("=" * 50)
    lines.append("")
    
    # 先显示装备库结果
    if equip_result_text:
        lines.append(equip_result_text)
        lines.append("")
    
    # 再显示普通记忆库结果
    if integrated.strip():
        lines.append(integrated)
        lines.append("")
    
    # 如果没有任何结果
    if not equip_result_text and not integrated.strip():
        lines.append(_no_match_response(question, keywords))
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
