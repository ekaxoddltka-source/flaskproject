# posts_data/build_aezen_full_json.py

import pymysql
import json

# 🔥 당신의 DB 설정에 맞게 수정
DB = {
    "host": "192.168.60.136",
    "user": "jwh",
    "password": "ezen",
    "db": "aezen",
    "charset": "utf8",
}

conn = pymysql.connect(**DB)
cur = conn.cursor(pymysql.cursors.DictCursor)

print("📌 DB에서 게시글 불러오는 중...")

cur.execute("""
    SELECT 
        board_no, 
        board_title AS title, 
        board_content AS content
    FROM board
    WHERE board_deleted = 0
""")

rows = cur.fetchall()

print(f"📌 총 {len(rows)}개의 게시글을 불러옴")

with open("posts_data/aezen_articles_full.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)

print("✅ aezen_articles_full.json 생성 완료")
