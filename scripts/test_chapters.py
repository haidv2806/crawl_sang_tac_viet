# test_chapters.py - Test lấy thông tin sách và danh sách chương
# Chỉ log dữ liệu ra console, không gửi đi đâu cả.
#
# Cách chạy:
#   cd F:\crawlSTV\crawlCode
#   python test_chapters.py

import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.stv_book import parse_book_info
from scrapers.stv_chapters import get_chapters

# ---- CẤU HÌNH TEST ----
TEST_BOOK_URL = "https://sangtacviet.app/truyen/dich/1/47055/"
HEADLESS = True  # False để thấy cửa sổ browser (debug)
# -----------------------


async def main():
    print("=" * 60)
    print("🔍 TEST: Lấy thông tin sách")
    print(f"📖 URL: {TEST_BOOK_URL}")
    print("=" * 60)

    # 1. Lấy thông tin sách (không dùng browser)
    print("\n📚 Đang lấy thông tin sách...")
    book_info = await parse_book_info(TEST_BOOK_URL)

    if not book_info:
        print("❌ Không lấy được thông tin sách!")
        return

    print("\n✅ Thông tin sách:")
    print(f"  Tên       : {book_info['name']}")
    print(f"  Tác giả   : {book_info['authors']}")
    print(f"  Trạng thái: {book_info['status']}")
    print(f"  Thể loại  : {book_info['tags']}")
    print(f"  Ảnh bìa   : {book_info['cover_url']}")
    print(f"  Book ID   : {book_info['book_id']}")
    print(f"  Host      : {book_info['host']}")
    print(f"  Mô tả     : {book_info['description'][:200]}...")

    print("\n" + "=" * 60)
    print("🔍 TEST: Lấy danh sách chương (cần browser)")
    print("=" * 60)

    # 2. Lấy danh sách chương (cần Playwright + cookie)
    print(f"\n📋 Đang lấy danh sách chương (headless={HEADLESS})...")
    chapters = await get_chapters(
        book_url=TEST_BOOK_URL,
        book_id=book_info["book_id"],
        host=book_info["host"],
        headless=HEADLESS,
    )

    if not chapters:
        print("❌ Không lấy được danh sách chương!")
        return

    print(f"\n✅ Tổng số chương: {len(chapters)}")
    print("\n📄 Danh sách chương (10 đầu):")
    for ch in chapters[:10]:
        print(f"  Vol={ch['volume']:>4} | ID={ch['chapter_id']:>12} | {ch['title'][:60]}")
        print(f"             URL: {ch['url']}")

    if len(chapters) > 10:
        print(f"\n  ... (còn {len(chapters) - 10} chương nữa)")

    print("\n📄 Chương cuối cùng:")
    last = chapters[-1]
    print(f"  Vol={last['volume']:>4} | ID={last['chapter_id']:>12} | {last['title'][:60]}")
    print(f"             URL: {last['url']}")

    print("\n" + "=" * 60)
    print("✅ TEST HOÀN THÀNH")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
