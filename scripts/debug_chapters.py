import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.stv_browser import STVBrowser
from bs4 import BeautifulSoup
from core.config import STV_BASE

async def test_chapters():
    url = "https://sangtacviet.app/truyen/fanqie/1/7077757205902035998/"
    browser = await STVBrowser.get_instance()
    
    print(f"🌍 Loading {url}")
    html = await browser.get_content(
        url, 
        wait_selector=".listchapitem", 
        click_selectors=["#clicktoexp"],
        extra_wait=5.0
    )
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Check directly for listchapitem
    items = soup.find_all("a", class_="listchapitem")
    print(f"Total listchapitem found: {len(items)}")
    
    container = soup.find("div", id="chaptercontainerinner")
    print(f"chaptercontainerinner found: {container is not None}")
    if container:
        items_in = container.find_all("a", class_="listchapitem")
        print(f"Items inside container: {len(items_in)}")
        
    await browser.close()

if __name__ == "__main__":
    asyncio.run(test_chapters())
