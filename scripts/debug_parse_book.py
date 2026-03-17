import os
import sys
import asyncio

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.stv_browser import STVBrowser
from bs4 import BeautifulSoup

async def debug_book():
    url = "https://sangtacviet.app/truyen/fanqie/1/7077757205902035998/"
    browser = await STVBrowser.get_instance()
    html = await browser.get_content(url, wait_selector=".listchapitem", click_selectors=["#clicktoexp"])
    with open("debug_book_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved HTML to debug_book_page.html")
    await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_book())
