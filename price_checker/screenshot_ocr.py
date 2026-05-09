# price_checker/screenshot_ocr.py — 截图识别模块

import os
import time
from typing import Dict, Optional, Tuple

try:
    from PIL import ImageGrab, Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False


class ScreenshotOCR:
    """截图识别类"""
    
    def __init__(self):
        self._tesseract_path = self._find_tesseract()
    
    def _find_tesseract(self) -> Optional[str]:
        """查找 Tesseract OCR 路径"""
        if os.name == 'nt':
            # Windows 常见路径
            paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\tesseract\tesseract.exe',
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
        return None
    
    def capture_screen(self, region: Tuple[int, int, int, int] = None) -> Optional[Image.Image]:
        """
        截取屏幕
        
        Args:
            region: (left, top, right, bottom) 区域坐标，None 表示全屏
        
        Returns:
            PIL Image 对象
        """
        if not HAS_PIL:
            raise RuntimeError("未安装 PIL 库，请执行：pip install pillow")
        
        try:
            if region:
                return ImageGrab.grab(bbox=region)
            return ImageGrab.grab()
        except Exception as e:
            raise RuntimeError(f"截图失败：{e}")
    
    def capture_and_save(self, save_path: str = "screenshot.png", region=None) -> str:
        """截取屏幕并保存"""
        img = self.capture_screen(region)
        img.save(save_path)
        return save_path
    
    def ocr_image(self, image: Image.Image) -> str:
        """
        OCR 识别图片中的文字
        
        Args:
            image: PIL Image 对象
        
        Returns:
            识别出的文本
        """
        if not HAS_TESSERACT:
            raise RuntimeError("未安装 pytesseract，请执行：pip install pytesseract")
        
        if self._tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self._tesseract_path
        
        try:
            # 使用自定义配置提高识别率
            custom_config = r'--oem 3 --psm 6 -l eng+chi_sim'
            return pytesseract.image_to_string(image, config=custom_config)
        except Exception as e:
            raise RuntimeError(f"OCR 识别失败：{e}")
    
    def ocr_file(self, file_path: str) -> str:
        """识别图片文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在：{file_path}")
        
        img = Image.open(file_path)
        return self.ocr_image(img)
    
    def parse_equipment(self, text: str) -> Dict:
        """
        从 OCR 文本中解析装备信息
        
        Args:
            text: OCR 识别的文本
        
        Returns:
            装备信息字典
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        equipment = {
            "name": "",
            "type": "",
            "level": 0,
            "rarity": "",
            "prefixes": [],  # 前缀词缀
            "suffixes": [],  # 后缀词缀
            "properties": {},  # 基础属性
            "implicit": "",  # 隐性词缀
        }
        
        # POE2 装备信息的典型格式：
        # 装备名称（可能是彩色的）
        # 装备类型
        # 等级 X
        # 稀有度标识
        # 属性行...
        
        for line in lines:
            line = line.strip()
            
            # 尝试识别等级
            if line.startswith("Level") or line.startswith("等级"):
                try:
                    # Level 80 或 等级 80
                    parts = line.split()
                    for part in parts:
                        if part.isdigit():
                            equipment["level"] = int(part)
                            break
                except:
                    pass
            
            # 尝试识别稀有度
            rarity_keywords = {
                "Unique": "Unique",
                "Rare": "Rare", 
                "Magic": "Magic",
                "Normal": "Normal",
                "暗金": "Unique",
                "稀有": "Rare",
                "魔法": "Magic",
                "普通": "Normal",
            }
            for kw, rarity in rarity_keywords.items():
                if kw in line:
                    equipment["rarity"] = rarity
                    break
            
            # 尝试识别属性
            if ":" in line:
                parts = line.split(":", 1)
                key = parts[0].strip()
                value = parts[1].strip()
                equipment["properties"][key] = value
            
            # 词缀识别（通常以 "+" 或 "-" 开头）
            if line.startswith("+") or line.startswith("-"):
                # 尝试判断是前缀还是后缀
                # 在 POE 中，前缀通常是基础属性，后缀通常是额外属性
                suffix_keywords = ["to", "increased", "reduced", "chance", "duration", "radius"]
                is_suffix = any(kw.lower() in line.lower() for kw in suffix_keywords)
                
                if is_suffix:
                    equipment["suffixes"].append(line)
                else:
                    equipment["prefixes"].append(line)
        
        # 尝试提取装备名称（通常是第一行非空行）
        if lines:
            # 跳过等级和稀有度行，找第一个看起来像装备名的行
            for line in lines:
                if not line.startswith("Level") and not line.startswith("等级"):
                    # 检查是否包含稀有度关键词
                    has_rarity = any(r in line for r in ["Unique", "Rare", "Magic", "Normal", "暗金", "稀有", "魔法", "普通"])
                    if not has_rarity:
                        equipment["name"] = line
                        break
        
        return equipment
    
    def capture_and_parse(self, region=None) -> Tuple[str, Dict]:
        """
        截图并解析装备信息
        
        Returns:
            (识别的原始文本, 解析后的装备信息)
        """
        img = self.capture_screen(region)
        text = self.ocr_image(img)
        equipment = self.parse_equipment(text)
        return text, equipment


def test_ocr():
    """测试 OCR 功能"""
    ocr = ScreenshotOCR()
    
    print("=== 测试截图 OCR ===")
    print(f"PIL 可用: {HAS_PIL}")
    print(f"Tesseract 可用: {HAS_TESSERACT}")
    print(f"Tesseract 路径: {ocr._tesseract_path}")
    
    if HAS_PIL and HAS_TESSERACT:
        print("\n按 Enter 键截图...")
        input()
        
        print("正在截图...")
        text, equipment = ocr.capture_and_parse()
        
        print("\n=== 识别结果 ===")
        print(text)
        
        print("\n=== 解析结果 ===")
        print(f"装备名称: {equipment['name']}")
        print(f"装备类型: {equipment['type']}")
        print(f"等级: {equipment['level']}")
        print(f"稀有度: {equipment['rarity']}")
        print(f"前缀词缀: {equipment['prefixes']}")
        print(f"后缀词缀: {equipment['suffixes']}")
        print(f"属性: {equipment['properties']}")


if __name__ == "__main__":
    test_ocr()