# crawler/poe2_chronicles_crawler.py — POE2 编年史做装数据爬虫

from datetime import datetime
from crawler._base import fetch_html
from utils.memory_manager import save_memory
from config import CRAWLER_URLS

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# 编年史各子页面（均为 Wiki 页面，优先爬取数据型页面）
CHRONICLES_PAGES = {
    "modifiers": "https://poe2db.tw/us/Modifiers",
    "items":     "https://poe2db.tw/us/Items",
    "gems":      "https://poe2db.tw/us/Gems",
    "crafting":  "https://poe2db.tw/us/Crafting",
}


def _crawl_page(url: str, section_title: str) -> str:
    """爬取单个编年史子页面的有效文本。"""
    html = fetch_html(url)
    if html is None:
        return f"## {section_title}\n❌ 请求失败\n"

    soup = BeautifulSoup(html, "html.parser")

    # 移除噪音标签
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # 优先取主内容区
    main = soup.select_one("main, article, .content, #content, .main-content")
    source = main if main else soup
    text = source.get_text(separator="\n", strip=True)

    # 清理：去除导航垃圾（极短行、纯导航词）
    _NAV_JUNK = {
        "home", "db", "tw 正體中文", "cn 简体中文", "us english",
        "poe2", "poe", "item", "gem", "modifiers", "crafting",
        "quest", "economy", "patreon", "stash tab", "sales",
        "unique", "currency", "build planner", "update cookie preferences",
        "kr 한국어", "jp japanese", "ru Русский", "po português",
        "th ภาษาไทย", "fr français", "de deutsch", "es spanish",
        "ascendancy classes", "passive skill tree", "waystones",
        "fragment stash tab",
    }
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if len(line) < 4 and not line.startswith(("#", "-", "*", "•")):
            continue
        if line.lower() in _NAV_JUNK:
            continue
        # 跳过纯数字/纯标点行
        if len(line) <= 6 and not any(c.isalpha() for c in line):
            continue
        lines.append(line)

    result = f"## {section_title}\n" + "\n".join(lines[:250])
    return result


def crawl_poe2_chronicles_craft() -> str:
    """
    爬取 POE2 编年史做装数据（词缀/底材/技能/工艺），全版本适配。
    从多个子页面抓取数据，合并保存。
    """
    if not HAS_BS4:
        return "❌ 未安装 beautifulsoup4"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = [
        f"# POE2 编年史做装数据（全版本）\n",
        f"> 最后更新：{now}\n",
        f"> 数据来源：https://poe2db.tw/us/\n",
        "> 如果内容较少，说明网页依赖 JS 渲染，可手动打开下方链接补充。\n",
    ]

    # 逐个爬取子页面
    crawled = 0
    url_map = [
        ("modifiers", "一、词缀数据"),
        ("items",     "二、装备与底材"),
        ("gems",      "三、技能宝石"),
        ("crafting",  "四、做装工艺"),
    ]
    for key, title in url_map:
        url = CHRONICLES_PAGES.get(key)
        if not url:
            continue
        section = _crawl_page(url, title)
        line_count = len(section.split("\n"))
        if line_count > 3:
            content.append(section)
            crawled += 1

    # 兜底：抓不到数据时保存链接
    if crawled == 0:
        content.append("\n⚠️ 自动抓取未获取到有效数据（网页可能依赖 JS 渲染）。")
        content.append("\n## 重要参考链接（可在浏览器打开后手动喂养）")
        content.append("- 词缀大全：https://poe2db.tw/us/Modifiers")
        content.append("- 装备底材：https://poe2db.tw/us/Items")
        content.append("- 技能宝石：https://poe2db.tw/us/Gems")
        content.append("- 做装工艺：https://poe2db.tw/us/Crafting")

    save_memory("craft", "chronicles_craft_data.md", "\n\n".join(content))
    return f"✅ POE2 编年史已更新：{crawled} 个子页面有数据"
