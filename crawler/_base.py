# crawler/_base.py — 爬虫公共基类（统一请求、重试、解析、数据验证）

import time
from typing import Optional, Tuple
from config import REQUEST_TIMEOUT

try:
    import requests as _requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# 增强的请求头，模拟真实浏览器
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,image/apng,*/*;q=0.8,"
              "application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


def fetch_html(url: str, retries: int = 3, encoding: str = "utf-8", 
               headers: dict = None) -> Tuple[Optional[str], str]:
    """
    通用 HTTP 请求，带重试机制和数据验证。
    优先使用 requests（兼容 Windows https），返回页面文本和状态信息。
    
    :param url: 目标 URL
    :param retries: 重试次数
    :param encoding: 编码
    :param headers: 自定义请求头
    :return: (页面文本, 状态信息)，失败时页面文本为 None
    """
    if not HAS_REQUESTS:
        return None, "❌ 未安装 requests 库，请执行：pip install requests"

    # 合并默认请求头和自定义请求头
    final_headers = DEFAULT_HEADERS.copy()
    if headers:
        final_headers.update(headers)

    for attempt in range(1, retries + 1):
        try:
            resp = _requests.get(
                url,
                headers=final_headers,
                timeout=REQUEST_TIMEOUT,
                verify=True,
                allow_redirects=True,
            )
            resp.raise_for_status()
            
            # 检查内容类型
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type and "json" not in content_type:
                return None, f"⚠️ 返回内容不是 HTML/JSON，类型：{content_type}"
            
            # 检查内容长度
            content_length = len(resp.content)
            if content_length < 100:
                return None, f"⚠️ 返回内容过短（{content_length} 字节），可能被屏蔽"
            
            resp.encoding = encoding
            return resp.text, f"✅ 请求成功（{content_length} 字节）"
            
        except _requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            error_msg = f"HTTP {status_code} 错误"
            if status_code == 403:
                error_msg = "403 被拒绝（可能需要登录或被反爬）"
            elif status_code == 404:
                error_msg = "404 页面不存在"
            elif status_code == 503:
                error_msg = "503 服务不可用"
            print(f"⚠️ {error_msg}（第{attempt}次）：{url}")
            
        except _requests.exceptions.ConnectionError:
            print(f"⚠️ 无法连接到 {url}（第{attempt}次），请检查网络")
            
        except _requests.exceptions.Timeout:
            print(f"⚠️ 请求超时（第{attempt}次）：{url}")
            
        except _requests.exceptions.SSLError:
            print(f"⚠️ SSL 证书错误（第{attempt}次）：{url}")
            
        except Exception as e:
            print(f"⚠️ 请求异常（第{attempt}次）：{str(e)[:100]}")
            
        if attempt < retries:
            time.sleep(3 * attempt)
    
    return None, f"❌ 所有 {retries} 次请求均失败"


def safe_text(element, default: str = "") -> str:
    """安全地从 BeautifulSoup 元素提取文本。"""
    if element is None:
        return default
    return element.get_text(strip=True)


def validate_data(data: list | dict, min_items: int = 1) -> Tuple[bool, str]:
    """
    验证爬取数据是否有效。
    
    :param data: 待验证的数据
    :param min_items: 最小有效条目数
    :return: (是否有效, 验证信息)
    """
    if data is None:
        return False, "数据为 None"
    
    if isinstance(data, list):
        if len(data) == 0:
            return False, "数据列表为空"
        if len(data) < min_items:
            return False, f"数据条目不足（{len(data)} < {min_items}）"
        
        # 检查数据质量
        empty_count = 0
        for item in data[:10]:  # 抽样检查前10条
            if isinstance(item, dict):
                # 检查字典是否有有效内容
                if not item or all(v in ["", "-", None, "未知"] for v in item.values()):
                    empty_count += 1
            elif isinstance(item, str):
                if not item.strip() or len(item.strip()) < 2:
                    empty_count += 1
        
        if empty_count >= len(data[:10]) * 0.5:
            return False, f"超过 50% 的数据为空或无效"
        
    elif isinstance(data, dict):
        if not data:
            return False, "数据字典为空"
        # 检查是否只有元数据字段
        meta_keys = {"_meta", "_last_update", "_source", "note", "reference_links"}
        if set(data.keys()).issubset(meta_keys):
            return False, "只有元数据，没有实际内容"
    
    return True, f"数据有效（{len(data) if isinstance(data, list) else len(data.keys())} 条）"


def extract_text_with_fallback(soup, selectors: list, default: str = "") -> str:
    """
    使用多个选择器提取文本，增加容错性。
    
    :param soup: BeautifulSoup 对象
    :param selectors: 选择器列表（按优先级）
    :param default: 默认值
    :return: 提取的文本
    """
    for selector in selectors:
        try:
            element = soup.select_one(selector)
            if element:
                text = safe_text(element)
                if text and len(text) > 1:
                    return text
        except Exception:
            continue
    return default
