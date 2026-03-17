import asyncio
import os
import sys

# Thêm thư mục hiện tại vào path để import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.stv_browser import STVBrowser

async def test_interaction():
    print("🔍 Bắt đầu kiểm tra giả lập tương tác...")
    browser = await STVBrowser.get_instance()
    
    url = "https://sangtacviet.app/truyen/trxs2/1/11319/3/"
    print(f"🌍 Gọi get_content cho {url}...")
    
    # get_content sẽ tự động gọi simulate_human_interaction
    content = await browser.get_content(url, extra_wait=1.0)
    
    if len(content) > 0:
        print(f"✅ Thành công: Lấy được nội dung trang ({len(content)} bytes)")
    else:
        print("❌ Thất bại: Không lấy được nội dung trang.")
        
    await browser.close()

if __name__ == "__main__":
    asyncio.run(test_interaction())
