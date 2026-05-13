# crawler/_base.py — 公共请求基类（用 requests，兼容 Windows https）

import time
from config import REQUEST_TIMEOUT, REQUEST_HEADERS

try:
    import requests as _req
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

def fetch_html(url: str, retries: int = 3, encoding: str = "utf-8") -> str | None:
    if not HAS_REQUESTS:
        print("❌ 未安装 requests：pip install requests")
        return None
    for attempt in range(1, retries + 1):
        try:
            r = _req.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT, verify=True)
            r.raise_for_status()
            r.encoding = encoding
            return r.text
        except _req.exceptions.HTTPError as e:
            print(f"⚠️ HTTP {e.response.status_code}（第{attempt}次）：{url}")
        except _req.exceptions.ConnectionError:
            print(f"⚠️ 无法连接（第{attempt}次）：{url}")
        except Exception as e:
            print(f"⚠️ 请求异常（第{attempt}次）：{e}")
        if attempt < retries:
            time.sleep(3 * attempt)
    return None

def safe_text(el, default="") -> str:
    if el is None:
        return default
    return el.get_text(strip=True)
