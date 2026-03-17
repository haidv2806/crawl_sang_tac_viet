# test_create_book.py - Test tạo sách qua API
# Flow: lấy book info → tải ảnh bìa → gọi API POST /Book/create → log kết quả
#
# Cách chạy:
#   cd F:\crawlSTV\crawlCode
#   python test_create_book.py

import asyncio
import json
import os
import sys
import tempfile
import requests

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import BASE_URL, HEADERS
from scrapers.stv_book import parse_book_info, download_cover
from core.stv_categories import map_tags

# ---- CẤU HÌNH TEST ----
TEST_BOOK_URL = "https://sangtacviet.app/truyen/fanqie/1/7520527127867821081/"
# -----------------------


def api_create_book(info: dict, cover_path: str) -> dict | None:
    """
    Gọi POST /Book/create với multipart/form-data.
    Trả về toàn bộ response JSON để log, hoặc None nếu lỗi.

    Fields theo controller:
      - book_name  : string (required)
      - authors    : JSON string array (required)
      - status     : "show"|"hidden"|"ongoing"|"completed" (required)
      - description: string (required)
      - categories : array of integers (gửi nhiều tuple cùng key)
      - image      : file (required)
      [optional: sub_names, artists]
    """
    url = f"{BASE_URL}/Book/create"
    categories = map_tags(info.get("tags", []))

    # Multipart data — gửi nhiều tuple cùng key cho categories
    data = [
        ("book_name",   info["name"]),
        ("sub_names",   json.dumps(info.get("sub_names", []), ensure_ascii=False)),
        ("authors",     json.dumps(info["authors"], ensure_ascii=False)),
        ("status",      info["status"]),
        ("description", info["description"][:1000]),
    ]
    for cat_id in categories:
        data.append(("categories", str(cat_id)))

    print(f"\n📤 Gửi API tạo sách:")
    print(f"   URL       : {url}")
    print(f"   book_name : {info['name']}")
    print(f"   authors   : {info['authors']}")
    print(f"   status    : {info['status']}")
    print(f"   sub_names : {info.get('sub_names', [])}")
    print(f"   categories: {categories}")
    print(f"   cover     : {cover_path}")
    print(f"   desc (100): {info['description'][:100]}...")

    try:
        from pathlib import Path
        ext = Path(cover_path).suffix or ".jpg"
        with open(cover_path, "rb") as img_f:
            files = {"image": (f"cover{ext}", img_f, "image/jpeg")}
            resp = requests.post(url, data=data, files=files, headers=HEADERS, timeout=60)

        print(f"\n📊 HTTP Status : {resp.status_code}")
        print(f"📊 Response raw: {resp.text[:800]}")

        try:
            return resp.json()
        except Exception:
            print("⚠️ Không parse được JSON từ response")
            return None

    except Exception as e:
        print(f"❌ Exception khi gọi API: {e}")
        return None


async def main():
    print("=" * 60)
    print("🔍 TEST: Tạo sách qua API")
    print(f"📖 URL sách STV : {TEST_BOOK_URL}")
    print(f"🌐 API endpoint : {BASE_URL}/Book/create")
    print("=" * 60)

    # 1. Lấy thông tin sách
    print("\n📚 Bước 1: Lấy thông tin sách...")
    book_info = await parse_book_info(TEST_BOOK_URL)
    if not book_info:
        print("❌ Không lấy được thông tin sách!")
        return

    print(f"  ✅ Tên      : {book_info['name']}")
    print(f"  ✅ Authors  : {book_info['authors']}")
    print(f"  ✅ Status   : {book_info['status']}")
    print(f"  ✅ Tags     : {book_info['tags']}")
    print(f"  ✅ Sub-names: {book_info['sub_names']}")
    print(f"  ✅ Cover URL: {book_info['cover_url']}")

    # 2. Map tags → categories
    categories = map_tags(book_info.get("tags", []))
    print(f"\n🏷️  Bước 2: Map tags → categories: {categories}")

    # 3. Tải ảnh bìa về file tạm
    print(f"\n🖼️  Bước 3: Tải ảnh bìa...")
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        cover_path = f.name

    # Đường dẫn tới ảnh mặc định (cùng thư mục với script hoặc thư mục cha)
    DEFAULT_IMAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "defaultImage.png")
    if not os.path.exists(DEFAULT_IMAGE):
        DEFAULT_IMAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "defaultImage.png")

    cover_ok = await download_cover(book_info["cover_url"], cover_path)
    if not cover_ok:
        print("⚠️ Không tải được ảnh bìa, dùng defaultImage.png...")
        if not os.path.exists(DEFAULT_IMAGE):
            print(f"  ❌ Không tìm thấy defaultImage.png! Hủy test.")
            os.remove(cover_path)
            return
        import shutil
        shutil.copy(DEFAULT_IMAGE, cover_path)
        print(f"  ✅ Dùng ảnh mặc định: {DEFAULT_IMAGE}")
    else:
        size = os.path.getsize(cover_path)
        print(f"  ✅ Đã tải ảnh bìa: {cover_path} ({size:,} bytes)")

    # 4. Gọi API tạo sách
    print(f"\n🚀 Bước 4: Gọi API tạo sách...")
    result = api_create_book(book_info, cover_path)

    # 5. Dọn file tạm
    if os.path.exists(cover_path):
        os.remove(cover_path)

    # 6. Log kết quả
    print("\n" + "=" * 60)
    if result:
        print("📋 Kết quả API (full JSON):")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        if result.get("result") is True:
            book_id = result.get("data", {}).get("book_id")
            print(f"\n✅ TẠO SÁCH THÀNH CÔNG! book_id = {book_id}")
        else:
            print(f"\n❌ API trả lỗi: {result.get('message', 'Không rõ')}")
    else:
        print("❌ Không nhận được response từ API")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
