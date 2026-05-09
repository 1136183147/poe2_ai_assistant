# crawler/version_crawler.py — 版本更新爬虫（自动爬取新版本机制）

from crawler._base import fetch_html, safe_text
from utils.memory_manager import save_memory, update_version_memory

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# 新增爬虫规则表（可随版本扩展）
_extra_crawlers: list[dict] = []


def add_new_crawler(url: str, filename: str, category: str = "core"):
    """动态添加新版本爬虫规则，无需重启程序。"""
    _extra_crawlers.append({"url": url, "filename": filename, "category": category})
    print(f"✅ 已添加新爬虫规则：{url} → {category}/{filename}")


def crawl_version_patch_notes(version: str) -> str:
    """
    爬取指定版本补丁说明（Patch Notes），存入对应版本记忆。
    URL 格式适配 POE2 官网补丁页面。
    """
    if not HAS_BS4:
        return "❌ 未安装 beautifulsoup4"

    url  = f"https://www.pathofexile2.com/news/patch-notes-{version.replace('.', '-')}"
    html = fetch_html(url)
    if html is None:
        return f"❌ {version} 补丁说明页面请求失败"

    soup    = BeautifulSoup(html, "html.parser")
    content = [f"# POE2 {version} 补丁说明\n"]
    sections = soup.select(".news-article-content p, .patch-notes p, article p")
    for p in sections[:50]:
        text = safe_text(p)
        if text:
            content.append(text)

    full_text = "\n\n".join(content)
    update_version_memory(version, full_text)
    return f"✅ {version} 版本补丁说明已存入记忆（{len(sections)} 段）"


def run_extra_crawlers() -> list[str]:
    """执行所有动态添加的爬虫规则。"""
    if not HAS_BS4:
        return ["❌ 未安装 beautifulsoup4"]
    results = []
    for rule in _extra_crawlers:
        url      = rule["url"]
        filename = rule["filename"]
        category = rule["category"]
        html = fetch_html(url)
        if html is None:
            results.append(f"❌ {url} 请求失败")
            continue
        soup = BeautifulSoup(html, "html.parser")
        body = soup.get_text(separator="\n", strip=True)[:5000]
        save_memory(category, filename, body)
        results.append(f"✅ {url} → {category}/{filename} 已更新")
    return results
