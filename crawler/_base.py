# crawler/_base.py — 爬虫公共基类（统一请求、重试、解析）

import time
from typing import Optional
from config import REQUEST_TIMEOUT, REQUEST_HEADERS

try:
    import requests as _requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def fetch_html(url: str, retries: int = 3, encoding: str = "utf-8") -> Optional[str]:
    """
    通用 HTTP 请求，带重试机制。
    优先使用 requests（兼容 Windows https），返回页面文本，失败返回 None。
    """
    if not HAS_REQUESTS:
        print("❌ 未安装 requests 库，请执行：pip install requests")
        return None

    for attempt in range(1, retries + 1):
        try:
            resp = _requests.get(
                url,
                headers=REQUEST_HEADERS,
                timeout=REQUEST_TIMEOUT,
                verify=True,
            )
            resp.raise_for_status()
            resp.encoding = encoding
            return resp.text
        except _requests.exceptions.HTTPError as e:
            print(f"⚠️ HTTP {e.response.status_code} 爬取失败（第{attempt}次）：{url}")
        except _requests.exceptions.ConnectionError:
            print(f"⚠️ 无法连接到 {url}（第{attempt}次），请检查网络或目标站是否可访问")
        except _requests.exceptions.Timeout:
            print(f"⚠️ 请求超时（第{attempt}次）：{url}")
        except Exception as e:
            print(f"⚠️ 请求异常（第{attempt}次）：{e}")
        if attempt < retries:
            time.sleep(3 * attempt)
    return None


def safe_text(element, default: str = "") -> str:
    """安全地从 BeautifulSoup 元素提取文本。"""
    if element is None:
        return default
    return element.get_text(strip=True)
