#!/usr/bin/env python3
# main.py — POE2 全版本 AI 助手入口（一键启动所有功能）

import sys
import os
import threading

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _init_memories():
    """首次运行初始化：生成 MD 模板 + 检查 0.5 赛季个人总结。"""
    print("📂 初始化记忆库模板…")
    from md_manager.md_generator import init_all_templates
    result = init_all_templates()
    print(result)

    from utils.memory_manager import load_memory, init_user_version_memory
    user_05 = load_memory("core", "user_version_0.5.md", version="0.5")
    if not user_05:
        print("\n" + "=" * 60)
        print("💡 未检测到你个人总结的 0.5 赛季细节。")
        print("   请将你整理好的总结内容粘贴到下方，按回车确认：")
        print("   （也可直接回车跳过，后续在悬浮窗用指令补充）")
        print("=" * 60)
        try:
            content = input("粘贴总结（回车跳过）：").strip()
            if content:
                init_user_version_memory(version="0.5", content=content)
            else:
                print("⏭️  已跳过，稍后可在悬浮窗输入：初始化0.5赛季总结：<内容>")
        except EOFError:
            pass


def _start_crawlers():
    """后台线程启动爬虫定时任务。"""
    try:
        from crawler import start_crawler_schedule
        print("🕷️  启动爬虫线程…")
        start_crawler_schedule()
    except Exception as e:
        print(f"⚠️  爬虫线程异常退出：{e}")


def main():
    print("=" * 60)
    print("  ⚡ POE2 全版本 AI 助手 v1.0 启动中…")
    print("=" * 60)

    # 1. 初始化记忆库
    _init_memories()

    # 2. 后台启动爬虫
    crawler_thread = threading.Thread(target=_start_crawlers, daemon=True)
    crawler_thread.start()
    print("✅ 爬虫线程已在后台启动")

    # 3. 启动悬浮窗（主线程，阻塞直到窗口关闭）
    print("✅ 启动悬浮窗，游戏时置顶使用，按 ESC 隐藏…\n")
    try:
        from gui.float_window import start_float_window
        start_float_window()
    except ImportError as e:
        print(f"❌ 悬浮窗启动失败（缺少 tkinter）：{e}")
        print("   请确认 Python 环境包含 tkinter（Windows 默认已内置）")
    except Exception as e:
        print(f"❌ 悬浮窗异常：{e}")

    print("\n👋 POE2 AI 助手已退出，再见！")


if __name__ == "__main__":
    main()
