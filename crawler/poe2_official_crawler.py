# crawler/poe2_official_crawler.py — POE2 官网做装指南爬虫

from datetime import datetime
from crawler._base import fetch_html, safe_text
from utils.memory_manager import save_memory
from config import CRAWLER_URLS

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


def crawl_poe2_official_craft() -> str:
    """爬取 POE2 官网做装指南（官网依赖 JS，可能抓不到内容）。"""
    if not HAS_BS4:
        return "❌ 未安装 beautifulsoup4"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    url  = CRAWLER_URLS["official"]
    html = fetch_html(url)
    if html is None:
        content = [
            f"# POE2 官方做装指南\n> 最后尝试：{now}\n",
            "⚠️ 自动抓取失败，请手动打开：",
            f"- POE2 官网：{url}",
            "- POE2 编年史做装：https://poe2db.tw/us/Crafting",
            "- POE2 Wiki：https://www.poewiki.net/wiki/Path_of_Exile_2",
        ]
        save_memory("craft", "offical_craft_guide.md", "\n\n".join(content))
        return "❌ POE2 官网请求失败，已保存参考链接"

    soup    = BeautifulSoup(html, "html.parser")
    content = [f"# POE2 官方做装指南（自动同步）\n> 更新时间：{now}\n"]

    # 官网通常需要 JS 渲染，先尝试提取内容
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    # 提取各章节
    sections = soup.select("section, article, .feature, [class*='section'], [class*='content'], [class*='block']")
    found = 0
    for sec in sections[:12]:
        h = sec.select_one("h2, h3, h4")
        p = sec.select_one("p, li")
        sec_title   = safe_text(h) or ""
        sec_content = safe_text(p) or ""
        if sec_title and sec_title not in [s.split("\n")[0].lstrip("# ") for s in content]:
            content.append(f"## {sec_title}\n{sec_content[:400]}")
            found += 1

    if found == 0:
        # 抓不到结构化内容
        body = soup.get_text(separator="\n", strip=True)
        # 检查是否是 "JavaScript required" 之类
        if "javascript" in body.lower() or "enable javascript" in body.lower():
            content.append("\n⚠️ POE2 官网需要 JavaScript 渲染，无法自动抓取。")
            content.append("\n## 重要参考链接（可手动打开）")
            content.append(f"- POE2 官网主页：{url}")
            content.append("- POE2 编年史（做装数据）：https://poe2db.tw/us/Crafting")
            content.append("- POE2 Wiki：https://www.poewiki.net/wiki/Path_of_Exile_2")
            content.append("- POE2 忍者（BD排行）：https://poe.ninja/poe2/builds/")
        else:
            # 清理并保存部分文本
            lines = [l.strip() for l in body.split("\n") if len(l.strip()) > 10]
            content.append("\n".join(lines[:150]))

    save_memory("craft", "offical_craft_guide.md", "\n\n".join(content))
    return f"✅ POE2 官网做装指南已更新（{found} 章节）"
