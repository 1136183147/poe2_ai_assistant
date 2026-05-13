# price_checker/screenshot_ocr.py — 截图识别模块 v2
#
# 两种模式：
#   1. 剪贴板模式（推荐）：游戏内 Ctrl+C 复制装备 → 助手自动解析，100% 准确
#   2. 截图+OCR 模式（备用）：截图鼠标附近 → Tesseract 识别文字

import os
import re
import time
from typing import Dict, Optional, Tuple

try:
    from PIL import ImageGrab, Image, ImageEnhance, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False


class ScreenshotOCR:

    def __init__(self):
        self._tesseract_path = self._find_tesseract()
        if self._tesseract_path and HAS_TESSERACT:
            pytesseract.pytesseract.tesseract_cmd = self._tesseract_path

    def _find_tesseract(self) -> Optional[str]:
        if os.name == 'nt':
            for path in [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\tesseract\tesseract.exe',
            ]:
                if os.path.exists(path):
                    return path
        return None

    # ── 剪贴板模式 ──────────────────────────────
    def read_clipboard(self) -> str:
        """读取剪贴板（POE2 Ctrl+C 复制装备后调用）"""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            return text
        except Exception:
            return ""

    def is_poe2_item(self, text: str) -> bool:
        """判断剪贴板内容是否是 POE2 装备"""
        if not text or len(text) < 20:
            return False
        markers = ["Item Class:", "Rarity:", "Item Level:", "--------",
                   "物品类型", "稀有度", "物品等级"]
        return sum(1 for m in markers if m in text) >= 2

    # ── 截图+OCR 模式 ───────────────────────────
    def capture_screen(self, region=None) -> Optional[Image.Image]:
        if not HAS_PIL:
            raise RuntimeError("未安装 Pillow：pip install pillow")
        try:
            return ImageGrab.grab(bbox=region) if region else ImageGrab.grab()
        except Exception as e:
            raise RuntimeError(f"截图失败：{e}")

    def capture_near_mouse(self) -> Optional[Image.Image]:
        """截取鼠标附近装备框区域"""
        if not HAS_PIL:
            return None
        try:
            try:
                import pyautogui
                mx, my = pyautogui.position()
                sw, sh = pyautogui.size()
            except ImportError:
                full = ImageGrab.grab()
                sw, sh = full.size
                mx, my = sw // 2, sh // 2

            bw, bh = 360, 680
            gap = 15
            x1 = mx + gap if mx + bw + gap < sw else mx - bw - gap
            y1 = max(0, my - bh // 3)
            x2 = min(sw, x1 + bw)
            y2 = min(sh, y1 + bh)
            return ImageGrab.grab(bbox=(x1, y1, x2, y2))
        except Exception as e:
            print(f"截图失败：{e}")
            return None

    def enhance_for_ocr(self, img: Image.Image) -> Image.Image:
        """增强图像提升 OCR 准确率"""
        w, h = img.size
        img = img.resize((w * 2, h * 2), Image.LANCZOS)
        img = ImageEnhance.Contrast(img).enhance(2.5)
        img = ImageEnhance.Brightness(img).enhance(1.4)
        img = img.filter(ImageFilter.SHARPEN)
        return img

    def ocr_image(self, image: Image.Image) -> str:
        if not HAS_TESSERACT:
            raise RuntimeError(
                "未安装 pytesseract：pip install pytesseract\n"
                "还需安装 Tesseract-OCR 程序：https://github.com/tesseract-ocr/tesseract/releases"
            )
        try:
            enhanced = self.enhance_for_ocr(image)
            return pytesseract.image_to_string(enhanced, config=r'--oem 3 --psm 6 -l eng+chi_sim').strip()
        except Exception as e:
            raise RuntimeError(f"OCR 识别失败：{e}")

    # ── 装备文本解析（Ctrl+C 或 OCR 均可）──────
    def parse_equipment(self, text: str) -> Dict:
        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
        equipment = {
            "name": "", "base_type": "", "item_class": "",
            "level": 0, "rarity": "", "corrupted": False,
            "prefixes": [], "suffixes": [], "implicit": [],
            "explicit": [], "properties": {}, "raw_text": text,
        }

        # 按 -------- 分节
        sections, cur = [], []
        for line in lines:
            if re.match(r"^-{4,}$", line):
                if cur:
                    sections.append(cur)
                cur = []
            else:
                cur.append(line)
        if cur:
            sections.append(cur)

        if not sections:
            return equipment

        # 第一节解析
        first = sections[0]
        for line in first:
            if line.startswith("Item Class:"):
                equipment["item_class"] = line.split(":", 1)[1].strip()
            elif line.startswith("Rarity:"):
                r = line.split(":", 1)[1].strip()
                equipment["rarity"] = {"Normal":"普通","Magic":"魔法","Rare":"稀有","Unique":"传奇"}.get(r, r)
            elif "Item Level:" in line:
                m = re.search(r"Item Level:\s*(\d+)", line)
                if m:
                    equipment["level"] = int(m.group(1))

        # 名称 / 底材
        name_lines = [l for l in first if not any(
            l.startswith(k) for k in ["Item Class:", "Rarity:", "Item Level:", "Sockets:"]
        )]
        if name_lines:
            equipment["base_type"] = name_lines[-1]
            if len(name_lines) >= 2:
                equipment["name"] = name_lines[-2]

        full = "\n".join(lines)

        # 腐化
        if re.search(r"\bCorrupted\b|已腐化", full, re.I):
            equipment["corrupted"] = True

        # 物品等级备用
        if not equipment["level"]:
            m = re.search(r"(?:Item Level|物品等级)[:\s]+(\d+)", full, re.I)
            if m:
                equipment["level"] = int(m.group(1))

        # 词条提取
        STATS = [
            (r"(\+[\d,]+) to maximum Life",                     "最大生命值 +{0}",    "prefix"),
            (r"(\+[\d,]+) to maximum Mana",                     "最大魔力 +{0}",      "prefix"),
            (r"(\+[\d,]+) to maximum Energy Shield",            "最大能量护盾 +{0}",  "prefix"),
            (r"(\+\d+)% to Fire Resistance",                    "火抗性 +{0}%",       "suffix"),
            (r"(\+\d+)% to Cold Resistance",                    "冰抗性 +{0}%",       "suffix"),
            (r"(\+\d+)% to Lightning Resistance",               "闪抗性 +{0}%",       "suffix"),
            (r"(\+\d+)% to Chaos Resistance",                   "混沌抗性 +{0}%",     "suffix"),
            (r"(\+\d+)% to all Elemental Resistances",          "全元素抗性 +{0}%",   "suffix"),
            (r"(\d+)% increased Physical Damage",               "物理伤害提升 {0}%",  "prefix"),
            (r"(\d+)% increased Attack Speed",                  "攻击速度提升 {0}%",  "suffix"),
            (r"(\d+)% increased Cast Speed",                    "施法速度提升 {0}%",  "suffix"),
            (r"(\d+)% increased Movement Speed",                "移动速度提升 {0}%",  "suffix"),
            (r"([\d.]+)% Critical Strike Chance",               "暴击率 {0}%",        "suffix"),
            (r"(\+\d+) to Strength",                            "力量 +{0}",          "suffix"),
            (r"(\+\d+) to Dexterity",                           "敏捷 +{0}",          "suffix"),
            (r"(\+\d+) to Intelligence",                        "智慧 +{0}",          "suffix"),
            (r"(\+\d+) to all Attributes",                      "全属性 +{0}",        "suffix"),
            (r"Adds (\d+) to (\d+) Physical Damage",            "附加物理伤害 {0}-{1}","prefix"),
            (r"Adds (\d+) to (\d+) Fire Damage",                "附加火焰伤害 {0}-{1}","prefix"),
            (r"Adds (\d+) to (\d+) Cold Damage",                "附加冰冷伤害 {0}-{1}","prefix"),
            (r"Adds (\d+) to (\d+) Lightning Damage",           "附加闪电伤害 {0}-{1}","prefix"),
        ]

        for pattern, label_tpl, slot in STATS:
            m = re.search(pattern, full, re.M | re.I)
            if m:
                groups = m.groups()
                label = label_tpl.format(*groups)
                entry = {"text": label, "raw": m.group(0).strip(), "values": list(groups)}
                equipment["explicit"].append(entry)
                if slot == "prefix":
                    equipment["prefixes"].append(label)
                else:
                    equipment["suffixes"].append(label)

        return equipment

    def capture_and_parse(self, region=None) -> Tuple[str, Dict]:
        """截图 + OCR + 解析，返回 (原始文本, 解析结果)"""
        img = self.capture_screen(region)
        text = self.ocr_image(img)
        return text, self.parse_equipment(text)

    def clipboard_and_parse(self) -> Tuple[str, Dict]:
        """读取剪贴板 + 解析（推荐方式）"""
        text = self.read_clipboard()
        return text, self.parse_equipment(text)
