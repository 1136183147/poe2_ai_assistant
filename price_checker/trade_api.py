# price_checker/trade_api.py — POE2 官方交易 API（国际服 / 国服 / 台服）

import json
import re
import time
from typing import Optional, Dict, List, Tuple

try:
    import requests as _requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from config import TRADE_API, POESESSID, DEFAULT_SERVER, DEFAULT_LEAGUE, REQUEST_TIMEOUT

# POE2 词条 stat_id 对照表（用于 API 过滤）
STAT_ID_MAP = {
    "maximum life":              "explicit.stat_3299347043",
    "maximum mana":              "explicit.stat_1050105434",
    "maximum energy shield":     "explicit.stat_4015621042",
    "fire resistance":           "explicit.stat_3372524247",
    "cold resistance":           "explicit.stat_4220027924",
    "lightning resistance":      "explicit.stat_1671376347",
    "chaos resistance":          "explicit.stat_2923486259",
    "all elemental resistances": "explicit.stat_2901986750",
    "physical damage":           "explicit.stat_1509134228",
    "attack speed":              "explicit.stat_210067635",
    "cast speed":                "explicit.stat_4277795662",
    "movement speed":            "explicit.stat_2250533757",
    "critical strike chance":    "explicit.stat_587431675",
    "strength":                  "explicit.stat_4080418644",
    "dexterity":                 "explicit.stat_3261801346",
    "intelligence":              "explicit.stat_328541901",
    "all attributes":            "explicit.stat_1379411836",
}

RARITY_MAP = {"普通": "normal", "魔法": "magic", "稀有": "rare", "传奇": "unique"}
CURRENCY_CN = {
    "exalted": "崇高石", "chaos": "混沌石", "divine": "神圣石",
    "gold": "金币", "mirror": "镜子", "ancient": "远古石",
}


class TradeAPI:
    """POE2 官方交易 API 封装"""

    def __init__(self, server: str = DEFAULT_SERVER, league: str = DEFAULT_LEAGUE):
        self.server = server
        self.league = league
        self._cfg = TRADE_API.get(server, TRADE_API["international"])
        self._session = None
        self._last_req = 0.0
        self._init_session()

    def _init_session(self):
        if not HAS_REQUESTS:
            return
        self._session = _requests.Session()
        self._session.headers.update({
            "User-Agent": "POE2-AI-Assistant/2.0 (personal tool)",
            "Accept":     "application/json",
            "Content-Type": "application/json",
        })
        if POESESSID and not POESESSID.startswith("YOUR_"):
            self._session.headers["Cookie"] = f"POESESSID={POESESSID}"

    def _rate_limit(self):
        """两次请求间隔至少 1.5 秒，避免被限流"""
        wait = 1.5 - (time.time() - self._last_req)
        if wait > 0:
            time.sleep(wait)
        self._last_req = time.time()

    def _request(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        if not HAS_REQUESTS or not self._session:
            return None
        self._rate_limit()
        for attempt in range(3):
            try:
                resp = self._session.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
                if resp.status_code == 403:
                    return {"error": "403 认证失败，请重新获取 POESESSID（登录官网 → F12 → Application → Cookies）"}
                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", 60))
                    return {"error": f"429 请求过于频繁，请等待 {wait} 秒后重试"}
                resp.raise_for_status()
                return resp.json()
            except _requests.exceptions.ConnectionError:
                if attempt == 2:
                    return {"error": f"无法连接到 {url}，请检查网络"}
                time.sleep(3)
            except Exception as e:
                return {"error": str(e)}
        return None

    def get_leagues(self) -> List[str]:
        """获取当前可用赛季列表"""
        leagues_url = self._cfg.get("leagues_url",
            f"{self._cfg['base_url']}/data/leagues")
        data = self._request("GET", leagues_url)
        if not data or "result" not in data:
            return [DEFAULT_LEAGUE, "Standard"]
        result = data["result"]
        active = [l["id"] for l in result
                  if l.get("id") not in ("Standard", "Hardcore")
                  and "HC" not in l.get("id", "")]
        return active if active else [l["id"] for l in result[:3]]

    def search_items(self, query: Dict) -> Optional[Dict]:
        url = self._cfg["search_url"].format(league=self.league)
        return self._request("POST", url, json=query)

    def fetch_items(self, item_ids: List[str], search_id: str = "") -> Optional[Dict]:
        ids_str = ",".join(item_ids[:10])
        url = self._cfg["fetch_url"].format(ids=ids_str)
        params = {"realm": "poe2"}
        if search_id:
            params["query"] = search_id
        return self._request("GET", url, params=params)


class PriceChecker:
    """装备查价器"""

    def __init__(self, server: str = DEFAULT_SERVER, league: str = DEFAULT_LEAGUE):
        self.api = TradeAPI(server, league)
        self.server_name = TRADE_API.get(server, {}).get("name", server)

    def _build_query(self, item_name: str, base_type: str,
                     rarity: str, affixes: List[str]) -> Dict:
        """构建 POE2 交易 API 查询体"""
        query: Dict = {
            "query": {
                "status": {"option": "online"},
                "stats":  [{"type": "and", "filters": []}],
            },
            "sort": {"price": "asc"},
        }

        if item_name:
            query["query"]["name"] = item_name
        if base_type:
            query["query"]["type"] = base_type

        # 稀有度过滤
        rarity_en = RARITY_MAP.get(rarity, "")
        if rarity_en:
            query["query"].setdefault("filters", {})
            query["query"]["filters"]["type_filters"] = {
                "filters": {"rarity": {"option": rarity_en}}
            }

        # 词条过滤（最多取3条，太多会搜不到结果）
        stat_filters = []
        for affix in affixes[:3]:
            affix_lower = affix.lower()
            stat_id = None
            for keyword, sid in STAT_ID_MAP.items():
                if keyword in affix_lower:
                    stat_id = sid
                    break
            if not stat_id:
                continue
            # 提取数值
            nums = re.findall(r"[\d.]+", affix)
            if nums:
                min_val = float(nums[0]) * 0.8  # 放宽20%容差
                stat_filters.append({
                    "id": stat_id,
                    "value": {"min": round(min_val)},
                    "disabled": False,
                })

        if stat_filters:
            query["query"]["stats"][0]["filters"] = stat_filters

        return query

    def check_price(self, item_name: str = "", base_type: str = "",
                    rarity: str = "", affixes: List[str] = None,
                    limit: int = 10) -> Tuple[str, List[Dict]]:
        """查价主函数"""
        if not POESESSID or POESESSID.startswith("YOUR_"):
            return "❌ 请先配置 POESESSID（点击主界面「配置」按钮）", []

        query = self._build_query(item_name, base_type, rarity, affixes or [])

        # Step 1：搜索
        search_result = self.api.search_items(query)
        if not search_result:
            return "❌ 搜索失败，请检查网络", []
        if "error" in search_result:
            return f"❌ {search_result['error']}", []

        result_ids = search_result.get("result", [])
        search_id  = search_result.get("id", "")
        total      = search_result.get("total", 0)

        if not result_ids:
            trade_url = self._cfg_url(search_id)
            return f"ℹ️ 未找到符合条件的挂售（共搜索到 {total} 件）\n尝试减少词条限制后重新搜索", []

        # Step 2：获取详情
        fetch_ids = result_ids[:min(limit, 10)]
        fetch_result = self.api.fetch_items(fetch_ids, search_id)
        if not fetch_result:
            return "❌ 获取价格详情失败", []
        if "error" in fetch_result:
            return f"❌ {fetch_result['error']}", []

        prices = []
        for entry in fetch_result.get("result", []):
            listing = entry.get("listing", {})
            item    = entry.get("item", {})
            price_info = listing.get("price", {})
            if not price_info:
                continue
            prices.append({
                "amount":   price_info.get("amount", "?"),
                "currency": price_info.get("currency", "?"),
                "currency_cn": CURRENCY_CN.get(price_info.get("currency",""), price_info.get("currency","")),
                "account":  listing.get("account", {}).get("name", "?"),
                "online":   listing.get("account", {}).get("online", {}).get("status") == "online",
                "whisper":  listing.get("whisper", ""),
                "item_name": item.get("name", "") or item.get("typeLine", ""),
                "item_level": item.get("ilvl", 0),
            })

        return f"✅ {self.server_name}·{self.api.league} 找到 {total} 件，显示最低价 {len(prices)} 件", prices

    def _cfg_url(self, search_id: str = "") -> str:
        base = self.api._cfg.get("trade_site", "https://www.pathofexile.com/trade2")
        if search_id:
            return f"{base}/search/poe2/{self.api.league}/{search_id}"
        return f"{base}/search/poe2/{self.api.league}"

    def format_result(self, message: str, prices: List[Dict],
                      search_id: str = "") -> str:
        lines = [message, ""]
        if not prices:
            lines.append("没有找到挂售，建议放宽搜索条件")
        else:
            lines.append("┌──────────────────────────────────────")
            for i, p in enumerate(prices, 1):
                online = "🟢" if p.get("online") else "⚫"
                c_cn   = p.get("currency_cn") or p.get("currency")
                lines.append(f"│ {i:2d}. {p['amount']} {c_cn}  {online} {p['account']}")
                if p.get("item_name"):
                    lines.append(f"│     {p['item_name']}")
            lines.append("└──────────────────────────────────────")

            # 中位价参考
            try:
                mid = prices[len(prices) // 2]
                c_cn = mid.get("currency_cn") or mid.get("currency")
                lines.append(f"\n📊 中位参考价：{mid['amount']} {c_cn}")
            except Exception:
                pass

        if search_id:
            lines.append(f"\n🔗 完整结果：{self._cfg_url(search_id)}")
        return "\n".join(lines)


# ── 工具函数 ─────────────────────────────────

def quick_check(item_name: str, server: str = None, league: str = None) -> str:
    checker = PriceChecker(
        server=server or DEFAULT_SERVER,
        league=league or DEFAULT_LEAGUE,
    )
    msg, prices = checker.check_price(item_name=item_name)
    return checker.format_result(msg, prices)


def get_server_list() -> List[Tuple[str, str]]:
    return [(k, v["name"]) for k, v in TRADE_API.items()]
