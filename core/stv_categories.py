# stv_categories.py - Mapping tag sangtacviet.app → category_id trong DB
# Tất cả truyện đều mặc định có Chinese Novel (ID=10)

# Bảng mapping: keyword (lowercase, không dấu hay có một phần) → category_id
# Tìm theo "contains" để xử lý biến thể tên tag

CHINESE_NOVEL_ID = 10  # Mặc định tất cả đều là Chinese Novel

# Map: fragment (lower) → category_id
# Một tag STV có thể map vào nhiều category
_KEYWORD_MAP = [
    # Action / Chiến đấu
    ("hanh dong", 1),
    ("nhiet huyet", 1),
    ("chien dau", 1),
    ("chien than", 1),
    ("vo thuat", 1),

    # Adapted to Anime
    ("anime dien sinh", 2),
    ("chuyen the anime", 2),

    # Adapted to Manga / Manhua
    ("chuyen the manga", 4),
    ("manhua", 4),

    # Adult (18+)
    ("18+", 11),
    ("nguoi lon", 11),
    ("hen", 11),       # tag "hidehen", "hen" trên STV

    # Adventure
    ("mao hiem", 6),
    ("tham hiem", 6),
    ("phieu luu", 6),

    # Age Gap
    ("hao mon tong giam doc", 7),
    ("chenh lech giai cap", 7),

    # Boys Love / Đam mỹ
    ("dam my", 8),
    ("ngon dam", 8),
    ("song nam chinh", 8),

    # Character Growth
    ("truong thanh", 9),
    ("nhan vat truong thanh", 9),

    # Comedy
    ("hai huoc", 17),
    ("khoi hai", 17),
    ("ham cuoi", 17),

    # Cooking / Cuộc sống nông thôn
    ("nau an", 12),
    ("am thuc", 12),
    ("lam ruong", 12),
    ("duong sinh", 12),

    # Different Social Status
    ("hao mon", 13),

    # Drama
    ("chinh kich", 14),

    # Ecchi
    ("ecchi", 15),

    # Fantasy / Huyền huyễn
    ("huyen huyen", 17),
    ("ky huyen", 17),
    ("tien hiep", 17),
    ("ki huyen", 17),
    ("di the", 17),
    ("di gioi", 17),
    ("huyen tuong", 17),
    ("khoahuyenmaphap", 17),
    ("huyenhuyenmaphap", 17),
    ("ma phap", 28),    # Magic
    ("phap thuat", 28),

    # Female Protagonist
    ("nu chinh", 18),
    ("nu ton", 18),

    # Game / Võng du
    ("vong du", 19),
    ("tro choi", 19),
    ("game", 19),
    ("he thong", 19),    # hệ thống = system → dùng trong game/cultivation

    # Gender Bender
    ("bien than", 20),
    ("sfacg", 20),

    # Harem
    ("hau cung", 21),
    ("harem", 21),

    # Historical / Lịch sử
    ("lich su", 22),
    ("co dai", 22),
    ("quan su lich su", 22),
    ("lich su vo can cu", 22),
    ("lich su than thoai", 22),
    ("trung quoc lich su", 22),
    ("ngoai quoc lich su", 22),

    # Horror / Kinh dị
    ("kinh di", 23),
    ("kinh khung", 23),
    ("linh di", 23),
    ("quy di", 23),

    # Incest
    ("loan luan", 24),

    # Isekai / Xuyên qua
    ("xuyen qua", 25),
    ("xuyen khong", 25),
    ("di gioi", 25),
    ("trung sinh", 25),
    ("isekai", 25),
    ("xuyen thu", 25),
    ("nhanh xuyen", 25),

    # Korean Novel
    ("han quoc", 27),

    # Martial Arts / Võ hiệp
    ("vo hiep", 29),
    ("vo thuat", 29),
    ("luyen cong", 29),
    ("luyen dan", 29),

    # Military
    ("quan su", 32),
    ("chien tranh", 32),
    ("wars", 62),
    ("quan doi", 32),

    # Mystery / Huyền nghi
    ("huyen nghi", 34),
    ("trinh tham", 34),
    ("bi an", 34),

    # One shot / Ngắn
    ("ngan co su", 36),
    ("ngan khac", 36),

    # Parody / Đồng nhân
    ("dong nhan", 44),
    ("fan fiction", 44),

    # Psychological
    ("tam ly", 45),

    # Reverse Harem
    ("reverse harem", 46),

    # Romance / Ngôn tình
    ("ngon tinh", 47),
    ("tinh yeu", 47),
    ("tinh cam", 47),
    ("hon nhan", 47),
    ("diem van", 47),
    ("ngot sung", 47),
    ("thuan ai", 47),

    # School Life
    ("hoc duong", 48),
    ("san truong", 48),

    # Science Fiction / Khoa huyễn
    ("khoa huyen", 49),
    ("khoa hoc vien tuong", 49),
    ("tan the", 49),
    ("tuong lai", 49),

    # Slice of Life / Đô thị
    ("do thi", 55),
    ("sinh hoat", 55),
    ("cuoc song", 55),

    # Slow Life / Điền văn
    ("diem van", 56),
    ("nhe nhom", 56),
    ("nhan ha", 56),

    # Sports
    ("the thao", 57),
    ("bong da", 57),
    ("bong chuyen", 57),

    # Super Power / Dị năng
    ("di nang", 58),
    ("sieu nang luc", 58),
    ("sieu anh hung", 58),

    # Supernatural
    ("than bi", 59),
    ("quy bi", 59),

    # Tragedy
    ("bi kich", 61),
    ("tham kich", 61),

    # Workplace
    ("cong so", 64),
    ("van phong", 64),
    ("quan truong", 64),

    # Yuri / Bách hợp
    ("bach hop", 65),
    ("yuri", 65),
    ("chi em yeu nhau", 65),
    ("dong tinh nu", 65),
]


def _normalize(text: str) -> str:
    """Chuyển về lowercase, bỏ dấu cơ bản để so sánh."""
    import unicodedata
    text = text.lower().strip()
    # Normalize unicode và bỏ combining chars để dễ match
    # Không bỏ hoàn toàn vì một số từ cần phân biệt
    return text


def _remove_diacritics(text: str) -> str:
    """Bỏ dấu tiếng Việt để match keyword."""
    import unicodedata
    # Chuyển sang dạng NFD rồi bỏ combining diacritical marks
    normalized = unicodedata.normalize('NFD', text.lower())
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')


def map_tags(tag_list: list[str]) -> list[int]:
    """
    Chuyển list tag STV → list category_id.
    Luôn bao gồm CHINESE_NOVEL_ID (10).
    Bỏ qua tag không map được (không fallback).
    """
    result = {CHINESE_NOVEL_ID}  # Mặc định Chinese Novel

    for tag in tag_list:
        tag_clean = _remove_diacritics(tag)
        for keyword, cat_id in _KEYWORD_MAP:
            keyword_clean = _remove_diacritics(keyword)
            if keyword_clean in tag_clean:
                result.add(cat_id)
                break  # Mỗi tag chỉ match 1 category đầu tiên

    return sorted(result)


if __name__ == "__main__":
    # Test
    test_tags = ["Huyền Huyễn", "Xuyên Qua", "Ngôn Tình", "Hệ Thống", "blah unknown"]
    print("Tags:", test_tags)
    print("Category IDs:", map_tags(test_tags))
