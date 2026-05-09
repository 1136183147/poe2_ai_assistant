# crawler/poe2_official_crawler.py — POE2 官网做装指南爬虫

from crawler._base import fetch_html, safe_text
from utils.memory_manager import save_memory
from config import CRAWLER_URLS

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


def crawl_poe2_official_craft() -> str:
    """爬取 POE2 官网做装指南，全版本适配，自动同步版本更新。"""
    if not HAS_BS4:
        return "❌ 未安装 beautifulsoup4"

    url  = CRAWLER_URLS["official"]
    html = fetch_html(url)
    if html is None:
        return "❌ POE2 官网请求失败"

    soup    = BeautifulSoup(html, "html.parser")
    content = ["# POE2 官方做装指南（自动同步）\n"]

    # 提取页面标题
    h1 = soup.select_one("h1, .title, [class*='hero'] h2")
    if h1:
        content[0] = f"# {safe_text(h1)}\n"

    # 提取各章节（适配 /poe2 页面结构）
    sections = soup.select("section, article, .feature, [class*='section'], [class*='content'], [class*='block']")
    for sec in sections[:12]:
        h = sec.select_one("h2, h3, h4")
        p = sec.select_one("p, li")
        sec_title   = safe_text(h) or ""
        sec_content = safe_text(p) or ""
        if sec_title and sec_title not in [s.split("\n")[0].lstrip("# ") for s in content]:
            content.append(f"## {sec_title}\n{sec_content[:400]}")

    if len(content) == 1:
        body = soup.get_text(separator="\n", strip=True)
        content.append(body[:4000])

    save_memory("craft", "offical_craft_guide.md", "\n\n".join(content))
    return f"✅ POE2 官网做装指南已更新（{len(sections)} 章节）"
