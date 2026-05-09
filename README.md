# POE2 全版本 AI 游戏助手

适配 0.5 / 1.0 及所有后续版本，无需随版本重新开发。

---

## 快速开始

### 1. 环境要求
- Python 3.10+（Windows 自带 tkinter）
- 安装依赖：
```bash
pip install requests beautifulsoup4 schedule
```

### 2. 配置 LLM
打开 `config.py`，找到 `LLM_CONFIG`，填入你的 API Key：
```python
LLM_PROVIDER = "deepseek"   # 或 "openai" / "qianwen"

LLM_CONFIG = {
    "deepseek": {
        "api_key": "sk-xxxxxxxxxxxxxxxx",   # ← 替换这里
        ...
    }
}
```

> **推荐使用 DeepSeek**（价格低、速度快、支持中文）  
> 申请地址：https://platform.deepseek.com/

### 3. 启动
```bash
python main.py
```
首次启动时可粘贴你整理的 0.5 赛季总结，后续无需重复操作。

---

## 悬浮窗使用

| 操作 | 说明 |
|------|------|
| 直接提问 | 0.5赛季符咒怎么玩？做装怎么选底材？ |
| 初始化版本总结 | `初始化1.0赛季总结：<你的内容>` |
| 记录新发现 | `记录：<你的发现>` |
| 做装心得 | `做装心得：<心得内容>` |
| 收藏BD | `收藏BD：<BD描述>` |
| 切换版本 | 下拉框选择版本，点击「切换版本」|
| 导出记忆 | 点击「导出记忆」，生成 ZIP 包 |
| 导入记忆 | 点击「导入记忆」，选择 ZIP 包 |
| 立即爬取 | 点击「立即爬取」，手动触发所有爬虫 |
| 隐藏窗口 | 按 ESC 键 |

---

## 项目结构

```
poe2_ai_assistant/
├── main.py                  # 入口，一键启动
├── config.py                # 全局配置（LLM Key、爬虫频率、悬浮窗参数）
├── requirements.txt         # 依赖列表
├── memory/                  # 记忆库（自动生成）
│   ├── core/                # 版本机制 + 职业信息
│   ├── craft/               # 做装攻略
│   ├── meta/                # 实时 Meta（BD / 物价）
│   ├── user/                # 个人专属记忆
│   └── backup/              # 每日自动备份
├── ai/
│   ├── llm_engine.py        # AI 对话核心 + 特殊指令处理
│   └── memory_retriever.py  # 记忆检索 + 版本切换
├── crawler/
│   ├── __init__.py          # 爬虫调度
│   ├── _base.py             # 公共请求工具
│   ├── ninja_crawler.py     # POE2 Ninja
│   ├── darkcore_crawler.py  # 暗黑核
│   ├── caimogu_crawler.py   # 踩蘑菇
│   ├── douyin_ace_crawler.py# 抖音 Ace（需 selenium）
│   ├── bilibili_crawler.py  # B站老孤独
│   ├── poe2_official_crawler.py    # POE2 官网
│   ├── poe2_chronicles_crawler.py  # POE2 编年史
│   └── version_crawler.py   # 版本补丁说明
├── gui/
│   └── float_window.py      # 悬浮窗界面
├── md_manager/
│   └── md_generator.py      # MD 模板生成器
└── utils/
    └── memory_manager.py    # 记忆读写 / 导出导入 / 备份
```

---

## 常见问题

**Q：爬虫失败/抓不到内容？**  
A：检查网络；若目标网站改版，修改对应爬虫文件中的 CSS 选择器即可。

**Q：悬浮窗遮挡游戏？**  
A：拖动到屏幕边缘，或按 ESC 隐藏；在 `config.py` 调整 `FLOAT_WINDOW` 大小和透明度。

**Q：AI 回答不准确？**  
A：用 `初始化[版本]赛季总结：` 补充你的个人总结，优先级最高。

**Q：换电脑/分享给朋友？**  
A：点「导出记忆」生成 ZIP 包，在新电脑上点「导入记忆」一键继承。

**Q：1.0 及后续版本怎么适配？**  
A：无需改动代码。新版本上线后：
1. 爬虫自动同步资讯
2. 在悬浮窗输入 `初始化1.0赛季总结：<内容>` 补充个人总结
3. 下拉框切换至对应版本即可
