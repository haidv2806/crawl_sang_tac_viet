# Crawler sangtacviet.app

Công cụ crawl truyện từ [sangtacviet.app](https://sangtacviet.app) và đẩy lên backend API.

## Cài đặt

```bash
# Tạo và kích hoạt virtual environment
python -m venv myenv
myenv\Scripts\activate      # Windows

# Cài thư viện
pip install playwright requests aiohttp beautifulsoup4
playwright install chromium
```

## Cấu hình (`config.py`)

| Biến | Mặc định | Ý nghĩa |
|------|----------|---------|
| `BASE_URL` | `http://localhost:3000` | URL backend API |
| `JWT_TOKEN` | — | Token xác thực backend |
| `CHAPTERS_PER_VOLUME` | `100` | Số chương mỗi volume |
| `HEADLESS` | `False` | `False` bắt buộc (site chặn headless) |

## Chạy

### Crawl 1 cuốn sách cụ thể

```bash
python crawl_stv.py --url https://sangtacviet.app/truyen/fanqie/1/7244246368233983032/
```

### Crawl theo search API

```bash
# Crawl truyện dịch, tối thiểu 100 chương, trang 1
python crawl_stv.py --type dich --minc 100 --pages 1

# Crawl 2 trang, giới hạn 5 chương đầu mỗi sách (để test)
python crawl_stv.py --type dich --pages 2 --limit 5

# Lọc theo tag
python crawl_stv.py --type dich --tag "Huyền Huyễn" --pages 1
```

### Tham số dòng lệnh

| Tham số | Mặc định | Ý nghĩa |
|---------|----------|---------|
| `--url` | — | URL trực tiếp 1 cuốn sách |
| `--type` | `dich` | Loại truyện (`dich`, `trxs2`, `qidian`...) |
| `--tag` | _(rỗng)_ | Tag lọc |
| `--minc` | `100` | Số chương tối thiểu |
| `--pages` | `1` | Số trang search cần crawl |
| `--limit` | _(không giới hạn)_ | Giới hạn số chương mỗi sách |

## Kiến trúc

```
crawl_stv.py           ← Entry point chính
├── stv_book.py        ← Parse thông tin sách (aiohttp)
├── stv_chapters.py    ← Lấy danh sách chương (Playwright cookie + requests)
├── stv_chapter_content.py  ← Lấy nội dung chương (requests, tự refresh cookie)
├── stv_categories.py  ← Map tag → category_id
└── config.py          ← Cấu hình
```

## Lưu ý quan trọng

> **Browser không headless:**  
> `sangtacviet.app` detect headless automation và chặn XHR.  
> Script sẽ mở cửa sổ Chromium khi cần lấy cookie mới. Đây là bình thường.

> **Xử lý Cloudflare Challenge:**  
> Nếu site hiện trang "Verify you are human", script sẽ in cảnh báo ra terminal.  
> Hãy nhìn vào cửa sổ trình duyệt và click vào ô xác minh.  
> Nhờ sử dụng **Persistent Context**, bạn chỉ cần giải captcha một vài lần đầu, sau đó session sẽ được lưu lại trong thư mục `browser_data`.
