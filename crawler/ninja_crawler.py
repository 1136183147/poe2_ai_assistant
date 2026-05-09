# crawler/ninja_crawler.py — POE2 Ninja 爬虫（热门BD + 通货价格）

import json
from crawler._base import fetch_html, safe_text
from utils.memory_manager import save_memory
from config import CRAWLER_URLS

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


def crawl_poe2_ninja() -> str:
    """爬取 POE2 Ninja 热门 BD 排行与价格趋势，全版本适配。"""
    if not HAS_BS4:
        return "❌ 未安装 beautifulsoup4，请执行：pip install beautifulsoup4"

    url  = CRAWLER_URLS["ninja"]
    html = fetch_html(url)
    if html is None:
        return "❌ POE2 Ninja 页面请求失败，请检查网络"

    soup = BeautifulSoup(html, "html.parser")

    # ── 热门 BD ──────────────────────────────────
    builds = []
    build_rows = soup.select("table tbody tr")[:20]   # 取前20条
    for row in build_rows:
        cols = row.select("td")
        if len(cols) < 3:
            continue
        rank  = safe_text(cols[0]) or "-"
        name  = safe_text(cols[1]) or "未知BD"
        usage = safe_text(cols[2]) or "-"
        builds.append({"rank": rank, "name": name, "usage": usage})

    # 若结构解析为空，尝试备用选择器
    if not builds:
        items = soup.select(".build-row, .league-build, [class*='build']")[:20]
        for i, item in enumerate(items, 1):
            name = safe_text(item)[:60]
            if name:
                builds.append({"rank": str(i), "name": name, "usage": "-"})

    # ── 通货价格 ──────────────────────────────────
    prices = {}
    price_items = soup.select(".currency-item, [class*='currency']")[:15]
    for item in price_items:
        name_el  = item.select_one(".currency-name, [class*='name']")
        price_el = item.select_one(".currency-value, [class*='value'], [class*='price']")
        if name_el and price_el:
            prices[safe_text(name_el)] = safe_text(price_el)

    save_memory("meta", "top_builds.json",   builds)
    save_memory("meta", "price_trend.json",  prices)
    return f"✅ POE2 Ninja 已更新：{len(builds)} 条 BD，{len(prices)} 条价格"
