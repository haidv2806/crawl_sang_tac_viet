import os
import sys
import asyncio

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.stv_chapter_content import get_chapter_content

# ---- CAU HINH TEST ----
BOOK_ID   = "11319"
HOST      = "trxs2"
CHAPTER_C = "4"
# -----------------------

async def main():
    print("=" * 60)
    print("TEST: Lay noi dung chuong dung stv_chapter_content (Refactored - Direct API)")
    print(f"Book ID: {BOOK_ID}, Host: {HOST}, Chapter: {CHAPTER_C}")
    print("=" * 60)

    try:
        result = await get_chapter_content(
            book_id=BOOK_ID,
            host=HOST,
            chapter_c=CHAPTER_C,
        )

        code = result.get("code")
        print(f"\nResult code = {code}")

        if code == "0":
            print("\nSUCCESS! Nhan duoc noi dung chuong!")
            print(f"  bookname   : {result.get('bookname', '')}")
            print(f"  chaptername: {result.get('chaptername', '')}")
            content = result.get("text", "")
            print(f"  data       : {len(content)} chars")
            print(f"\nPreview noi dung (500 dau):")
            print(content[:500])
        else:
            print(f"\nLoi result: {result}")

    except Exception as e:
        print(f"\nException: {e}")

    print("\n" + "=" * 60)
    print("TEST HOAN THANH")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

