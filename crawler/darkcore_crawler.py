# crawler/darkcore_crawler.py — 3DM POE2 新闻/攻略爬虫（原暗黑核 d2core.com/poe2/ 已 404）

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

    url  = CRAWLER_URLS["darkcore"]
    html = fetch_html(url)
    if html is None:
        return "❌ 3DM POE2 页面请求失败"

    soup    = BeautifulSoup(html, "html.parser")
    content = ["# 3DM POE2 攻略与资讯（自动同步）\n"]

    # 提取新闻/文章列表：3DM 游戏页通常使用 .news-list、.article-list 等
    articles = []
    for sel in [".news-list li", ".artilelist li", ".newslist li",
                "ul.list li", ".g-mn article", ".news_list li"]:
        items = soup.select(sel)[:15]
        if items:
            for item in items:
                a_tag = item.select_one("a[href]")
                if not a_tag:
                    continue
                title = safe_text(a_tag).strip()
                href  = a_tag.get("href", "")
                if title and len(title) > 4:
                    full_url = href if href.startswith("http") else f"https://www.3dmgame.com{href}"
                    articles.append((title, full_url))
            if articles:
                break

    for title, link in articles[:15]:
        content.append(f"## {title}\n链接：{link}")

    if len(content) == 1:
        # 备用：提取页面标题与前 3000 字文字
        body = soup.get_text(separator="\n", strip=True)
        content.append(body[:3000])

    save_memory("meta", "darkcore_guides.md", "\n\n".join(content))
    return f"✅ 3DM POE2 已更新：{len(articles)} 条资讯"
