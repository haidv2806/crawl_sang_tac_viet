# crawl_stv.py - Crawler sangtacviet.app
#
# Usage:
#   python crawl_stv.py --url https://sangtacviet.app/truyen/dich/1/47055/
#   python crawl_stv.py --type dich --minc 100 --pages 2
#   python crawl_stv.py --type dich --limit 5   (gioi han 5 chuong dau moi sach)

import argparse
import asyncio
import json
import os
import tempfile
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from core.config import BASE_URL, CHAPTERS_PER_VOLUME, HEADERS, STV_BASE
from scrapers.stv_book import download_cover, parse_book_info
from core.stv_categories import map_tags
from scrapers.stv_chapters import get_chapters
from scrapers.stv_chapter_content import get_chapter_content

# ------------------------------------------------------------------ #
# Search API                                                           #
# ------------------------------------------------------------------ #

SEARCH_URL = f"{STV_BASE}/io/searchtp/searchBooks"
from core.req_config import req_get

def fetch_book_list(
    type_: str = "dich",
    tag: str = "",
    minc: int = 0,
    page: int = 1,
) -> list[str]:
    """
    Goi API searchBooks, tra ve danh sach URL sach.
    API tra ve HTML, parse bang BeautifulSoup.
    """
    params = {
        "find":  "",
        "minc":  str(minc),
        "type":  type_,
        "tag":   tag,
        "sort":  "view",
        "p":     str(page),
    }
    try:
        resp = req_get(SEARCH_URL, params=params, referer=STV_BASE, timeout=30)
        soup = BeautifulSoup(resp.text, "html.parser")
        urls = []
        for a in soup.find_all("a", class_=lambda c: c and "booksearch" in c):
            href = a.get("href", "")
            if not href or "/truyen/" not in href:
                continue
            full = href if href.startswith("http") else STV_BASE + href
            urls.append(full)
        return urls
    except Exception as e:
        print(f"[search] Loi fetch trang {page}: {e}")
        return []


# ------------------------------------------------------------------ #
# Backend API calls                                                    #
# ------------------------------------------------------------------ #

def api_create_book(info: dict, cover_path: str) -> int | None:
    url = f"{BASE_URL}/Book/create"
    categories = map_tags(info.get("tags", []))
    # Dùng indexed notation categories[] để backend nhận diện là mảng
    data = [
        ("book_name",   info["name"]),
        ("sub_names",   json.dumps(info.get("sub_names", []), ensure_ascii=False)),
        ("authors",     json.dumps(info["authors"], ensure_ascii=False)),
        ("status",      info["status"]),
        ("description", info["description"]),
    ]
    for cat_id in categories:
        data.append(("categories[]", str(cat_id)))
    try:
        with open(cover_path, "rb") as img_f:
            ext = Path(cover_path).suffix or ".jpg"
            files = {"image": (f"cover{ext}", img_f, "image/jpeg")}
            resp = requests.post(url, data=data, files=files, headers=HEADERS, timeout=60)
        print(f"  [book] create: {resp.status_code} | {resp.text[:200]}")
        if resp.status_code not in (200, 201):
            return None
        return resp.json().get("data", {}).get("book_id")
    except Exception as e:
        print(f"  [book] Loi: {e}")
        return None


def api_create_volume(book_id: int, volume_name: str) -> int | None:
    url = f"{BASE_URL}/Book/Volume/create"
    try:
        resp = requests.post(
            url,
            json={"book_id": book_id, "volume_name": volume_name, "status": "completed"},
            headers=HEADERS, timeout=30,
        )
        print(f"  [vol] {volume_name}: {resp.status_code}")
        return resp.json().get("data", {}).get("volume_id")
    except Exception as e:
        print(f"  [vol] Loi: {e}")
        return None


def api_create_chapter(volume_id: int, chapter_name: str, content: str) -> bool:
    url = f"{BASE_URL}/Book/Volume/Chapter/create"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", encoding="utf-8", delete=False
    ) as f:
        f.write(content)
        tmp = f.name
    try:
        data = {
            "volume_id":    str(volume_id),
            "chapter_name": chapter_name,
            "status":       "completed",
        }
        with open(tmp, "rb") as md_f:
            files = {"markdownFile": ("chapter.md", md_f, "text/markdown")}
            resp = requests.post(url, data=data, files=files, headers=HEADERS, timeout=120)
        return resp.status_code in (200, 201)
    except Exception as e:
        print(f"  [chap] Loi API: {e}")
        return False
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def default_cover_path() -> str:
    """Tra ve duong dan den defaultImage.png (cung thu muc hoac thu muc cha)."""
    for base in [Path(__file__).parent, Path(__file__).parent.parent]:
        p = base / "defaultImage.png"
        if p.exists():
            return str(p)
    # Neu khong tim thay, tra ve duong dan tuong doi
    return str(Path(__file__).parent / "defaultImage.png")


# ------------------------------------------------------------------ #
# Core crawl logic                                                     #
# ------------------------------------------------------------------ #

async def crawl_book(book_url: str, chapter_limit: int | None = None):
    """
    Crawl 1 cuon sach: lay info -> tao sach -> tao volume -> tao chuong.
    """
    print(f"\n{'='*60}")
    print(f"[book] {book_url}")

    # 1. Lay thong tin sach
    info = await parse_book_info(book_url)
    if not info:
        print("  [book] Khong lay duoc thong tin, bo qua.")
        return

    book_id_stv = info.get("book_id", "")
    host        = info.get("host", "")
    print(f"  [book] {info['name']} | host={host} | book_id={book_id_stv}")

    # 2. Lay danh sach chuong
    if not book_id_stv or not host:
        print("  [book] Khong co book_id/host, bo qua.")
        return

    chapters = await get_chapters(book_url, book_id_stv, host)
    if not chapters:
        print("  [book] Khong co chuong nao, bo qua.")
        return

    if chapter_limit:
        chapters = chapters[:chapter_limit]
    print(f"  [book] {len(chapters)} chuong se crawl")

    # 3. Tai anh bia
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        cover_path = f.name
    ok = await download_cover(info["cover_url"], cover_path)
    if not ok:
        if os.path.exists(cover_path):
            os.remove(cover_path)
        cover_path = default_cover_path()

    # 4. Tao sach tren backend
    backend_book_id = api_create_book(info, cover_path)
    if cover_path != default_cover_path() and os.path.exists(cover_path):
        os.remove(cover_path)
    if not backend_book_id:
        print("  [book] Khong tao duoc sach, bo qua.")
        return
    print(f"  [book] Da tao sach backend_book_id={backend_book_id}")

    # 5. Chia volume va tao chuong
    total = len(chapters)
    for vol_start in range(0, total, CHAPTERS_PER_VOLUME):
        chunk = chapters[vol_start : vol_start + CHAPTERS_PER_VOLUME]
        vol_end  = vol_start + len(chunk)
        vol_name = f"Chuong {vol_start + 1} - {vol_end}"

        volume_id = api_create_volume(backend_book_id, vol_name)
        if not volume_id:
            print(f"  [vol] Khong tao duoc volume {vol_name}, bo qua.")
            continue

        for idx, ch in enumerate(chunk, start=vol_start + 1):
            chap_id = ch["chapter_id"]
            title   = ch["title"] or f"Chuong {idx}"

            result = await get_chapter_content(
                book_id=book_id_stv,
                host=host,
                chapter_c=chap_id,
                headless=False,
            )

            if result.get("code") != "0":
                print(f"  [{idx}/{total}] Loi lay chuong {chap_id}: {result.get('err')}")
                continue

            chap_name_raw = result.get("chaptername") or title
            chap_name = f"{chap_name_raw} #{idx}"
            content   = result.get("text", "")
            if not content:
                print(f"  [{idx}/{total}] Noi dung trong, bo qua.")
                continue

            success = api_create_chapter(volume_id, chap_name, content)
            status  = "OK" if success else "FAIL"
            print(f"  [{idx}/{total}] {status}: {chap_name[:60]}")


# ------------------------------------------------------------------ #
# Main                                                                 #
# ------------------------------------------------------------------ #

async def main():
    parser = argparse.ArgumentParser(description="Crawler sangtacviet.app")
    parser.add_argument("--url",   type=str, help="URL 1 cuon sach cu the")
    parser.add_argument("--type",  type=str, default="", help="Loai truyen (dich, trxs2, ...)")
    parser.add_argument("--tag",   type=str, default="",     help="Tag loc")
    parser.add_argument("--minc",  type=int, default=100,    help="So chuong toi thieu")
    parser.add_argument("--pages", type=int, default=1,      help="So trang search can crawl")
    parser.add_argument("--limit", type=int, default=None,   help="Gioi han so chuong moi sach")
    args = parser.parse_args()

    try:
        if args.url:
            # Crawl 1 sach cu the
            await crawl_book(args.url, args.limit)
        else:
            # Crawl theo search API
            seen = set()
            for page in range(1, args.pages + 1):
                print(f"\n[search] Trang {page}/{args.pages}...")
                urls = fetch_book_list(
                    type_=args.type,
                    tag=args.tag,
                    minc=args.minc,
                    page=page,
                )
                print(f"[search] Tim thay {len(urls)} sach trang {page}")
                for url in urls:
                    if url in seen:
                        continue
                    seen.add(url)
                    await crawl_book(url, args.limit)
    finally:
        pass


if __name__ == "__main__":
    asyncio.run(main())
