# stv_search.py - Lấy danh sách URL truyện từ API tìm kiếm sangtacviet.app

from bs4 import BeautifulSoup
from config import STV_BASE
import aiohttp
import asyncio

# Endpoint API gốc trả về HTML fragment danh sách truyện
STV_SEARCH_API = "https://sangtacviet.app/io/searchtp/searchBooks"

# Tham số mặc định khi tìm kiếm
DEFAULT_PARAMS = {
    "find": "",
    "minc": 100,
    "type": "dich",
    "tag": "",
}

from core.config import STV_BASE
from core.req_config import async_req_get

async def _fetch_page_html(session: aiohttp.ClientSession, page: int) -> str:
    """Gọi API và trả về nội dung HTML của trang chỉ định."""
    params = {**DEFAULT_PARAMS, "p": page}
    async with await async_req_get(session, STV_SEARCH_API, params=params, referer=STV_BASE) as resp:
        resp.raise_for_status()
        return await resp.text()


def _parse_book_list(html: str) -> list[str]:
    """Phân tích HTML fragment trả về từ API, lấy URL các truyện."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", class_=lambda c: c and "booksearch" in c):
        href = a.get("href", "")
        if not href:
            continue
        full_url = STV_BASE + href if href.startswith("/") else href
        if "/truyen/" in full_url:
            links.append(full_url)
    return links


async def get_book_urls_from_page(page: int, session: aiohttp.ClientSession = None) -> list[str]:
    """
    Lấy danh sách URL trang sách từ một trang tìm kiếm qua API trực tiếp.
    Nếu không truyền session thì tự tạo session mới.
    """
    if session is not None:
        try:
            html = await _fetch_page_html(session, page)
            return _parse_book_list(html)
        except Exception as e:
            print(f"❌ Lỗi lấy trang tìm kiếm {page}: {e}")
            return []

    async with aiohttp.ClientSession() as s:
        try:
            html = await _fetch_page_html(s, page)
            return _parse_book_list(html)
        except Exception as e:
            print(f"❌ Lỗi lấy trang tìm kiếm {page}: {e}")
            return []


async def get_total_pages(session: aiohttp.ClientSession = None) -> int:
    """
    Xác định tổng số trang bằng cách tìm trang cuối còn có dữ liệu
    thông qua binary search đơn giản (tăng dần đến khi trang rỗng).
    """
    async def _has_results(s: aiohttp.ClientSession, page: int) -> bool:
        try:
            html = await _fetch_page_html(s, page)
            return len(_parse_book_list(html)) > 0
        except Exception:
            return False

    async def _find_max(s: aiohttp.ClientSession) -> int:
        # Bước 1: tìm giới hạn trên bằng cách nhân đôi
        lo, hi = 1, 1
        while await _has_results(s, hi):
            lo = hi
            hi *= 2

        # Bước 2: binary search giữa lo và hi
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            if await _has_results(s, mid):
                lo = mid
            else:
                hi = mid
        return lo

    if session is not None:
        return await _find_max(session)

    async with aiohttp.ClientSession() as s:
        return await _find_max(s)


async def generate_all_book_urls(max_pages: int | None = None):
    """
    Generator bất đồng bộ, lần lượt yield URL của từng truyện trên tất cả các trang.
    """
    async with aiohttp.ClientSession() as session:
        if max_pages is None:
            total = await get_total_pages(session)
            print(f"📋 Tìm thấy {total} trang tìm kiếm")
        else:
            total = max_pages

        seen = set()
        for page in range(1, total + 1):
            print(f"📄 Đang lấy danh sách trang {page}/{total}...")
            urls = await get_book_urls_from_page(page, session)
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    yield url
