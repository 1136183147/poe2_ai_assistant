# crawler/douyin_ace_crawler.py — 抖音 Ace 做装视频爬虫
# 说明：抖音页面大量依赖 JS 渲染，此处提供两种实现：
#   1. 若安装了 selenium，使用浏览器渲染（推荐）
#   2. 若未安装，提供占位文件并提示用户手动喂养

from utils.memory_manager import save_memory


def crawl_douyin_ace() -> str:
    """尝试爬取抖音 Ace 最新做装攻略。"""
    try:
        return _crawl_with_selenium()
    except ImportError:
        return _placeholder()
    except Exception as e:
        return f"❌ 抖音 Ace 爬取失败：{e}，请手动喂养"


def _crawl_with_selenium() -> str:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    import time

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://www.douyin.com/user/Ace_poe")
        time.sleep(5)
        videos = driver.find_elements(By.CSS_SELECTOR, "[class*='video-card'], [class*='item']")[:10]
        content = ["# 抖音 Ace 最新做装攻略（自动同步）\n"]
        for v in videos:
            try:
                title = v.find_element(By.CSS_SELECTOR, "[class*='title'], [class*='desc']").text.strip()
                if title:
                    content.append(f"- {title}")
            except Exception:
                pass
        text = "\n".join(content)
        save_memory("craft", "ace_craft_guide.md", text)
        return f"✅ 抖音 Ace 已更新：{len(videos)} 条视频标题"
    finally:
        driver.quit()


def _placeholder() -> str:
    note = (
        "# 抖音 Ace 做装攻略（手动喂养区）\n\n"
        "> 说明：抖音需要 selenium 才能自动爬取。\n"
        "> 你可以在悬浮窗输入 '做装心得：<你的总结>' 手动喂养 Ace 的视频内容。\n\n"
        "## 如何启用自动爬取\n"
        "1. 安装 Chrome 浏览器\n"
        "2. 下载对应版本的 ChromeDriver\n"
        "3. 执行：pip install selenium\n"
        "4. 重启助手即可自动爬取"
    )
    save_memory("craft", "ace_craft_guide.md", note)
    return "⚠️ 未安装 selenium，已生成手动喂养提示文件"


def manual_feed_ace(content: str) -> str:
    """手动喂养 Ace 做装内容（在悬浮窗中调用）。"""
    from datetime import datetime
    from utils.memory_manager import append_memory
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    append_memory("craft", "ace_craft_guide.md", f"\n## [{timestamp}] 手动补充\n{content}")
    return "✅ 已将 Ace 做装内容存入记忆库"
