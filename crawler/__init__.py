# crawler/__init__.py — 爬虫模块统一入口

import time
import threading

try:
    import schedule
    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False

from config import CRAWLER_INTERVALS, DOUYIN_ACE_TIME

_crawler_version = "0.5"


def set_crawler_version(version: str):
    global _crawler_version
    _crawler_version = version
    print(f"✅ 爬虫已切换至 {version} 版本资讯")


def get_crawler_version() -> str:
    return _crawler_version


def _safe_run(name: str, fn) -> str:
    """安全执行单个爬虫，任何异常都不会向上传播。"""
    try:
        result = fn()
        return f"{name}：{result}"
    except Exception as e:
        return f"{name}：❌ 异常 - {e}"


def _run_all_once():
    """首次启动预热，全部异常隔离，不影响主线程。"""
    try:
        from crawler.ninja_crawler           import crawl_poe2_ninja
        from crawler.darkcore_crawler        import crawl_darkcore
        from crawler.caimogu_crawler         import crawl_caimogu
        from crawler.poe2_official_crawler   import crawl_poe2_official_craft
        from crawler.poe2_chronicles_crawler import crawl_poe2_chronicles_craft
    except ImportError as e:
        print(f"❌ 爬虫模块导入失败：{e}")
        return

    jobs = [
        ("POE2 Ninja", crawl_poe2_ninja),
        ("暗黑核",       crawl_darkcore),
        ("踩蘑菇",       crawl_caimogu),
        ("POE2官网",     crawl_poe2_official_craft),
        ("POE2编年史",   crawl_poe2_chronicles_craft),
    ]
    for name, fn in jobs:
        result = _safe_run(name, fn)
        print(f"[爬虫预热] {result}")


def start_crawler_schedule():
    """启动所有爬虫定时任务（在独立后台线程中运行）。"""
    if not HAS_SCHEDULE:
        print("⚠️ 未安装 schedule 模块，请执行：pip install schedule")
        return

    try:
        from crawler.ninja_crawler           import crawl_poe2_ninja
        from crawler.darkcore_crawler        import crawl_darkcore
        from crawler.caimogu_crawler         import crawl_caimogu
        from crawler.douyin_ace_crawler      import crawl_douyin_ace
        from crawler.poe2_official_crawler   import crawl_poe2_official_craft
        from crawler.poe2_chronicles_crawler import crawl_poe2_chronicles_craft
        from crawler.bilibili_crawler        import crawl_bilibili_lgdz
    except ImportError as e:
        print(f"❌ 爬虫模块导入失败，跳过爬虫调度：{e}")
        return

    # 首次预热（另起线程，不阻塞调度循环）
    threading.Thread(target=_run_all_once, daemon=True).start()

    # 用 lambda 包裹，确保单个爬虫失败不影响整个调度
    schedule.every(CRAWLER_INTERVALS["ninja"]).hours.do(
        lambda: _safe_run("POE2 Ninja", crawl_poe2_ninja))
    schedule.every(CRAWLER_INTERVALS["darkcore"]).hours.do(
        lambda: _safe_run("暗黑核", crawl_darkcore))
    schedule.every(CRAWLER_INTERVALS["caimogu"]).hours.do(
        lambda: _safe_run("踩蘑菇", crawl_caimogu))
    schedule.every(CRAWLER_INTERVALS["chronicles"]).hours.do(
        lambda: _safe_run("POE2编年史", crawl_poe2_chronicles_craft))
    schedule.every(CRAWLER_INTERVALS["official"]).hours.do(
        lambda: _safe_run("POE2官网", crawl_poe2_official_craft))
    schedule.every(CRAWLER_INTERVALS["bilibili"]).hours.do(
        lambda: _safe_run("B站老孤独", crawl_bilibili_lgdz))
    schedule.every().day.at(DOUYIN_ACE_TIME).do(
        lambda: _safe_run("抖音Ace", crawl_douyin_ace))

    print("✅ 所有爬虫定时任务已注册，开始轮询")
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"⚠️ 爬虫调度异常（已忽略）：{e}")
        time.sleep(60)
