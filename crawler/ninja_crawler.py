# crawler/ninja_crawler.py — POE2 Ninja 爬虫（热门BD + 通货价格）

import json
from datetime import datetime
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

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    url  = CRAWLER_URLS["ninja"]
    html = fetch_html(url)
    if html is None:
        # 请求失败时保存链接兜底
        content = {
            "_meta": {
                "last_attempt": now,
                "source_url": url,
                "note": "自动抓取失败，请手动访问网站查看",
            },
            "reference_links": [
                {"name": "POE2 Ninja Builds", "url": url},
                {"name": "POE2 Ninja Economy", "url": "https://poe.ninja/poe2/economy/"},
            ],
        }
        save_memory("meta", "top_builds.json", content)
        save_memory("meta", "price_trend.json", {"_meta": {"last_attempt": now, "note": "抓取失败"}})
        return "❌ POE2 Ninja 请求失败，已保存参考链接"

    soup = BeautifulSoup(html, "html.parser")

    # ── 热门 BD ──
    builds = []
    # 尝试多种表格选择器
    for table_sel in ["table tbody tr", ".build-table tr", "[class*='build'] tr", ".table tr"]:
        rows = soup.select(table_sel)
        if rows:
            for row in rows[:25]:
                cols = row.select("td, th")
                if len(cols) >= 2:
                    rank  = safe_text(cols[0]) or "-"
                    name  = safe_text(cols[1]) or "未知BD"
                    usage = safe_text(cols[2]) if len(cols) > 2 else "-"
                    builds.append({"rank": rank, "name": name, "usage": usage})
            if builds:
                break

    # 备用：从页面找所有含 build 的文本块
    if not builds:
        for item in soup.select(".build-row, .league-build, [class*='build']")[:20]:
            text = safe_text(item)[:80]
            if text and len(text) > 5:
                builds.append({"rank": "-", "name": text, "usage": "-"})

    # ── 通货价格 ──
    prices = {}
    for item in soup.select(".currency-item, [class*='currency'], .price-row")[:20]:
        name_el  = item.select_one(".currency-name, [class*='name'], td:first-child")
        price_el = item.select_one(".currency-value, [class*='value'], [class*='price'], td:last-child")
        if name_el and price_el:
            prices[safe_text(name_el)] = safe_text(price_el)

    # 兜底：存入源链接
    if not builds:
        builds = [{"rank": "⚠️", "name": "未能解析 BD 数据", "usage": f"请手动访问：{url}"}]
    if not prices:
        prices = {"⚠️": f"未能解析价格数据，请访问 {url}"}

    save_memory("meta", "top_builds.json", builds)
    save_memory("meta", "price_trend.json", {
        "_last_update": now,
        "_source": url,
        "prices": prices,
    })
    return f"✅ POE2 Ninja 已更新：{len(builds)} 条 BD，{len(prices)} 条价格"
