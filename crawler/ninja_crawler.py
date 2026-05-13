# crawler/ninja_crawler.py — POE2 Ninja 爬虫（热门BD + 通货价格）

import json
from datetime import datetime
from crawler._base import fetch_html, safe_text, validate_data, extract_text_with_fallback
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
    html, status = fetch_html(url)
    
    if html is None:
        # 请求失败时保存链接兜底
        content = {
            "_meta": {
                "last_attempt": now,
                "source_url": url,
                "note": f"自动抓取失败（{status}），请手动访问网站查看",
            },
            "reference_links": [
                {"name": "POE2 Ninja Builds", "url": url},
                {"name": "POE2 Ninja Economy", "url": "https://poe.ninja/poe2/economy/"},
            ],
        }
        save_memory("meta", "top_builds.json", content)
        save_memory("meta", "price_trend.json", {"_meta": {"last_attempt": now, "note": status}})
        return f"❌ POE2 Ninja {status}，已保存参考链接"

    soup = BeautifulSoup(html, "html.parser")

    # ── 热门 BD ──
    builds = []
    
    # 尝试多种表格选择器（按优先级）
    table_selectors = [
        "table.builds-table tbody tr",
        "table.table tbody tr",
        ".build-table tr",
        "[class*='build'] tr",
        ".table tr",
    ]
    
    for table_sel in table_selectors:
        rows = soup.select(table_sel)
        if rows and len(rows) > 2:
            for row in rows[:25]:
                cols = row.select("td, th")
                if len(cols) >= 2:
                    rank  = extract_text_with_fallback(cols[0], ["span", "div", "a"], "-")
                    name  = extract_text_with_fallback(cols[1], ["a", "span", "div"], "未知BD")
                    usage = extract_text_with_fallback(cols[2], ["span", "div"], "-") if len(cols) > 2 else "-"
                    
                    # 验证数据有效性
                    if name and len(name) > 3 and name not in ["Rank", "Name", "Usage", "排名", "名称"]:
                        builds.append({"rank": rank, "name": name.strip(), "usage": usage})
            if builds:
                break

    # 备用：从页面找所有含 build 的文本块
    if not builds:
        build_elements = soup.select(".build-row, .league-build, [class*='build'], .build-item")[:20]
        for item in build_elements:
            text = safe_text(item)[:80]
            if text and len(text) > 5 and not text.isdigit():
                builds.append({"rank": "-", "name": text.strip(), "usage": "-"})

    # ── 通货价格 ──
    prices = {}
    currency_selectors = [
        ".currency-item", 
        "[class*='currency']", 
        ".price-row",
        ".item-row",
    ]
    
    for selector in currency_selectors:
        items = soup.select(selector)[:30]
        if items:
            for item in items:
                name_selectors = [".currency-name", "[class*='name']", "td:first-child", ".item-name"]
                price_selectors = [".currency-value", "[class*='value']", "[class*='price']", "td:last-child", ".item-price"]
                
                name = extract_text_with_fallback(item, name_selectors)
                price = extract_text_with_fallback(item, price_selectors)
                
                if name and price and len(name) > 2 and len(price) > 0:
                    # 过滤无效数据
                    if name not in ["Name", "Currency", "通货", "名称"]:
                        prices[name.strip()] = price.strip()
            if prices:
                break

    # 数据验证
    builds_valid, builds_msg = validate_data(builds, min_items=3)
    prices_valid, prices_msg = validate_data(prices, min_items=5)

    # 兜底：存入源链接
    if not builds_valid:
        print(f"⚠️ BD 数据验证失败：{builds_msg}")
        builds = [{"rank": "⚠️", "name": f"未能解析 BD 数据（{builds_msg}）", "usage": f"请手动访问：{url}"}]
    
    if not prices_valid:
        print(f"⚠️ 价格数据验证失败：{prices_msg}")
        prices = {"⚠️": f"未能解析价格数据（{prices_msg}），请访问 {url}"}

    save_memory("meta", "top_builds.json", {
        "_last_update": now,
        "_source": url,
        "_status": "valid" if builds_valid else "invalid",
        "builds": builds,
    })
    
    save_memory("meta", "price_trend.json", {
        "_last_update": now,
        "_source": url,
        "_status": "valid" if prices_valid else "invalid",
        "prices": prices,
    })
    
    return f"✅ POE2 Ninja 已更新：{len(builds)} 条 BD（{builds_msg}），{len(prices)} 条价格（{prices_msg}）"
