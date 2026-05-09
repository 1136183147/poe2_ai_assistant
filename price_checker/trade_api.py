# price_checker/trade_api.py — POE2 交易API封装（支持多服务器）

import json
import time
from typing import Optional, Dict, List, Any, Tuple

try:
    import requests as _requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from config import TRADE_API, POESESSID, DEFAULT_SERVER, DEFAULT_LEAGUE, REQUEST_TIMEOUT


class TradeAPI:
    """POE2 交易 API 封装类"""
    
    def __init__(self, server: str = DEFAULT_SERVER, league: str = DEFAULT_LEAGUE):
        self.server = server
        self.league = league
        self._session = None
        self._init_session()
    
    def _init_session(self):
        """初始化请求会话"""
        if not HAS_REQUESTS:
            raise RuntimeError("未安装 requests 库，请执行：pip install requests")
        
        self._session = _requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Cookie": f"POESESSID={POESESSID}",
        })
    
    def _get_api_urls(self) -> Dict[str, str]:
        """获取当前服务器的API地址"""
        api_info = TRADE_API.get(self.server)
        if not api_info:
            raise ValueError(f"未知服务器类型: {self.server}")
        return api_info
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        """通用请求方法，带重试和错误处理"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self._session.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
                response.raise_for_status()
                return response.json()
            except _requests.exceptions.HTTPError as e:
                if response.status_code == 403:
                    return {"error": "认证失败", "message": "请检查 POESESSID 是否正确"}
                print(f"HTTP错误 {response.status_code} (尝试 {attempt+1}/{max_retries}): {url}")
            except _requests.exceptions.ConnectionError:
                print(f"连接失败 (尝试 {attempt+1}/{max_retries}): {url}")
            except _requests.exceptions.Timeout:
                print(f"请求超时 (尝试 {attempt+1}/{max_retries}): {url}")
            except Exception as e:
                print(f"请求异常 (尝试 {attempt+1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        
        return None
    
    def search_items(self, query: Dict) -> Optional[Dict]:
        """搜索装备"""
        api_urls = self._get_api_urls()
        search_url = api_urls["search_url"].format(league=self.league)
        return self._make_request("POST", search_url, json=query)
    
    def fetch_items(self, item_ids: List[str]) -> Optional[Dict]:
        """获取装备详情"""
        api_urls = self._get_api_urls()
        ids_str = ",".join(item_ids)
        fetch_url = api_urls["fetch_url"].format(ids=ids_str)
        return self._make_request("GET", fetch_url)
    
    def get_exchange_rate(self, target_currency: str = "chaos") -> Optional[float]:
        """获取通货兑换率"""
        api_urls = self._get_api_urls()
        exchange_url = api_urls["exchange_url"].format(league=self.league)
        
        query = {
            "exchange": {
                "want": [{"name": target_currency}],
                "have": [{"name": "Divine Orb"}]
            }
        }
        
        result = self._make_request("POST", exchange_url, json=query)
        if result and "result" in result:
            # 取前几个价格的平均值作为参考
            rates = []
            for entry in result["result"][:5]:
                if "listing" in entry and "price" in entry["listing"]:
                    price = entry["listing"]["price"]
                    if "amount" in price and "exchange" in price:
                        rates.append(price["exchange"] / price["amount"])
            if rates:
                return sum(rates) / len(rates)
        return None


class PriceChecker:
    """装备查价器"""
    
    def __init__(self, server: str = DEFAULT_SERVER, league: str = DEFAULT_LEAGUE):
        self.api = TradeAPI(server, league)
        self.server_name = TRADE_API.get(server, {}).get("name", "未知服务器")
    
    def _build_stat_filter(self, affixes: List[str]) -> List[Dict]:
        """
        构建词缀过滤器
        
        Args:
            affixes: 词缀列表
        
        Returns:
            词缀过滤器列表
        """
        stats = []
        
        for affix in affixes:
            affix = affix.strip()
            if not affix:
                continue
            
            # 尝试解析词缀中的数值
            import re
            
            # 提取数值范围（如 "+10-20 力量"）
            match = re.search(r'([+-]?\d+)\s*[-~]\s*([+-]?\d+)', affix)
            if match:
                min_val = int(match.group(1))
                max_val = int(match.group(2))
            else:
                # 尝试提取单个数值
                match = re.search(r'([+-]?\d+)', affix)
                if match:
                    min_val = int(match.group(1))
                    max_val = min_val + 10  # 给予一定容差
                else:
                    min_val = 0
                    max_val = 999
            
            stats.append({
                "type": "and",
                "filters": [{
                    "id": "explicit_mods",
                    "value": {
                        "min": min_val,
                        "max": max_val,
                        "text": affix,
                        "disabled": False
                    },
                    "disabled": False
                }]
            })
        
        return stats
    
    def check_price(self, item_name: str, item_type: str = None, 
                    affixes: List[str] = None, filters: Dict = None, limit: int = 10) -> Tuple[str, List[Dict]]:
        """
        查询装备价格
        
        Args:
            item_name: 装备名称
            item_type: 装备类型（如 "Weapon", "Armor", "Helmet" 等）
            affixes: 词缀列表（用于精确搜索）
            filters: 额外过滤条件
            limit: 返回结果数量
        
        Returns:
            (错误信息或成功提示, 价格列表)
        """
        if not POESESSID or POESESSID.startswith("YOUR_"):
            return "❌ 请先配置 POESESSID（点击「配置」按钮）", []
        
        # 构建搜索查询
        query = {
            "query": {
                "status": {"option": "online"},
                "name": item_name,
                "type": item_type if item_type else "",
                "filters": filters or {}
            },
            "sort": {"price": "asc"},
            "limit": limit
        }
        
        # 添加词缀过滤
        if affixes and len(affixes) > 0:
            stats_filter = self._build_stat_filter(affixes)
            if stats_filter:
                query["query"]["filters"]["stats"] = {"type": "and", "filters": stats_filter}
        
        # 执行搜索
        search_result = self.api.search_items(query)
        if not search_result:
            return f"❌ 搜索失败，请检查网络或 API 配置", []
        
        if "error" in search_result:
            return f"❌ {search_result.get('message', '未知错误')}", []
        
        if "result" not in search_result or len(search_result["result"]) == 0:
            return f"ℹ️ 未找到名为 '{item_name}' 的装备", []
        
        # 获取详情
        item_ids = [r["id"] for r in search_result["result"][:min(limit, len(search_result["result"]))]]
        fetch_result = self.api.fetch_items(item_ids)
        
        if not fetch_result or "items" not in fetch_result:
            return "❌ 获取装备详情失败", []
        
        # 解析价格
        prices = []
        for item_data in fetch_result["items"]:
            item = item_data.get("item", {})
            listing = item_data.get("listing", {})
            
            price_info = listing.get("price", {})
            currency = price_info.get("currency", "unknown")
            amount = price_info.get("amount", 0)
            
            # 获取装备基础信息
            item_info = {
                "name": item.get("name", ""),
                "type": item.get("type", ""),
                "level": item.get("level", 0),
                "rarity": item.get("rarity", ""),
                "currency": currency,
                "price": amount,
                "seller": listing.get("account", {}).get("name", "unknown"),
                "online": listing.get("status", {}).get("option") == "online",
            }
            
            # 添加词缀信息
            properties = item.get("properties", [])
            for prop in properties:
                name = prop.get("name", "")
                values = prop.get("values", [])
                if values:
                    item_info[name] = values[0][0]
            
            prices.append(item_info)
        
        return f"✅ 在 {self.server_name} [{self.api.league}] 找到 {len(prices)} 个匹配结果", prices
    
    def format_price_result(self, message: str, prices: List[Dict]) -> str:
        """格式化价格结果为可读文本"""
        result = [message]
        
        if prices:
            result.append("")
            result.append("┌─────────────────────────────────────────")
            
            for i, item in enumerate(prices, 1):
                rarity_color = {
                    "Normal": "白",
                    "Magic": "蓝",
                    "Rare": "黄",
                    "Unique": "暗金",
                }.get(item["rarity"], "未知")
                
                online_mark = "🟢" if item["online"] else "🔴"
                result.append(f"│ {i:2d}. [{rarity_color}] {item['name'] or item['type']}")
                result.append(f"│    等级: {item['level']} | 价格: {item['price']} {item['currency']}")
                result.append(f"│    卖家: {item['seller']} {online_mark}")
                
                # 显示关键属性
                key_props = ["Physical Damage", "Elemental Damage", "Critical Strike Chance", 
                            "Strength", "Dexterity", "Intelligence", "Life"]
                props_shown = []
                for prop in key_props:
                    if prop in item:
                        props_shown.append(f"{prop}: {item[prop]}")
                if props_shown:
                    result.append(f"│    属性: {', '.join(props_shown)}")
                
                result.append("│")
            
            result.append("└─────────────────────────────────────────")
            
            # 统计信息
            chaos_prices = [p["price"] for p in prices if p["currency"] == "chaos"]
            if chaos_prices:
                avg_price = sum(chaos_prices) / len(chaos_prices)
                min_price = min(chaos_prices)
                max_price = max(chaos_prices)
                result.append(f"📊 价格统计 (Chaos): 最低 {min_price}, 最高 {max_price}, 平均 {avg_price:.1f}")
        
        return "\n".join(result)


def quick_check(item_name: str, server: str = None, league: str = None) -> str:
    """快速查价接口"""
    checker = PriceChecker(
        server=server or DEFAULT_SERVER,
        league=league or DEFAULT_LEAGUE
    )
    message, prices = checker.check_price(item_name)
    return checker.format_price_result(message, prices)


def get_server_list() -> List[Tuple[str, str]]:
    """获取服务器列表"""
    return [(key, TRADE_API[key]["name"]) for key in TRADE_API]
