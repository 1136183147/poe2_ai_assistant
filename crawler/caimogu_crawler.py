# crawler/caimogu_crawler.py — 踩蘑菇社区爬虫

from crawler._base import fetch_html, safe_text
from utils.memory_manager import save_memory
from config import CRAWLER_URLS

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


def crawl_caimogu() -> str:
    """爬取踩蘑菇社区 POE2 玩家讨论与机制解析。"""
    if not HAS_BS4:
        return "❌ 未安装 beautifulsoup4"

    url  = CRAWLER_URLS["caimogu"]
    html = fetch_html(url)
    if html is None:
        return "❌ 踩蘑菇页面请求失败"

    soup    = BeautifulSoup(html, "html.parser")
    content = ["# 踩蘑菇社区讨论（自动同步）\n"]

    posts = soup.select(".post, .topic, .thread, [class*='post'], [class*='topic']")[:15]
    for post in posts:
        title_el = post.select_one("h1, h2, h3, a[href], .title")
        body_el  = post.select_one("p, .content, .body")
        title = safe_text(title_el) or ""
        body  = safe_text(body_el)  or ""
        if title:
            content.append(f"### {title}\n{body[:200]}")

    if len(content) == 1:
        body = soup.get_text(separator="\n", strip=True)
        content.append(body[:3000])

    save_memory("meta", "caimogu_discuss.md", "\n\n".join(content))
    return f"✅ 踩蘑菇已更新：{len(posts)} 条讨论"
