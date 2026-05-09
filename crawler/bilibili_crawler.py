# crawler/bilibili_crawler.py — B站「受宠的老孤独」爬虫

from crawler._base import fetch_html, safe_text
from utils.memory_manager import save_memory

# 「受宠的老孤独」B站 UID（请替换为真实 UID）
LGDZ_UID = "123456789"   # ← 替换为实际 UID


def crawl_bilibili_lgdz() -> str:
    """爬取 B站老孤独最新 POE2 版本解读视频标题与简介。"""
    url  = f"https://space.bilibili.com/{LGDZ_UID}/video"
    html = fetch_html(url)
    if html is None:
        # B站主页防爬，提供备用 RSS 方式
        return _try_rss()

    try:
        from bs4 import BeautifulSoup
        soup    = BeautifulSoup(html, "html.parser")
        content = ["# B站老孤独 POE2 版本解读（自动同步）\n"]
        items   = soup.select(".small-item, .video-item, [class*='video']")[:10]
        for item in items:
            title_el = item.select_one(".title, a[title]")
            title    = safe_text(title_el) or (title_el.get("title", "") if title_el else "")
            if title.strip():
                content.append(f"- {title}")
        text = "\n".join(content)
        save_memory("core", "version_guides.md", text)
        return f"✅ B站老孤独已更新：{len(items)} 条视频"
    except ImportError:
        return "❌ 未安装 beautifulsoup4"
    except Exception as e:
        return f"❌ B站爬取失败：{e}"


def _try_rss() -> str:
    """尝试通过 B站 RSS 接口获取视频列表。"""
    url  = f"https://api.bilibili.com/x/space/arc/search?mid={LGDZ_UID}&ps=10&pn=1"
    html = fetch_html(url)
    if html is None:
        return "❌ B站接口请求失败，请手动补充版本总结"
    import json as _json
    try:
        data  = _json.loads(html)
        vlist = data.get("data", {}).get("list", {}).get("vlist", [])
        content = ["# B站老孤独 POE2 版本解读（RSS）\n"]
        for v in vlist[:10]:
            title = v.get("title", "")
            desc  = v.get("description", "")[:100]
            if title:
                content.append(f"## {title}\n{desc}")
        text = "\n\n".join(content)
        save_memory("core", "version_guides.md", text)
        return f"✅ B站老孤独（RSS）已更新：{len(vlist)} 条"
    except Exception as e:
        return f"❌ B站 RSS 解析失败：{e}"
