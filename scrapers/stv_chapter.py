# stv_chapter.py - Parse nội dung chương (Playwright Version)

import asyncio
from bs4 import BeautifulSoup
from core.stv_browser import STVBrowser

async def extract_chapter_content(chapter_url: str, browser: STVBrowser = None) -> list[str] | None:
    """
    Sử dụng Browser để render JavaScript và giải mã nội dung thẻ <i>.
    """
    if browser is None:
        browser = await STVBrowser.get_instance()
        
    try:
        # Chờ contentbox chứa các thẻ i xuất hiện
        # Selector .contentbox i đảm bảo JS đã render ra các thẻ i dịch
        html = await browser.get_content(chapter_url, wait_selector="div.contentbox i")
        soup = BeautifulSoup(html, "html.parser")
        return parse_chapter_content_from_soup(soup)
    except Exception as e:
        print(f"  ❌ Lỗi lấy nội dung chương {chapter_url}: {e}")
        return None

def parse_chapter_content_from_soup(soup: BeautifulSoup) -> list[str] | None:
    # Tìm div.contentbox có chứa id cld-... (đã render)
    contentbox = soup.find("div", class_="contentbox", id=lambda x: x and x.startswith("cld-"))
    if not contentbox:
        contentbox = soup.find("div", class_="contentbox")

    if not contentbox:
        return None

    paragraphs = []
    current_parts = []

    def flush():
        text = "".join(current_parts).strip()
        if text:
            paragraphs.append(text)
        current_parts.clear()

    # Duyệt qua các node để giữ cấu trúc xuống dòng <br>
    for node in contentbox.children:
        if node.name == "br":
            flush()
        elif node.name == "i":
            # Lấy text đã được browser render (tiếng Việt)
            current_parts.append(node.get_text())
        elif node.name is None: # Text node
            text = str(node)
            if "@" in text or "đang đọc bản" in text:
                continue
            current_parts.append(text)
        elif node.name == "span":
            # Bỏ qua text rác hệ thống
            continue

    flush()
    result = [p for p in paragraphs if p.strip()]
    return result if result else None

def content_to_markdown(paragraphs: list[str]) -> str:
    return "\n\n".join(paragraphs)

async def extract_chapter_name_from_page(chapter_url: str, browser: STVBrowser = None) -> str:
    """Lấy tên chương thực tế từ page (vì URL có thể không chứa tên)."""
    if browser is None:
        browser = await STVBrowser.get_instance()
    try:
        html = await browser.get_content(chapter_url, wait_selector="#bookchapnameholder")
        soup = BeautifulSoup(html, "html.parser")
        el = soup.find("center", id="bookchapnameholder")
        if el:
            return el.get_text(strip=True)
        return "Chương không tên"
    except:
        return "Chương không tên"
