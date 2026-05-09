# crawler/poe2_chronicles_crawler.py — POE2 编年史做装数据爬虫

from crawler._base import fetch_html, safe_text
from utils.memory_manager import save_memory
from config import CRAWLER_URLS

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


def crawl_poe2_chronicles_craft() -> str:
    """爬取 POE2 编年史做装数据（底材/词缀/催化剂），全版本适配。"""
    if not HAS_BS4:
        return "❌ 未安装 beautifulsoup4"

    url  = CRAWLER_URLS["chronicles"]
    html = fetch_html(url)
    if html is None:
        return "❌ POE2 编年史请求失败"

    soup    = BeautifulSoup(html, "html.parser")
    content = ["# POE2 编年史做装数据（全版本）\n"]

    # ── 底材数据 ──────────────────────────────────
    content.append("## 一、做装底材大全")
    bases = soup.select(".base-material-item, [class*='base-item'], [class*='material']")[:25]
    for base in bases:
        name_el  = base.select_one(".base-name, [class*='name']")
        level_el = base.select_one(".base-level, [class*='level']")
        stats_el = base.select_one(".base-stats, [class*='stats'], p")
        name  = safe_text(name_el)  or "未知底材"
        level = safe_text(level_el) or "-"
        stats = safe_text(stats_el) or ""
        content.append(f"- **{name}**（需求等级：{level}）：{stats[:100]}")

    # ── 词缀数据 ──────────────────────────────────
    content.append("\n## 二、核心词缀大全")
    affixes = soup.select(".affix-item, [class*='affix']")[:35]
    for affix in affixes:
        name_el   = affix.select_one(".affix-name, [class*='name']")
        effect_el = affix.select_one(".affix-effect, [class*='effect']")
        type_el   = affix.select_one(".affix-type, [class*='type']")
        name   = safe_text(name_el)   or "未知词缀"
        effect = safe_text(effect_el) or ""
        typ    = safe_text(type_el)   or "词缀"
        content.append(f"- {typ}【{name}】：{effect[:120]}")

    # ── 催化剂数据 ──────────────────────────────────
    content.append("\n## 三、催化剂效果")
    catalysts = soup.select(".catalyst-item, [class*='catalyst']")
    for cat in catalysts:
        name_el   = cat.select_one(".catalyst-name, [class*='name']")
        effect_el = cat.select_one(".catalyst-effect, [class*='effect'], p")
        name   = safe_text(name_el)   or "未知催化剂"
        effect = safe_text(effect_el) or ""
        content.append(f"- **{name}**：{effect[:150]}")

    if len(bases) == 0 and len(affixes) == 0:
        body = soup.get_text(separator="\n", strip=True)
        content.append(body[:4000])

    save_memory("craft", "chronicles_craft_data.md", "\n\n".join(content))
    return (f"✅ POE2 编年史已更新："
            f"{len(bases)} 条底材 / {len(affixes)} 条词缀 / {len(catalysts)} 条催化剂")
