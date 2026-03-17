import asyncio
import os
import sys

# Thêm thư mục hiện tại vào path để import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.stv_browser import STVBrowser

async def test_cookies():
    print("🔍 Bắt đầu kiểm tra cookies...")
    browser = await STVBrowser.get_instance()
    context = await browser.get_context()
    
    cookies = await context.cookies()
    print(f"📊 Tìm thấy {len(cookies)} cookies trong trình duyệt:")
    
    found_stv_cookies = False
    for cookie in cookies:
        if cookie['domain'] == 'sangtacviet.app':
            print(f"✅ Cookie: {cookie['name']} = {cookie['value'][:10]}... (Domain: {cookie['domain']})")
            found_stv_cookies = True
            
    if found_stv_cookies:
        print("🚀 Thành công: Đã tìm thấy cookies của sangtacviet.app!")
    else:
        print("❌ Thất bại: Không tìm thấy cookies của sangtacviet.app.")
        
    await browser.close()

if __name__ == "__main__":
    asyncio.run(test_cookies())
