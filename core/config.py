# config.py - Cấu hình crawler sangtacviet.app

JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJqdGkiOiI0ZjZlNTViOS1iNjZlLTRlOTMtYWE1Mi05ZjRiOTk1MjU0ODkiLCJpYXQiOjE3NzM3NzMxMTgsImV4cCI6MTc3NjM2NTExOH0.ZqXGVJx5cr0N4_nVvCS8_2C5GUj2RFm1kFyE2WJOsQ8"

BASE_URL = "https://localhost:3000"

HEADERS = {
    "Authorization": f"Bearer {JWT_TOKEN}"
}

STV_BASE = "https://sangtacviet.app"

# Cấu hình Browser
HEADLESS = True  # False = hiển thị cửa sổ browser (tránh bị phát hiện là bot)
BROWSER_TIMEOUT = 90000  # ms - tăng lên 90s để chờ JS render
USER_DATA_DIR = "./browser_data" # Thư mục lưu session/cookies

# Bao nhiêu chương mỗi volume
CHAPTERS_PER_VOLUME = 100

# Crawl tất cả hay chỉ N trang đầu (None = tất cả)
MAX_PAGES = 1000

# Số luồng song song crawl chương (số tab browser chạy cùng lúc)
MAX_WORKERS = 3

# Khi gặp 429: chờ bao nhiêu giây rồi thử lại
RATE_LIMIT_BACKOFF_INITIAL = 10   # giây ban đầu
RATE_LIMIT_BACKOFF_MAX = 600      # tối đa 10 phút
