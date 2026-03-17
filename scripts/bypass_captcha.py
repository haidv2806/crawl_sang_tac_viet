import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.req_config import req_post

# ---- CAU HINH ----
URL = "https://sangtacviet.app/index.php?ngmar=verifyca"

# Form data tu user cung cap
DATA = {
    "ajax": "verifycaptcha",
    "token": "CAKF",
    "purpose": "read",
    "provider": "sangtacviet"
}
# ------------------

def main():
    try:
        print(f"Sending POST request with data: {DATA}")
        # REQConfig automatically handles cookies from auth.json
        resp = req_post(URL, data=DATA, timeout=30)
        
        print(f"Status Code: {resp.status_code}")
        print(f"Response Body: {resp.text}")

        try:
            result = resp.json()
            print(f"\nParsed JSON: {result}")
            if result.get("code") == "0" or result.get("status") == "success":
                print("\n✅ CAPTCHA BYPASS SUCCESS!")
            else:
                print("\n❌ CAPTCHA BYPASS FAILED (check token/cookies)")
        except:
            if resp.text.strip().lower() == "success":
                print("\n✅ CAPTCHA BYPASS SUCCESS! (Plain text response)")
            else:
                print(f"\nResponse is not JSON and not 'success'. Raw: {resp.text}")

    except Exception as e:
        print(f"\nException: {e}")

if __name__ == "__main__":
    main()
