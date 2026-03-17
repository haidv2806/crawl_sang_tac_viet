import asyncio
import json

from core.stv_browser import STVBrowser

# URL trang chương cần đọc
CHAPTER_URL = "https://sangtacviet.app/truyen/dich/1/47055/4/"
# Từ khóa nhận diện AJAX request nội dung chương
AJAX_KEYWORD = "sajax=readchapter"
# Token bypass captcha (giống req_config.py)
BYPASS_TOKEN = "GHLQ"


async def bypass_captcha_in_browser(page) -> dict:
    """
    Gọi endpoint bypass captcha từ BÊN TRONG trình duyệt bằng page.evaluate().
    Cookies của browser session được tự động đính kèm → đúng phiên làm việc.
    """
    print("🔓 Đang thực hiện bypass captcha từ browser context...")
    result = await page.evaluate(f"""
        async () => {{
            try {{
                const resp = await fetch(
                    'https://sangtacviet.app/index.php?ngmar=verifyca',
                    {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-Requested-With': 'XMLHttpRequest'
                        }},
                        body: 'ajax=verifycaptcha&token={BYPASS_TOKEN}&purpose=read&provider=sangtacviet',
                        credentials: 'include'
                    }}
                );
                const text = await resp.text();
                return {{ status: resp.status, body: text }};
            }} catch (e) {{
                return {{ status: -1, body: String(e) }};
            }}
        }}
    """)
    print(f"   → Bypass status: {result.get('status')}, body: {result.get('body', '')[:100]}")
    return result


async def wait_for_ajax(captured: dict, timeout: float = 15.0) -> bool:
    """Chờ tối đa `timeout` giây cho đến khi AJAX được capture."""
    elapsed = 0.0
    while elapsed < timeout:
        if captured["response_text"] is not None:
            return True
        await asyncio.sleep(0.5)
        elapsed += 0.5
    return False


async def test_cookie_ajax():
    browser = await STVBrowser.get_instance()

    print(f"🌐 Đang mở trang: {CHAPTER_URL}")
    page = await browser.get_page()

    # --- Biến lưu kết quả từ network intercept ---
    captured = {"url": None, "response_text": None}

    async def handle_response(response):
        if AJAX_KEYWORD in response.url and response.request.method == "POST":
            captured["url"] = response.url
            try:
                captured["response_text"] = await response.text()
            except Exception as e:
                captured["response_text"] = f"[Lỗi đọc response: {e}]"
            print(f"📡 Đã bắt AJAX: {response.url}")
            print(f"   Status: {response.status}")

    # Đăng ký lắng nghe TRƯỚC khi goto
    page.on("response", handle_response)

    await page.goto(CHAPTER_URL, wait_until="domcontentloaded")

    # Giả lập tương tác người dùng
    print("🖱️ Giả lập tương tác người dùng...")
    await browser.simulate_human_interaction(page, duration=5.0)

    # Chờ AJAX lần đầu (trang có thể tự gọi)
    print("⏳ Chờ AJAX lần 1 (tối đa 10 giây)...")
    got_data = await wait_for_ajax(captured, timeout=10.0)

    # Nếu code 7 / 21 → cần bypass captcha rồi thử lại
    if got_data:
        try:
            first_data = json.loads(captured["response_text"])
            code = int(first_data.get("code", 0))
        except Exception:
            code = 0

        if code in (7, 21):
            print(f"⚠️  Server trả code {code} (captcha/rate-limit). Đang bypass...")
            captured["url"] = None
            captured["response_text"] = None

            await bypass_captcha_in_browser(page)
            await asyncio.sleep(1)

            # Reload trang để trigger lại AJAX sau khi bypass
            print("🔄 Reload trang sau bypass captcha...")
            await page.reload(wait_until="domcontentloaded")
            await browser.simulate_human_interaction(page, duration=5.0)

            print("⏳ Chờ AJAX lần 2 sau bypass (tối đa 15 giây)...")
            got_data = await wait_for_ajax(captured, timeout=15.0)
    else:
        # Không nhận được AJAX lần đầu → thử bypass luôn
        print("⚠️  Không nhận được AJAX lần đầu. Thử bypass captcha...")
        await bypass_captcha_in_browser(page)
        await asyncio.sleep(1)
        await page.reload(wait_until="domcontentloaded")
        await browser.simulate_human_interaction(page, duration=5.0)
        print("⏳ Chờ AJAX lần 2 sau bypass (tối đa 15 giây)...")
        got_data = await wait_for_ajax(captured, timeout=15.0)

    # --- In kết quả cuối cùng ---
    print("\n========== KẾT QUẢ ==========")
    if captured["response_text"] is not None:
        print(f"🔗 URL: {captured['url']}")
        print("\n--- DỮ LIỆU ---")
        try:
            data = json.loads(captured["response_text"])
            print(json.dumps(data, indent=4, ensure_ascii=False))
        except Exception:
            text = captured["response_text"]
            print(text[:3000] + ("..." if len(text) > 3000 else ""))
    else:
        print("❌ Vẫn không lấy được dữ liệu sau khi bypass.")
    print("==============================")

    try:
        await page.close()
    except Exception:
        pass
    await browser.close()


if __name__ == "__main__":
    asyncio.run(test_cookie_ajax())

