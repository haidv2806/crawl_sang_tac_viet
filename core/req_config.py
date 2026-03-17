import json
import os
import requests
import aiohttp
import asyncio
import time
import datetime
from core.config import RATE_LIMIT_BACKOFF_INITIAL, RATE_LIMIT_BACKOFF_MAX

# ---- CAU HINH ----
AUTH_FILE = "auth.json"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
STV_BASE = "https://sangtacviet.app"
TOKEN = "GHLQ"

class REQConfig:
    _cookies_str = None
    _last_load_time = 0
    _is_bypassing = False  # Flag to prevent recursion

    @staticmethod
    def _log_request(method, url, status_code, data_preview):
        """Log request info to log.txt"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Use root dir for log.txt
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(current_dir)
            log_path = os.path.join(root_dir, "log.txt")
            
            # Clean up preview (remove newlines for single line log)
            preview = str(data_preview).replace("\n", " ").replace("\r", "")[:100]
            
            log_line = f"[{timestamp}] {method} {url} - Status: {status_code} - Data: {preview}...\n"
            
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            print(f"Error logging request: {e}")

    @classmethod
    def load_cookies(cls, force=False):
        """Load cookies tu file auth.json and format thành chuỗi cookie cho header."""
        # req_config.py is in core/, auth.json is in root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        auth_path = os.path.join(root_dir, AUTH_FILE)
        
        # Fallback neu dang o doc lap (root)
        if not os.path.exists(auth_path):
            auth_path = os.path.join(current_dir, AUTH_FILE)
        
        # Cache cookie de tranh doc file nhieu lan
        current_time = os.path.getmtime(auth_path) if os.path.exists(auth_path) else 0
        if not force and cls._cookies_str and current_time <= cls._last_load_time:
            return cls._cookies_str

        if not os.path.exists(auth_path):
            return None
        
        try:
            with open(auth_path, "r", encoding="utf-8") as f:
                cookies_dict = json.load(f)
            if not cookies_dict:
                return None
            cls._cookies_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
            cls._last_load_time = current_time
            return cls._cookies_str
        except Exception:
            return None

    @classmethod
    def get_headers(cls, referer=None, extra_headers=None):
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Referer": referer if referer else STV_BASE,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-CH-UA": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
        }
        
        cookie_str = cls.load_cookies()
        if cookie_str:
            headers["Cookie"] = cookie_str
            
        if extra_headers:
            headers.update(extra_headers)
            
        return headers

    @classmethod
    def _do_bypass(cls):
        """Logic bypass captcha (goi sau moi req nhe)."""
        if cls._is_bypassing:
            return

        global TOKEN
        cls._is_bypassing = True
        try:
            # Day la logic tu scripts/bypass_captcha.py
            # De tranh circular import, ta thuc hien request truc tiep o day
            url = f"{STV_BASE}/index.php?ngmar=verifyca"
            data = {
                "ajax": "verifycaptcha",
                "token": TOKEN,
                "purpose": "read",
                "provider": "sangtacviet"
            }
            headers = cls.get_headers(referer=STV_BASE)
            resp = requests.post(url, headers=headers, data=data, timeout=10)
            # Kiem tra ket qua - neu co loi thi hoi user
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}")
            # print("  [auto-bypass] executed.")
        except Exception as e:
            print(f"\n  ⚠️  [bypass-captcha] Thất bại: {e}")
            print(f"  Token hiện tại: {TOKEN}")
            try:
                new_token = input("  → Nhập token mới (Enter để bỏ qua): ").strip()
                if new_token:
                    TOKEN = new_token
                    print(f"  ✅ Đã cập nhật token: {TOKEN}. Thử bypass lại...")
                    # Thu lai voi token moi
                    url = f"{STV_BASE}/index.php?ngmar=verifyca"
                    data = {
                        "ajax": "verifycaptcha",
                        "token": TOKEN,
                        "purpose": "read",
                        "provider": "sangtacviet"
                    }
                    headers = cls.get_headers(referer=STV_BASE)
                    requests.post(url, headers=headers, data=data, timeout=10)
                    print("  ✅ Bypass lại hoàn tất.")
                else:
                    print("  ⏭️  Bỏ qua bypass.")
            except Exception as e2:
                print(f"  ❌ Bypass lại cũng thất bại: {e2}")
        finally:
            cls._is_bypassing = False

    @classmethod
    async def async_do_bypass(cls):
        """Logic bypass captcha (async version)."""
        if cls._is_bypassing:
            return
            
        cls._is_bypassing = True
        try:
            url = f"{STV_BASE}/index.php?ngmar=verifyca"
            data = {
                "ajax": "verifycaptcha",
                "token": TOKEN,
                "purpose": "read",
                "provider": "sangtacviet"
            }
            headers = cls.get_headers(referer=STV_BASE)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data, timeout=10) as resp:
                    await resp.text() # Ensure it completes
        except Exception:
            pass
        finally:
            cls._is_bypassing = False

    @classmethod
    def request(cls, method, url, referer=None, **kwargs):
        """Sync requests wrapper with fixed backoff for 429."""
        while True:
            headers = cls.get_headers(referer=referer, extra_headers=kwargs.pop("headers", None))
            # Put headers back into kwargs for the case we retry
            kwargs["headers"] = headers
            
            resp = requests.request(method, url, **kwargs)
            
            # Log request
            cls._log_request(method, url, resp.status_code, resp.text)
            
            if resp.status_code == 429 and "sangtacviet.app" in url:
                print(f"  ⚠️ Rate Limit (429) cho {url}. Cho {RATE_LIMIT_BACKOFF_INITIAL}s...")
                time.sleep(RATE_LIMIT_BACKOFF_INITIAL)
                continue
                
            # Goi bypass sau khi req xong (chi neu thanh cong hoac loi khac 429)
            if not cls._is_bypassing:
                cls._do_bypass()
                
            return resp

    @classmethod
    async def async_request(cls, method, url, session=None, referer=None, **kwargs):
        """Async aiohttp requests wrapper."""
        headers = cls.get_headers(referer=referer, extra_headers=kwargs.pop("headers", None))
        return headers

# Helper functions for convenience
def req_get(url, referer=None, **kwargs):
    return REQConfig.request("GET", url, referer=referer, **kwargs)

def req_post(url, data=None, json=None, referer=None, **kwargs):
    return REQConfig.request("POST", url, data=data, json=json, referer=referer, **kwargs)

async def async_req_get(session, url, referer=None, **kwargs):
    while True:
        headers = REQConfig.get_headers(referer=referer, extra_headers=kwargs.pop("headers", None))
        kwargs["headers"] = headers
        
        resp = await session.get(url, **kwargs)
        
        # Log request
        try:
            text = await resp.text()
            REQConfig._log_request("GET", url, resp.status, text)
        except:
            REQConfig._log_request("GET", url, resp.status, "Error reading content")
            
        if resp.status == 429 and "sangtacviet.app" in url:
            print(f"  ⚠️ Rate Limit (429) cho {url}. Cho {RATE_LIMIT_BACKOFF_INITIAL}s...")
            await asyncio.sleep(RATE_LIMIT_BACKOFF_INITIAL)
            continue
            
        # Goi bypass sau moi req async
        REQConfig._do_bypass()
        return resp

async def async_req_post(session, url, data=None, json=None, referer=None, **kwargs):
    while True:
        headers = REQConfig.get_headers(referer=referer, extra_headers=kwargs.pop("headers", None))
        kwargs["headers"] = headers
        
        resp = await session.post(url, data=data, json=json, **kwargs)
        
        # Log request
        try:
            text = await resp.text()
            REQConfig._log_request("POST", url, resp.status, text)
        except:
            REQConfig._log_request("POST", url, resp.status, "Error reading content")
            
        if resp.status == 429 and "sangtacviet.app" in url:
            print(f"  ⚠️ Rate Limit (429) cho {url}. Cho {RATE_LIMIT_BACKOFF_INITIAL}s...")
            await asyncio.sleep(RATE_LIMIT_BACKOFF_INITIAL)
            continue
            
        # Goi bypass sau moi req async
        REQConfig._do_bypass()
        return resp
