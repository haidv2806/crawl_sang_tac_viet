# stv_chapter_content.py - Lay noi dung chuong tu sangtacviet.app (STVBrowser)
#
# Strategy:
#   1. Su dung STVBrowser de mo trang chuong
#   2. Cho JS render noi dung (AJAX)
#   3. Parse truc tiep tu DOM (HTML full page)
#   4. Ve sinh HTML (xoa span xam, xu ly the <i>)

import re
import os
import sys
from bs4 import BeautifulSoup

# Fix path to allow importing 'core' when running directly
if __name__ == "__main__" or "scrapers" in __file__:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.stv_browser import STVBrowser
from core.req_config import REQConfig

STV_BASE = "https://sangtacviet.app"
# AUTH_FILE removed, handled by stv_utils

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

async def get_chapter_content(
    book_id: str,
    host: str,
    chapter_c: str,
    headless: bool = False, # Giữ tham số để không break code gọi đến
) -> dict:
    """
    Lay noi dung chuong dung STVBrowser de render JS va parse truc tiep tu DOM.
    """
    chapter_url = f"{STV_BASE}/truyen/{host}/1/{book_id}/{chapter_c}/"
    
    print(f"  [chapter] Lay noi dung qua browser: {chapter_url}")
    
    try:
        browser = await STVBrowser.get_instance()
        # Bypass captcha truoc moi lan cao chuong
        await REQConfig.async_do_bypass()
        # Chờ selector của content box xuat hien
        html_content = await browser.get_content(chapter_url, wait_selector="#content-container .contentbox")
        
        if not html_content:
            return {"code": "failed", "err": "Browser returned empty content"}
            
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Extract book name and chapter name
        book_name_el = soup.select_one("#booknameholder")
        chapter_name_el = soup.select_one("#bookchapnameholder")
        
        book_name = book_name_el.get_text().strip() if book_name_el else ""
        chapter_name = chapter_name_el.get_text().strip() if chapter_name_el else ""
        
        # Nếu chapter_name rỗng, JS chưa render kịp -> giả lập thêm và lấy lại content
        if not chapter_name:
            print(f"  ⚠️ Tên chương rỗng, thử giả lập thêm và lấy lại content...")
            import asyncio as _asyncio
            import random as _random
            context = await browser.get_context()
            pages = context.pages
            if pages:
                retry_page = pages[-1]  # trang vừa load (đã đóng? dùng page mới)
            # Tạo page mới và load lại
            retry_page = await browser.get_page()
            try:
                await retry_page.goto(chapter_url, wait_until="domcontentloaded", timeout=60000)
                try:
                    await retry_page.wait_for_selector("#content-container .contentbox", state="attached", timeout=30000)
                except Exception:
                    pass
                await browser.simulate_human_interaction(retry_page, duration=_random.uniform(2.0, 4.0))
                await _asyncio.sleep(3)
                html_content = await retry_page.content()
                soup = BeautifulSoup(html_content, "html.parser")
                book_name_el = soup.select_one("#booknameholder")
                chapter_name_el = soup.select_one("#bookchapnameholder")
                book_name = book_name_el.get_text().strip() if book_name_el else book_name
                chapter_name = chapter_name_el.get_text().strip() if chapter_name_el else ""
                print(f"  🔄 Tên chương sau retry: '{chapter_name}'")
            finally:
                await retry_page.close()
        
        text = parse_chapter_content_from_soup(soup)
        
        if not text or len(text) < 100:
            # Check for error messages in page
            if "Vui lòng xác nhận" in html_content or "Cloudflare" in html_content:
                 return {"code": "failed", "err": "Bi chan hoac yeu cau xac minh (Cloudflare/Human)"}

        return {
            "code":        "0",
            "bookname":    book_name,
            "chaptername": chapter_name,
            "text":        text,
            "html":        html_content, # Giu lai de debug neu can
        }
        
    except Exception as e:
        print(f"  ⚠️ Loi khi lay noi dung qua browser: {e}")
        return {"code": "failed", "err": str(e)}


async def close_browser():
    """Ham stub de giu tuong thich code cu."""
    pass

if __name__ == "__main__":
    import asyncio
    
    async def _test():
        result = await get_chapter_content("11319", "trxs2", "3")
        print(f"\ncode: {result.get('code')}")
        if result.get("code") == "0":
            print(f"bookname: {result.get('bookname')}")
            print(f"text length: {len(result['text'])}")
            print(f"Preview: {result['text'][:200]}")
        else:
            print(f"error: {result.get('err')}")
    
    asyncio.run(_test())
