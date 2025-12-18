# posts_data/auto_expand_keywords.py
import json
import re
import pymysql
from collections import Counter
from app.filters.tech_translate import KOREAN_TO_ENGLISH

# ===============================
# DB 연결 (run.py 설정과 동일)
# ===============================
def get_conn():
    return pymysql.connect(
        host="192.168.60.136",
        user="jwh",
        password="ezen",
        db="aezen",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

# ===============================
# 텍스트 정규화
# ===============================
def normalize(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    for kr, en in KOREAN_TO_ENGLISH.items():
        text = text.replace(kr, en)
    return text

# ===============================
# 메인 로직
# ===============================
def main():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT board_title, board_content
        FROM board
        WHERE board_deleted = 0
    """)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    print(f"📄 게시글 수: {len(rows)}")

    counter = Counter()

    for r in rows:
        text = normalize(f"{r['board_title']} {r['board_content']}")

        # 영어 단어만 추출 (3자 이상)
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9\+\#\-]{2,}", text)
        counter.update(words)

    print(f"🔍 추출된 단어 수: {len(counter)}")

    # 최소 5회 이상 등장한 키워드만
    keywords = [
        w for w, c in counter.items()
        if c >= 2 and len(w) <= 30
    ]

    print(f"✅ 저장 대상 키워드 수: {len(keywords)}")

    # ===============================
    # 파일 저장 (무조건 생성)
    # ===============================
    with open("posts_data/auto_tech_keywords.json", "w", encoding="utf-8") as f:
        json.dump(sorted(set(keywords)), f, ensure_ascii=False, indent=2)

    print("🎉 auto_tech_keywords.json 생성 완료")

if __name__ == "__main__":
    main()
