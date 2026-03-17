from core.config import STV_BASE
from core.req_config import req_get
import json
import re

# URL API lấy danh sách chương
CHAPTER_LIST_API = f"{STV_BASE}/index.php"

async def _get_chapter_list_raw(
    book_url: str,
    book_id: str,
    host: str,
    context = None, # Giữ tham số để không break code cũ, nhưng không dùng
    headless: bool = True, # Giữ tham số để không break code cũ
) -> dict | None:
    """
    Gọi API danh sách chương trực tiếp bằng REQConfig dùng cookie từ auth.json.
    """
    try:
        api_url = (
            f"{CHAPTER_LIST_API}"
            f"?ngmar=chapterlist&h={host}&bookid={book_id}&sajax=getchapterlist"
        )
        print(f"  📡 Gọi API chương (Direct): {api_url}")

        resp = req_get(api_url, referer=book_url, timeout=30)
        raw_text = resp.text
        
        if not raw_text.strip():
            print("  ⚠️ API trả về rỗng")
            return None

        return json.loads(raw_text)

    except Exception as e:
        print(f"  ❌ Lỗi lấy danh sách chương: {e}")
        return None

def _parse_chapter_data(json_data: dict) -> list[dict]:
    """
    Phân tích dữ liệu JSON từ API getchapterlist.
    Format data: "vol-/-chapId-/-title-//-vol-/-chapId-/-title-//..."
    Trả về danh sách dict: {volume, chapter_id, title, url}
    """
    if not json_data or json_data.get("code") != 1:
        code = json_data.get("code") if json_data else "N/A"
        err  = json_data.get("err", "") if json_data else ""
        print(f"  ❌ API lỗi (code={code}): {err}")
        return []

    raw_data = json_data.get("data", "")
    if not raw_data:
        print("  ⚠️ Không có dữ liệu chương")
        return []

    chapters = []
    entries = raw_data.split("-//-")
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("-/-")
        if len(parts) < 3:
            continue

        volume     = parts[0].strip()
        chapter_id = parts[1].strip()
        title      = parts[2].strip()
        # Làm sạch title (xóa \t, \n, <br>, &nbsp;)
        title = re.sub(r"[\t\n]+|<br>|&nbsp;", "", title).strip()
        title = re.sub(r"Thứ ([\d,]+) chương", r"Chương \1:", title, flags=re.IGNORECASE)

        chapters.append({
            "volume":     volume,
            "chapter_id": chapter_id,
            "title":      title,
        })

    return chapters

async def get_chapters(
    book_url: str,
    book_id: str,
    host: str,
    context = None,
    headless: bool = True,
) -> list[dict]:
    """
    Lấy toàn bộ danh sách chương của một sách.
    """
    json_data = await _get_chapter_list_raw(book_url, book_id, host, context, headless)
    chapters = _parse_chapter_data(json_data)

    # Gắn full URL cho từng chương
    for ch in chapters:
        ch["url"] = f"{STV_BASE}/truyen/{host}/{ch['volume']}/{book_id}/{ch['chapter_id']}/"

    return chapters
