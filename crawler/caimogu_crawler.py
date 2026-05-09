# crawler/caimogu_crawler.py — 踩蘑菇社区爬虫

from datetime import datetime
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

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    url = CRAWLER_URLS["caimogu"]
    html = fetch_html(url)
    if html is None:
        content = [
            f"# 踩蘑菇社区讨论\n> 最后尝试：{now}\n",
            "⚠️ 自动抓取失败，请手动打开：",
            f"- 踩蘑菇 POE2 圈子：{url}",
        ]
        save_memory("meta", "caimogu_discuss.md", "\n\n".join(content))
        return "❌ 踩蘑菇页面请求失败，已保存参考链接"

    soup    = BeautifulSoup(html, "html.parser")
    content = [f"# 踩蘑菇社区讨论（自动同步）\n> 更新时间：{now}\n"]

    # 提取帖子标题和链接
    posts = []
    # 尝试多种选择器
    for sel in [
        ".post a[href]", ".topic a[href]", ".thread a[href]",
        "[class*='post'] a[href]", "[class*='topic'] a[href]",
        ".post-list a[href]", ".list-item a[href]",
    ]:
        items = soup.select(sel)[:15]
        if items:
            for a_tag in items:
                title = safe_text(a_tag).strip()
                href  = a_tag.get("href", "")
                if title and len(title) > 4:
                    full_url = href if href.startswith("http") else f"https://www.caimogu.cc{href}"
                    posts.append((title, full_url))
            if posts:
                break

    if posts:
        for title, link in posts[:15]:
            content.append(f"### {title}\n🔗 {link}")
    else:
        # 兜底：保存源链接
        content.append(f"\n⚠️ 未能解析到帖子列表。请手动访问：{url}")
        content.append(f"\n备用链接：{url}")

    save_memory("meta", "caimogu_discuss.md", "\n\n".join(content))
    return f"✅ 踩蘑菇已更新：{len(posts)} 条讨论"
