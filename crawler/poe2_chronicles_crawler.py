# crawler/poe2_chronicles_crawler.py — POE2 编年史做装数据爬虫

from datetime import datetime
from urllib.parse import quote
from crawler._base import fetch_html
from utils.memory_manager import save_memory
from config import CRAWLER_URLS

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


# 实时搜索接口
def search_equipment(keyword: str) -> str:
    """
    实时从 POE2 编年史搜索装备/底材信息
    :param keyword: 搜索关键词（如：剑、法杖、底材等）
    :return: 搜索结果文本
    """
    if not HAS_BS4:
        return "❌ 需要安装 beautifulsoup4"
    
    try:
        # 构建搜索 URL
        encoded_keyword = quote(keyword)
        search_url = f"https://poe2db.tw/us/search?q={encoded_keyword}"
        
        html = fetch_html(search_url)
        if html is None:
            return "❌ 网络请求失败"
        
        soup = BeautifulSoup(html, "html.parser")
        
        # 查找搜索结果列表
        results = []
        
        # 尝试多种可能的结果容器
        result_containers = soup.select(".search-results, .results, table.items, .item-list, #search-results")
        
        if result_containers:
            for container in result_containers:
                items = container.find_all(["a", "tr", "div"])
                for item in items[:10]:  # 最多取10个结果
                    text = item.get_text(strip=True)
                    if text and len(text) > 2:
                        # 检查是否有链接
                        link = item.get("href")
                        if link:
                            full_link = f"https://poe2db.tw{link}" if link.startswith("/") else link
                            results.append(f"- [{text}]({full_link})")
                        else:
                            results.append(f"- {text}")
        
        # 如果没有找到结构化结果，尝试提取页面中的装备名称
        if not results:
            # 查找所有包含物品名称的元素
            item_names = soup.find_all(["h1", "h2", "h3", "span", "div"], text=True)
            for name in item_names[:15]:
                text = name.get_text(strip=True)
                if text and len(text) > 3 and len(text) < 50:
                    # 过滤掉常见导航词
                    if text.lower() not in ["items", "search", "results", "home", "database"]:
                        results.append(f"- {text}")
        
        if results:
            return f"## 搜索结果：{keyword}\n\n" + "\n".join(results[:10])
        else:
            return "未找到相关装备信息"
    
    except Exception as e:
        return f"❌ 搜索失败：{e}"


def search_skill(keyword: str) -> str:
    """
    实时从 POE2 编年史搜索技能/天赋信息
    :param keyword: 搜索关键词（如：技能名称、天赋等）
    :return: 搜索结果文本
    """
    if not HAS_BS4:
        return "❌ 需要安装 beautifulsoup4"
    
    try:
        encoded_keyword = quote(keyword)
        search_url = f"https://poe2db.tw/us/search?q={encoded_keyword}&type=skill"
        
        html = fetch_html(search_url)
        if html is None:
            return "❌ 网络请求失败"
        
        soup = BeautifulSoup(html, "html.parser")
        
        results = []
        
        # 查找技能相关结果
        skill_elements = soup.select(".skill-name, .gem-name, .skill-header, h3.skill")
        for element in skill_elements[:10]:
            text = element.get_text(strip=True)
            if text and len(text) > 2:
                link = element.find_parent("a")
                if link and link.get("href"):
                    full_link = f"https://poe2db.tw{link['href']}" if link['href'].startswith("/") else link['href']
                    results.append(f"- [{text}]({full_link})")
                else:
                    results.append(f"- {text}")
        
        # 兜底：通用搜索
        if not results:
            results = search_equipment(keyword)
        
        if isinstance(results, str) and results != "未找到相关装备信息":
            return results
        
        return "未找到相关技能信息"
    
    except Exception as e:
        return f"❌ 搜索失败：{e}"

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
