import os
import sys
import asyncio
import json

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.stv_chapters import get_chapters

async def test_chapters():
    url = "https://sangtacviet.app/truyen/shu05/1/91929/"
    
    parts = url.strip("/").split("/")
    if len(parts) >= 6:
        host = parts[4]
        book_id = parts[6] if len(parts) > 6 else parts[5]
    else:
        print("Invalid URL format")
        return

    print(f"🌍 Fetching chapters for {url} (host: {host}, book_id: {book_id})")
    
    chapters = await get_chapters(
        book_url=url,
        book_id=book_id,
        host=host
    )
    
    if chapters:
        print(json.dumps(chapters, indent=2, ensure_ascii=False))
        print(f"\nTotal chapters found: {len(chapters)}")
    else:
        print("No chapters found or error occurred.")

if __name__ == "__main__":
    asyncio.run(test_chapters())
