# stv_browser.py - Quản lý Playwright Browser cho sangtacviet.app

import asyncio
import os
import json
import random
from playwright.async_api import async_playwright, BrowserContext, Page
from core.config import HEADLESS, BROWSER_TIMEOUT, USER_DATA_DIR
import time

class STVBrowser:
    _instance = None
    _playwright = None
    _browser = None
    _context: BrowserContext = None

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            print("🌐 Khởi tạo trình duyệt Playwright...")
            cls._instance = STVBrowser()
            await cls._instance._init_browser()
            print("✅ Trình duyệt đã sẵn sàng.")
        return cls._instance

    async def _init_browser(self):
        self._playwright = await async_playwright().start()
        # Dùng launch_persistent_context để lưu cookies/session
        if not os.path.exists(USER_DATA_DIR):
            os.makedirs(USER_DATA_DIR)
            
        for i in range(3):
            try:
                self._context = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir=USER_DATA_DIR,
                    headless=HEADLESS,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 900},
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-infobars",
                        "--window-position=0,0",
                        "--ignore-certificate-errors",
                        "--ignore-certificate-errors-spki-list",
                    ]
                )
                break
            except Exception as e:
                print(f"⚠️ Thử lại khởi tạo browser ({i+1}/3): {e}")
                await asyncio.sleep(2)
        
        if not self._context:
             raise Exception("Không thể khởi tạo browser sau 3 lần thử.")
        self._context.set_default_timeout(BROWSER_TIMEOUT)
        
        # Load cookies từ auth.json
        auth_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "auth.json")
        if os.path.exists(auth_path):
            try:
                with open(auth_path, "r", encoding="utf-8") as f:
                    auth_data = json.load(f)
                
                cookies = []
                for name, value in auth_data.items():
                    cookies.append({
                        "name": name,
                        "value": str(value),
                        "domain": "sangtacviet.app",
                        "path": "/"
                    })
                
                if cookies:
                    await self._context.add_cookies(cookies)
                    print(f"✅ Đã nạp {len(cookies)} cookies từ auth.json")
            except Exception as e:
                print(f"⚠️ Lỗi khi nạp cookies từ auth.json: {e}")
        
        # Bypass webdriver detection
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['vi-VN', 'vi', 'en-US', 'en']});
            window.chrome = { runtime: {} };
        """)

    async def get_context(self) -> BrowserContext:
        """Trả về BrowserContext, khởi tạo nếu cần."""
        is_closed = True
        if self._context:
            try:
                _ = self._context.pages
                is_closed = False
            except Exception:
                is_closed = True
        
        if is_closed:
            await self._init_browser()
        return self._context

    async def get_page(self) -> Page:
        context = await self.get_context()
        return await context.new_page()

    async def get_cookie_string(self, url: str = None) -> str:
        """Lấy cookie từ context dưới dạng chuỗi header, có thể lọc theo URL."""
        context = await self.get_context()
        try:
            if url:
                cookies = await context.cookies(urls=[url])
            else:
                cookies = await context.cookies()
            return "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        except Exception as e:
            print(f"⚠️ Lỗi khi lấy cookies: {e}")
            return ""

    async def close(self):
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()
        STVBrowser._instance = None

    async def simulate_human_interaction(self, page: Page, duration: float = 3.0):
        """Giả lập chuột di chuyển lờ đờ và cuộn trang nhẹ nhàng."""
        print(f"🖱️ Đang giả lập tương tác người dùng ({duration}s)...")
        try:
            viewport = page.viewport_size
            if not viewport:
                viewport = {"width": 1280, "height": 900}
            
            end_time = asyncio.get_event_loop().time() + duration
            
            while asyncio.get_event_loop().time() < end_time:
                # Di chuyển chuột đến một vị trí ngẫu nhiên
                target_x = random.randint(0, viewport["width"])
                target_y = random.randint(0, viewport["height"])
                
                # Di chuyển mượt hơn bằng cách chia nhỏ quãng đường
                # Playwright's mouse.move already has 'steps', but we can add our own randomness
                steps = random.randint(5, 15)
                await page.mouse.move(target_x, target_y, steps=steps)
                
                # Đôi khi cuộn chuột
                if random.random() < 0.3:
                    scroll_amount = random.randint(100, 500)
                    await page.mouse.wheel(0, scroll_amount if random.random() > 0.5 else -scroll_amount)
                
                # Nghỉ ngẫu nhiên "lờ đờ"
                await asyncio.sleep(random.uniform(0.2, 0.8))
            
            print("✅ Kết thúc giả lập tương tác.")
        except Exception as e:
            print(f"⚠️ Lỗi khi giả lập tương tác: {e}")

    async def get_content(self, url: str, wait_selector: str = None, click_selectors: list[str] = None, extra_wait: float = 3.0) -> str:
        """Mở URL, chờ selector (nếu có), click các element (nếu có) và trả về HTML content."""
        print(f"🌍 Đang điều hướng đến: {url}")
        page = await self.get_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT)
            
            if wait_selector:
                print(f"⏳ Chờ selector: {wait_selector}")
                try:
                    await page.wait_for_selector(wait_selector, state="attached", timeout=30000)
                    print(f"✅ Selector '{wait_selector}' đã xuất hiện.")
                except Exception:
                    print(f"⚠️ Selector '{wait_selector}' chưa xuất hiện sau 30s, chờ thêm...")
                    await asyncio.sleep(5)
                    found = await page.query_selector(wait_selector)
                    if not found:
                        print(f"⚠️ Không tìm thấy '{wait_selector}', thử lấy content hiện tại...")

            if click_selectors:
                for selector in click_selectors:
                    try:
                        print(f"🖱️ Đang click: {selector}")
                        # Chờ selector xuất hiện và có thể click được
                        await page.wait_for_selector(selector, state="visible", timeout=5000)
                        await page.click(selector)
                        # Chờ một chút sau khi click để nội dung load (AJAX)
                        await asyncio.sleep(2)
                    except Exception as e:
                        print(f"⚠️ Không thể click {selector}: {e}")
            
            # Giả lập tương tác người dùng
            await self.simulate_human_interaction(page, duration=random.uniform(2.0, 4.0))
            
            # Chờ thêm để JS render xong hoàn toàn
            await asyncio.sleep(extra_wait)
            
            content = await page.content()
            return content
        except Exception as e:
            msg = str(e)
            if "Target page, context or browser has been closed" in msg:
                 print(f"❌ Browser/Page bị đóng bất ngờ khi load {url}. Bỏ qua.")
                 return ""
            print(f"⚠️ Lỗi khi load {url}: {e}")
            try:
                return await page.content()
            except:
                return ""
        finally:
            await page.close()

async def list_to_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]
