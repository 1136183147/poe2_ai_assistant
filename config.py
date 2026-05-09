# config.py — POE2 AI 助手全局配置

# ==================== LLM 配置 ====================
# 支持：openai / deepseek / qianwen / local
LLM_PROVIDER = "deepseek"   # 默认使用 DeepSeek（国内速度快）

LLM_CONFIG = {
    "deepseek": {
        "api_key": "YOUR_DEEPSEEK_API_KEY",  # 替换为你的 Key
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "max_tokens": 2000,
    },
    "openai": {
        "api_key": "YOUR_OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "max_tokens": 2000,
    },
    "qianwen": {
        "api_key": "YOUR_QIANWEN_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
        "max_tokens": 2000,
    },
    # 本地 Ollama（完全免费，无需 Key）
    "local": {
        "api_key": "ollama",
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "max_tokens": 1000,
    },
}

# ==================== 版本配置 ====================
CURRENT_VERSION = "0.5"
SUPPORTED_VERSIONS = ["0.5", "1.0"]

# ==================== 爬虫频率（小时）====================
CRAWLER_INTERVALS = {
    "ninja":       2,
    "darkcore":    3,
    "caimogu":     4,
    "chronicles":  6,
    "official":   24,
    "bilibili":  168,
}
DOUYIN_ACE_TIME = "00:00"

# ==================== 爬虫 URL（已核实真实地址）====================
CRAWLER_URLS = {
    # poe.ninja POE2 BD 页面（真实）
    "ninja":      "https://poe.ninja/poe2/builds/",
    # 3DM POE2 新闻攻略（原 d2core.com/poe2/ 已 404，NGA/贴吧封锁爬虫）
    "darkcore":   "https://www.3dmgame.com/games/pathofexile2/",
    # 踩蘑菇 POE2:降临 圈子（真实）
    "caimogu":    "https://www.caimogu.cc/circle/449.html",
    # POE2 台湾编年史 wiki（poe2chronicles.com 不存在，用 poe2db.tw 替代）
    "chronicles": "https://poe2db.tw/us/",
    # POE2 官网
    "official":   "https://www.pathofexile.com/poe2",
    # 老孤独 B站 API（UID 请自行到 B站主页确认后替换）
    "bilibili":   "https://api.bilibili.com/x/space/arc/search?mid=67490632&ps=10&pn=1",
}

# ==================== 悬浮窗配置 ====================
FLOAT_WINDOW = {
    "width":         420,
    "height":        540,
    "alpha":         0.92,
    "position":      "+20+80",
    "always_on_top": True,
    "dark_mode":     True,
}

# ==================== 记忆配置 ====================
MEMORY_ROOT      = "memory/"
BACKUP_KEEP_DAYS = 7

# ==================== 请求配置 ====================
REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36"
}
