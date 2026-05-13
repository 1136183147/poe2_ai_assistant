# crawler/ninja_crawler.py — poe.ninja 官方 API（稳定可靠）

import json
from datetime import datetime
from utils.memory_manager import save_memory

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

_HDR = {"User-Agent": "POE2-AI-Assistant/2.0"}

def _get_league() -> str:
    try:
        r = requests.get("https://api.poe.ninja/api/data/getindexstate", headers=_HDR, timeout=10)
        leagues = r.json().get("economyLeagues", [])
        poe2 = [l for l in leagues if l.get("realm") == "poe2" and "HC" not in l.get("name","")]
        if poe2:
            return poe2[0]["name"]
    except Exception:
        pass
    return "Dawn"

def crawl_poe2_ninja() -> str:
    if not HAS_REQUESTS:
        return "❌ 未安装 requests"
    now    = datetime.now().strftime("%Y-%m-%d %H:%M")
    league = _get_league()

    # BD 数据
    builds = []
    try:
        r = requests.get(
            f"https://poe.ninja/api/data/getbuildoverview?overview={league}&type=exp&language=en",
            headers=_HDR, timeout=15)
        data = r.json()
        skill_map = {s["id"]: s["name"] for s in data.get("activeSkills", [])}
        for i, c in enumerate(data.get("expData", [])[:30], 1):
            builds.append({
                "rank": i,
                "class": c.get("className",""),
                "skill": skill_map.get(c.get("mainSkillId",0), "未知"),
                "usage": f"{c.get('count',0)}人",
            })
    except Exception as e:
        builds = [{"note": f"BD获取失败: {e}"}]

    # 价格数据
    prices = {}
    try:
        r = requests.get(
            f"https://poe.ninja/api/data/currencyoverview?league={league}&type=Currency",
            headers=_HDR, timeout=15)
        for item in r.json().get("lines", [])[:30]:
            name = item.get("currencyTypeName","")
            val  = item.get("chaosEquivalent", 0)
            if name and val:
                prices[name] = f"{val:.1f}c"
    except Exception as e:
        prices = {"error": str(e)}

    save_memory("meta", "top_builds.json", {"_update": now, "_league": league, "builds": builds})
    save_memory("meta", "price_trend.json", {"_update": now, "_league": league, "prices": prices})
    return f"✅ poe.ninja({league})：{len(builds)}条BD / {len(prices)}条价格"
