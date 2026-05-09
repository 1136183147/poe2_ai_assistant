# memory/equipment_storage.py — 装备数据存储与检索模块

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional


class EquipmentStorage:
    """装备数据存储与检索类"""
    
    def __init__(self, storage_path: str = "memory/user/equipment.json"):
        self._storage_path = storage_path
        self._equipment_list = self._load_data()
    
    def _load_data(self) -> List[Dict]:
        """加载装备数据"""
        if os.path.exists(self._storage_path):
            try:
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []
    
    def _save_data(self):
        """保存装备数据"""
        os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
        with open(self._storage_path, "w", encoding="utf-8") as f:
            json.dump(self._equipment_list, f, ensure_ascii=False, indent=2)
    
    def save_equipment(self, equipment: Dict) -> str:
        """
        保存装备数据
        
        Args:
            equipment: 装备信息字典
            
        Returns:
            装备唯一ID
        """
        equipment_id = str(uuid.uuid4())[:8]
        
        saved_data = {
            "id": equipment_id,
            "name": equipment.get("name", ""),
            "type": equipment.get("type", ""),
            "level": equipment.get("level", 0),
            "rarity": equipment.get("rarity", ""),
            "prefixes": equipment.get("prefixes", []),
            "suffixes": equipment.get("suffixes", []),
            "properties": equipment.get("properties", {}),
            "implicit": equipment.get("implicit", ""),
            "created_at": datetime.now().isoformat(),
            "ocr_text": equipment.get("ocr_text", "")
        }
        
        self._equipment_list.append(saved_data)
        self._save_data()
        
        return equipment_id
    
    def search_equipment(self, keyword: str) -> List[Dict]:
        """
        搜索装备数据
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的装备列表
        """
        if not keyword:
            return []
        
        keyword = keyword.lower()
        results = []
        
        for equip in self._equipment_list:
            # 检查装备名称
            if keyword in equip["name"].lower():
                results.append(equip)
                continue
            
            # 检查装备类型
            if keyword in equip["type"].lower():
                results.append(equip)
                continue
            
            # 检查词缀
            for prefix in equip["prefixes"]:
                if keyword in prefix.lower():
                    results.append(equip)
                    break
            if equip in results:
                continue
            
            for suffix in equip["suffixes"]:
                if keyword in suffix.lower():
                    results.append(equip)
                    break
            if equip in results:
                continue
            
            # 检查属性
            for key, value in equip["properties"].items():
                if keyword in key.lower() or keyword in str(value).lower():
                    results.append(equip)
                    break
        
        # 按时间倒序排列
        results.sort(key=lambda x: x["created_at"], reverse=True)
        
        return results
    
    def get_all_equipment(self) -> List[Dict]:
        """获取所有装备"""
        return sorted(self._equipment_list, key=lambda x: x["created_at"], reverse=True)
    
    def get_equipment_by_id(self, equipment_id: str) -> Optional[Dict]:
        """根据ID获取装备"""
        for equip in self._equipment_list:
            if equip["id"] == equipment_id:
                return equip
        return None
    
    def delete_equipment(self, equipment_id: str) -> bool:
        """删除装备"""
        for i, equip in enumerate(self._equipment_list):
            if equip["id"] == equipment_id:
                del self._equipment_list[i]
                self._save_data()
                return True
        return False
    
    def clear_all(self):
        """清空所有装备数据"""
        self._equipment_list = []
        self._save_data()


def test_storage():
    """测试装备存储功能"""
    storage = EquipmentStorage()
    
    # 测试保存装备
    test_equip = {
        "name": "神圣之剑",
        "type": "双手剑",
        "level": 80,
        "rarity": "Rare",
        "prefixes": ["+100-150 物理伤害", "+20% 攻击速度"],
        "suffixes": ["+10% 暴击几率", "增加 50 火焰伤害"],
        "properties": {"品质": "20%"},
        "implicit": "攻击时有10%几率获得暴击球"
    }
    
    equip_id = storage.save_equipment(test_equip)
    print(f"保存装备成功，ID: {equip_id}")
    
    # 测试搜索
    results = storage.search_equipment("物理伤害")
    print(f"\n搜索 '物理伤害' 结果: {len(results)} 条")
    for r in results:
        print(f"  - {r['name']}")
    
    # 测试获取所有装备
    all_equip = storage.get_all_equipment()
    print(f"\n总装备数: {len(all_equip)}")


if __name__ == "__main__":
    test_storage()