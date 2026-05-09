# crawler/darkcore_crawler.py — 3DM POE2 新闻/攻略爬虫（原暗黑核 d2core.com/poe2/ 已 404）

from datetime import datetime
from crawler._base import fetch_html, safe_text
from utils.memory_manager import save_memory
from config import CRAWLER_URLS

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


def crawl_darkcore() -> str:
    """爬取 3DM POE2 页面新闻与攻略文章（替代已失效的 d2core.com/poe2/）。"""
    if not HAS_BS4:
        return "❌ 未安装 beautifulsoup4"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    url  = CRAWLER_URLS["darkcore"]
    html = fetch_html(url)
    if html is None:
        # 请求失败时保存链接兜底
        content = [
            f"# 3DM POE2 攻略与资讯\n> 最后尝试：{now}\n",
            "⚠️ 自动抓取失败，请手动打开以下链接查看：",
            f"- 3DM POE2 主页：{url}",
            "- POE2 忍者 BD 排行：https://poe.ninja/poe2/builds/",
            "- POE2 编年史：https://poe2db.tw/us/",
        ]
        save_memory("meta", "darkcore_guides.md", "\n\n".join(content))
        return "❌ 3DM POE2 页面请求失败，已保存参考链接"

    soup    = BeautifulSoup(html, "html.parser")
    content = [f"# 3DM POE2 攻略与资讯（自动同步）\n> 更新时间：{now}\n"]

    # 尝试多种选择器提取文章列表
    articles = []
    selectors = [
        ".news-list li a[href]", ".artilelist li a[href]",
        ".newslist li a[href]", "ul.list li a[href]",
        ".g-mn article a[href]", ".news_list li a[href]",
        ".list-con a[href]", ".item a[href]",
        "a[href*='pathofexile2']",
    ]
    for sel in selectors:
        items = soup.select(sel)[:20]
        if items:
            for a_tag in items:
                title = safe_text(a_tag).strip()
                href  = a_tag.get("href", "")
                if title and len(title) > 4:
                    full_url = href if href.startswith("http") else f"https://www.3dmgame.com{href}"
                    articles.append((title, full_url))
            if articles:
                break

    if articles:
        for title, link in articles[:15]:
            content.append(f"## {title}\n🔗 {link}")
    else:
        # 兜底：提取页面中所有带 POE / Path of Exile 的链接
        all_links = soup.select("a[href]")
        poe_links = []
        for a in all_links:
            txt = safe_text(a).strip()
            href = a.get("href", "")
            if txt and ("poe" in txt.lower() or "流放" in txt):
                full_url = href if href.startswith("http") else f"https://www.3dmgame.com{href}"
                poe_links.append((txt, full_url))
        if poe_links:
            for title, link in poe_links[:15]:
                content.append(f"## {title}\n🔗 {link}")
        else:
            content.append("\n⚠️ 未能解析到 POE2 相关文章。")
            content.append(f"请手动访问：{url}")

    save_memory("meta", "darkcore_guides.md", "\n\n".join(content))
    return f"✅ 3DM POE2 已更新：{len(articles)} 条资讯"
