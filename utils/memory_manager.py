# utils/memory_manager.py — 记忆管理核心（永久存储 + 全版本迭代 + 导出/导入）

import json
import os
import shutil
from datetime import datetime
from config import MEMORY_ROOT, BACKUP_KEEP_DAYS

# 初始化记忆根目录及各子目录
SUBDIRS = ["core", "craft", "meta", "user", "backup"]
for _d in SUBDIRS:
    os.makedirs(os.path.join(MEMORY_ROOT, _d), exist_ok=True)


# ──────────────────────────────────────────────
# 基础读写
# ──────────────────────────────────────────────

def load_memory(category: str, filename: str, version: str = "common"):
    """
    加载指定分类的记忆内容（MD / JSON），适配全版本。
    version="common" 表示通用路径；指定版本时读取版本子目录。
    """
    if version != "common":
        path = os.path.join(MEMORY_ROOT, category, f"version_{version}", filename)
    else:
        path = os.path.join(MEMORY_ROOT, category, filename)

    if not os.path.exists(path):
        return {} if filename.endswith(".json") else ""

    with open(path, "r", encoding="utf-8") as f:
        if filename.endswith(".json"):
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
        return f.read()


def save_memory(category: str, filename: str, content, version: str = "common"):
    """
    保存记忆内容，支持按版本分类，不覆盖历史版本。
    保存完成后自动触发备份。
    """
    if version != "common":
        category_path = os.path.join(MEMORY_ROOT, category, f"version_{version}")
    else:
        category_path = os.path.join(MEMORY_ROOT, category)
    os.makedirs(category_path, exist_ok=True)

    path = os.path.join(category_path, filename)
    with open(path, "w", encoding="utf-8") as f:
        if filename.endswith(".json"):
            json.dump(content, f, ensure_ascii=False, indent=2)
        else:
            f.write(str(content))

    _auto_backup()


def append_memory(category: str, filename: str, text: str, version: str = "common"):
    """在已有 MD 文件末尾追加内容（适合增量喂养）。"""
    existing = load_memory(category, filename, version)
    save_memory(category, filename, existing + "\n\n" + text, version)


# ──────────────────────────────────────────────
# 版本专属初始化
# ──────────────────────────────────────────────

def init_user_version_memory(version: str = "0.5", content: str = ""):
    """初始化用户个人总结的版本细节，单独存储，后续版本不覆盖。"""
    save_memory("core", f"user_version_{version}.md", content, version=version)
    print(f"✅ 已初始化你个人总结的 {version} 赛季细节，存入专属记忆")


def update_version_memory(version: str, new_content: str):
    """更新指定版本记忆，不覆盖历史版本与个人专属记忆。"""
    save_memory("core", f"version_{version}.md", new_content, version=version)
    print(f"✅ 已更新 {version} 版本记忆")


# ──────────────────────────────────────────────
# 用户笔记追加（手动喂养）
# ──────────────────────────────────────────────

def add_user_note(note: str, version: str = "common"):
    """将用户在悬浮窗中输入的新经验追加到个人记忆。"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    append_memory("user", "version_notes.md", f"[{timestamp}]\n{note}", version)
    print("✅ 已将你的新经验存入个人记忆")


def add_craft_note(note: str):
    """追加做装心得到个人做装笔记。"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    append_memory("user", "craft_notes.md", f"[{timestamp}]\n{note}")


def add_favorite_build(build: str):
    """收藏 BD 到个人 BD 列表。"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    append_memory("user", "favorite_builds.md", f"[{timestamp}]\n{build}")


# ──────────────────────────────────────────────
# 对话记录
# ──────────────────────────────────────────────

def save_chat_history(question: str, answer: str):
    """将一条对话追加到 chat_history.json。"""
    history = load_memory("user", "chat_history.json")
    if not isinstance(history, list):
        history = []
    history.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "question": question,
        "answer": answer,
    })
    # 只保留最新 200 条，避免文件过大
    if len(history) > 200:
        history = history[-200:]
    save_memory("user", "chat_history.json", history)


# ──────────────────────────────────────────────
# 导出 / 导入
# ──────────────────────────────────────────────

def export_memory(zip_path: str = "POE2_AI记忆包") -> str:
    """一键导出所有记忆为 ZIP 包，用于换电脑或发给朋友。"""
    try:
        abs_path = os.path.abspath(zip_path)
        shutil.make_archive(abs_path, "zip", MEMORY_ROOT)
        return f"✅ 记忆已导出：{abs_path}.zip"
    except Exception as e:
        return f"❌ 导出失败：{e}"


def import_memory(zip_path: str) -> str:
    """一键导入记忆包，继承所有版本记忆与个人专属记忆。"""
    if not os.path.exists(zip_path):
        return "❌ 记忆包文件不存在，请检查路径"
    try:
        shutil.unpack_archive(zip_path, MEMORY_ROOT)
        return "✅ 记忆导入成功，已继承所有版本知识库与专属记忆"
    except Exception as e:
        return f"❌ 导入失败：{e}"


# ──────────────────────────────────────────────
# 自动备份（内部调用）
# ──────────────────────────────────────────────

def _auto_backup():
    """每次写入时检查：当天若无备份则创建，并清理超期备份。"""
    backup_dir = os.path.join(MEMORY_ROOT, "backup")
    os.makedirs(backup_dir, exist_ok=True)
    today_str   = datetime.now().strftime("%Y%m%d")
    backup_name = f"backup_{today_str}"
    backup_full = os.path.join(backup_dir, backup_name + ".zip")

    if not os.path.exists(backup_full):
        # 临时打包除 backup 目录外的内容
        tmp_dir = os.path.join(MEMORY_ROOT, "_tmp_bk")
        os.makedirs(tmp_dir, exist_ok=True)
        for item in os.listdir(MEMORY_ROOT):
            if item in ("backup", "_tmp_bk"):
                continue
            src = os.path.join(MEMORY_ROOT, item)
            dst = os.path.join(tmp_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
        shutil.make_archive(os.path.join(backup_dir, backup_name), "zip", tmp_dir)
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # 删除超期备份
    for fname in os.listdir(backup_dir):
        if not fname.startswith("backup_") or not fname.endswith(".zip"):
            continue
        date_str = fname[7:15]
        try:
            file_date = datetime.strptime(date_str, "%Y%m%d")
            if (datetime.now() - file_date).days > BACKUP_KEEP_DAYS:
                os.remove(os.path.join(backup_dir, fname))
        except ValueError:
            pass
