# md_manager/md_generator.py — MD 知识库管理（自动生成/更新 MD 文档）

import os
from datetime import datetime
from utils.memory_manager import save_memory, load_memory


def generate_version_template(version: str) -> str:
    """生成指定版本的 MD 模板文件（若不存在）。"""
    existing = load_memory("core", f"version_{version}.md", version=version)
    if existing:
        return f"⚠️ {version} 版本记忆已存在，跳过模板生成"

    template = f"""# POE2 {version} 版本记忆（自动生成模板）

> 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}
> 此文件由 md_generator 自动创建，可通过爬虫或手动喂养补充内容。

## 版本核心机制
（待补充）

## 新职业 / 新升华
（待补充）

## 新玩法 / 赛季机制
（待补充）

## 重要机制变更
（待补充）

## 版本 T0 BD 推荐
（待补充）

## 国服 vs 国际服差异
（待补充）
"""
    save_memory("core", f"version_{version}.md", template, version=version)
    return f"✅ 已生成 {version} 版本 MD 模板"


def generate_all_templates(versions: list[str] = None):
    """为所有配置版本生成 MD 模板。"""
    if versions is None:
        from config import SUPPORTED_VERSIONS
        versions = SUPPORTED_VERSIONS
    results = [generate_version_template(v) for v in versions]
    return "\n".join(results)


def generate_craft_base_select():
    """生成底材选择规则模板（全版本通用）。"""
    existing = load_memory("craft", "base_select.md")
    if existing:
        return "⚠️ 底材选择文件已存在，跳过"

    content = """# 底材选择规则（全版本通用）

## 防具底材选择原则
1. 优先选择对应角色属性底材（力量/敏捷/智慧）
2. 终局底材等级要求：75 级以上
3. 隐含属性优先选择对 BD 有增益的（如攻速、暴击等）

## 武器底材选择原则
1. 匹配 BD 的伤害类型（物理/元素/混沌）
2. DPS 基础值是优先考虑项
3. 攻速底材适合叠加词缀 BD

## 首饰底材选择
- 戒指：优先生命 + 抗性底材
- 项链：优先暴击 / 施法速度底材（视 BD 而定）
- 手镯：优先全元素抗性底材

## 通用原则
- 不要在低级底材上浪费高级通货
- 优先用「偷看」确认词缀池再做装
"""
    save_memory("craft", "base_select.md", content)
    return "✅ 已生成底材选择规则模板"


def generate_common_mechanic():
    """生成全版本通用机制 MD。"""
    existing = load_memory("core", "common_mechanic.md")
    if existing:
        return "⚠️ 通用机制文件已存在，跳过"

    content = """# POE2 全版本通用机制

## 做装基础流程
1. 确定 BD 词缀目标（主属性 + 辅助词缀）
2. 选合适底材（等级 / 底材类型）
3. 魔法装：蔚蓝 → 改造/扩充 → 如有需要镜铸
4. 稀有装：混沌洗 / 神圣强化 / 工艺台强行做装
5. 若需特定词缀，先封条再做

## 通货功能速查
| 通货       | 作用                         |
|-----------|------------------------------|
| 改造石     | 重掷魔法装备词缀               |
| 混沌石     | 重掷稀有装备所有词缀            |
| 崇高石     | 为稀有装备添加一条词缀          |
| 神圣石     | 重掷数值范围                   |
| 工匠石     | 对魔法装备增加词缀数             |
| 镜子       | 复制一件装备                   |

## 地图机制
- 地图词缀越高，产出越丰厚，风险越高
- 地图 Boss 掉落受 MOD 加成
"""
    save_memory("core", "common_mechanic.md", content)
    return "✅ 已生成通用机制模板"


def init_all_templates():
    """一键初始化所有 MD 模板（首次运行调用）。"""
    results = [
        generate_all_templates(),
        generate_craft_base_select(),
        generate_common_mechanic(),
    ]
    return "\n".join(results)
