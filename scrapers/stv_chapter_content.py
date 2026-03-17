import re
import os
import sys
import json
import asyncio
from bs4 import BeautifulSoup

# Fix path to allow importing 'core' when running directly
if __name__ == "__main__" or "scrapers" in __file__:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.stv_browser import STVBrowser
from core.req_config import REQConfig
from core.config import TOKEN as BYPASS_TOKEN

STV_BASE = "https://sangtacviet.app"
AJAX_KEYWORD = "sajax=readchapter"

def parse_chapter_content_from_soup(soup: BeautifulSoup) -> str:
    """Parse selection from BeautifulSoup -> text thuan."""
    content_box = soup.select_one("#content-container .contentbox")
    if not content_box:
        # Fallback if selector fails
        content_box = soup.find("div", class_="contentbox")
    
    if not content_box:
        return ""

    # Clean up gray spans
    for span in content_box.find_all("span", style=lambda s: s and "color:gray" in s):
        span.decompose()
        
    # Clean up scripts/styles
    for tag in content_box.find_all(["script", "style"]):
        tag.decompose()
        
    # Handle vietnamese annotations in <i> tags
    for i_tag in content_box.find_all("i", attrs={"v": True}):
        viet = i_tag.get("v", "").strip().split("/")[0].strip()
        if viet:
            i_tag.replace_with(viet + " ")
            
    # Convert <br> to newlines
    for br in content_box.find_all("br"):
        br.replace_with("\n")
        
    text = content_box.get_text(separator=" ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return "\n\n".join(l.strip() for l in text.splitlines() if l.strip())

async def bypass_captcha_in_browser(page) -> dict:
    """
    Gọi endpoint bypass captcha từ BÊN TRONG trình duyệt bằng page.evaluate().
    Cookies của browser session được tự động đính kèm → đúng phiên làm việc.
    Trường hợp token sai/hết hạn, sẽ hỏi user nhập mới.
    """
    # Lấy token từ biến global của module (đã import từ core.config)
    global BYPASS_TOKEN
    
    print(f"  🔓 Đang thực hiện bypass captcha từ browser context (Token: {BYPASS_TOKEN})...")
    
    while True:
        result = await page.evaluate(f"""
            async () => {{
                try {{
                    const resp = await fetch(
                        '{STV_BASE}/index.php?ngmar=verifyca',
                        {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/x-www-form-urlencoded',
                                'X-Requested-With': 'XMLHttpRequest'
                            }},
                            body: 'ajax=verifycaptcha&token={BYPASS_TOKEN}&purpose=read&provider=sangtacviet',
                            credentials: 'include'
                        }}
                    );
                    const text = await resp.text();
                    return {{ status: resp.status, body: text }};
                }} catch (e) {{
                    return {{ status: -1, body: String(e) }};
                }}
            }}
        """)
        
        status = result.get('status')
        body = result.get('body', '')
        print(f"     → Bypass status: {status}, body: {body[:100]}")
        
        # Kiểm tra nếu bypass thành công (chữ "success" thường có trong body)
        if status == 200 and "success" in body.lower():
            print("  ✅ Bypass captcha thành công!")
            return result
        
        # Nếu thất bại, yêu cầu nhập token mới (để tránh block asyncio event loop, dùng run_in_executor)
        print(f"  ❌ Bypass captcha thất bại. Token hiện tại ({BYPASS_TOKEN}) có thể đã cũ.")
        
        loop = asyncio.get_event_loop()
        new_token = await loop.run_in_executor(
            None, 
            lambda: input("  → Nhập token bypass mới (nhấn Enter để bỏ qua bypass): ").strip()
        )
        
        if not new_token:
            print("  ⏭️ Bỏ qua bypass thủ công.")
            return result
            
        # Cập nhật global token và thử lại
        BYPASS_TOKEN = new_token
        print(f"  🔄 Thử lại bypass với token mới: {BYPASS_TOKEN} ...")

async def wait_for_ajax(captured: dict, timeout: float = 15.0) -> bool:
    """Chờ tối đa `timeout` giây cho đến khi AJAX được capture."""
    elapsed = 0.0
    while elapsed < timeout:
        if captured["response_text"] is not None:
            return True
        await asyncio.sleep(0.5)
        elapsed += 0.5
    return False

async def get_chapter_content(
    book_id: str,
    host: str,
    chapter_c: str,
    headless: bool = False, # Giữ tham số để không break code gọi đến
) -> dict:
    """
    Lay noi dung chuong dung STVBrowser.
    Su dung co che intercept AJAX va page.evaluate bypass captcha hieu qua nhat.
    """
    chapter_url = f"{STV_BASE}/truyen/{host}/1/{book_id}/{chapter_c}/"
    print(f"  [chapter] Lay noi dung: {chapter_url}")
    
    browser = await STVBrowser.get_instance()
    page = await browser.get_page()
    
    # Biến lưu kết quả từ network intercept
    captured = {"url": None, "response_text": None}

    async def handle_response(response):
        if AJAX_KEYWORD in response.url and response.request.method == "POST":
            captured["url"] = response.url
            try:
                captured["response_text"] = await response.text()
            except Exception as e:
                captured["response_text"] = f"[Lỗi đọc response: {e}]"
            print(f"  📡 Đã bắt AJAX: {response.url}")

    page.on("response", handle_response)
    
    try:
        try:
            await page.goto(chapter_url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"  ❌ Không thể mở trang: {e}")
            return {"code": "failed", "err": f"Không thể mở trang: {e}"}

        print("  🖱️ Giả lập tương tác người dùng...")
        await browser.simulate_human_interaction(page, duration=5.0)

        # Chờ AJAX lần đầu 
        print("  ⏳ Chờ AJAX lần 1 (tối đa 10 giây)...")
        got_data = await wait_for_ajax(captured, timeout=10.0)

        # Kiểm tra captcha
        if got_data:
            try:
                first_data = json.loads(captured["response_text"])
                code = int(first_data.get("code", 0))
            except Exception:
                code = 0

            if code in (7, 21):
                print(f"  ⚠️ Server trả code {code} (captcha/rate-limit). Đang bypass...")
                captured["url"] = None
                captured["response_text"] = None

                await bypass_captcha_in_browser(page)
                await asyncio.sleep(1)

                print("  🔄 Reload trang sau bypass captcha...")
                await page.reload(wait_until="domcontentloaded")
                await browser.simulate_human_interaction(page, duration=5.0)

                print("  ⏳ Chờ AJAX lần 2 sau bypass (tối đa 15 giây)...")
                await wait_for_ajax(captured, timeout=15.0)
        else:
            print("  ⚠️ Không nhận được AJAX lần đầu. Thử bypass captcha...")
            await bypass_captcha_in_browser(page)
            await asyncio.sleep(1)
            await page.reload(wait_until="domcontentloaded")
            await browser.simulate_human_interaction(page, duration=5.0)
            await wait_for_ajax(captured, timeout=15.0)

        # Cho JS render dom sau khi AJAX xong
        await asyncio.sleep(3)
        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Extract book name and chapter name
        book_name_el = soup.select_one("#booknameholder")
        chapter_name_el = soup.select_one("#bookchapnameholder")
        
        book_name = book_name_el.get_text().strip() if book_name_el else ""
        chapter_name = chapter_name_el.get_text().strip() if chapter_name_el else ""
        
        text = parse_chapter_content_from_soup(soup)
        
        if not text or len(text) < 100:
            if "Vui lòng xác nhận" in html_content or "Cloudflare" in html_content:
                 return {"code": "failed", "err": "Bị chặn hoặc yêu cầu xác minh (Cloudflare/Human)"}
                 
        return {
            "code":        "0",
            "bookname":    book_name,
            "chaptername": chapter_name,
            "text":        text,
            "html":        html_content, 
        }
        
    except Exception as e:
        print(f"  ⚠️ Lỗi khi lấy nội dung qua browser: {e}")
        return {"code": "failed", "err": str(e)}
    finally:
        try:
            await page.close()
        except Exception:
            pass


async def close_browser():
    """Ham stub de giu tuong thich code cu."""
    pass

if __name__ == "__main__":
    import asyncio
    
    async def _test():
        result = await get_chapter_content("47055", "dich", "4") # Test với URL fix
        print(f"\ncode: {result.get('code')}")
        if result.get("code") == "0":
            print(f"bookname: {result.get('bookname')}")
            print(f"chaptername: {result.get('chaptername')}")
            print(f"text length: {len(result['text'])}")
            print(f"Preview: {result['text'][:200]}")
        else:
            print(f"error: {result.get('err')}")
    
    asyncio.run(_test())
