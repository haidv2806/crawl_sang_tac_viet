# stv_book.py - Parse thông tin sách từ API sangtacviet.app (aiohttp version)
# Lưu ý: danh sách chương KHÔNG được lấy ở đây.
# Dùng stv_chapters.py để lấy danh sách chương.

import re
import aiohttp
import requests
from bs4 import BeautifulSoup
from core.config import STV_BASE
from core.req_config import req_get, async_req_get

async def parse_book_info(book_url: str, session: aiohttp.ClientSession = None) -> dict | None:
    """
    Lấy và parse thông tin sách từ URL trang sách.
    Trả về dict gồm: name, authors, description, cover_url, status, tags, book_id, host.
    Không bao gồm danh sách chương (xem stv_chapters.py).
    """
    async def _fetch(s: aiohttp.ClientSession) -> dict | None:
        try:
            async with await async_req_get(s, book_url) as resp:
                resp.raise_for_status()
                html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            return _parse_soup(soup, book_url)
        except Exception as e:
            print(f"❌ Lỗi parse trang sách {book_url}: {e}")
            return None

    if session is not None:
        return await _fetch(session)

    async with aiohttp.ClientSession() as s:
        return await _fetch(s)


def _extract_book_id_and_host(book_url: str) -> tuple[str, str]:
    """
    Trích xuất book_id và host từ URL dạng:
    https://sangtacviet.app/truyen/{host}/{vol}/{book_id}/
    """
    m = re.search(r"/truyen/([^/]+)/\d+/(\d+)/?", book_url)
    if m:
        return m.group(2), m.group(1)
    return "", ""


def _parse_soup(soup: BeautifulSoup, book_url: str) -> dict:
    # Tên sách
    name_el = soup.find("h1", id="book_name2")
    name = name_el.get_text(strip=True) if name_el else ""

    # Tác giả
    author = ""
    author_el = soup.find("h2", style=lambda s: s and "16px" in s)
    if author_el:
        author = author_el.get_text(strip=True)

    # Nếu không tìm thấy h2 styles, thử lấy từ meta
    if not author:
        meta_author = soup.find("meta", {"property": "og:novel:author"})
        if meta_author:
            author = meta_author.get("content", "").strip()

    # Ảnh bìa
    cover_url = ""
    cover_el = soup.find("img", id="thumb-prop")
    if cover_el:
        cover_url = cover_el.get("src", "")
    # Fallback: lấy từ meta og:image
    if not cover_url:
        meta_img = soup.find("meta", {"property": "og:image"})
        if meta_img:
            cover_url = meta_img.get("content", "")

    # Mô tả
    desc = ""
    desc_el = soup.find("div", id="book-sumary")
    if desc_el:
        desc = desc_el.get_text("\n", strip=True)[:700]

    # Trạng thái: lấy từ blk-body hoặc meta
    status_raw = ""
    status_el = soup.find("span", id="bookstatus")
    if status_el:
        status_raw = status_el.get_text(strip=True)
    # Fallback: lấy từ meta
    if not status_raw:
        meta_status = soup.find("meta", {"property": "og:novel:status"})
        if meta_status:
            status_raw = meta_status.get("content", "").strip()
    status = _map_status(status_raw)

    # Thể loại & Tên phụ (Tên gốc, Hán việt): tìm trong blk-body
    tags = []
    sub_names = []
    
    # Tên gốc đặc biệt có id oriname
    ori_name_el = soup.find("span", id="oriname")
    if ori_name_el:
        sub_names.append(ori_name_el.get_text(strip=True))

    for div in soup.find_all("div", class_="blk-body"):
        text = div.get_text()
        if "Thể loại" in text:
            raw = re.sub(r"Thể loại\s*:?\s*", "", text, flags=re.IGNORECASE).strip()
            parts = [t.strip() for t in raw.split(",") if t.strip()]
            tags.extend(parts)
        elif "Hán việt" in text:
            raw = re.sub(r"Hán việt\s*:?\s*", "", text, flags=re.IGNORECASE).strip()
            if raw and raw not in sub_names:
                sub_names.append(raw)
        elif "Tên gốc" in text and not sub_names: # Fallback neu oriname khong co record
            raw = re.sub(r"Tên gốc\s*:?\s*", "", text, flags=re.IGNORECASE).strip()
            if raw:
                sub_names.append(raw)

    # Lấy book_id và host từ URL (cần cho stv_chapters.py)
    book_id, host = _extract_book_id_and_host(book_url)

    return {
        "name": name,
        "sub_names": sub_names,
        "authors": [author] if author else ["Không rõ"],
        "description": desc or "Không có mô tả.",
        "cover_url": cover_url,
        "status": status,
        "tags": tags,
        "book_id": book_id,   # dùng cho API lấy chapter
        "host": host,         # dùng cho API lấy chapter
    }


def _map_status(raw: str) -> str:
    raw_lower = raw.lower()
    if "hoàn" in raw_lower or "hoan" in raw_lower:
        return "completed"
    return "ongoing"


async def download_cover(cover_url: str, dest_path: str) -> bool:
    """Tải ảnh bìa về file."""
    try:
        resp = req_get(cover_url, timeout=30)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        return True
    except Exception as e:
        print(f"  ❌ Lỗi tải ảnh bìa {cover_url}: {e}")
        return False
