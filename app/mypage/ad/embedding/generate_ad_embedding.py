# app/mypage/ad/embedding/generate_ad_embeddings.py

import pymysql
import json
from sentence_transformers import SentenceTransformer

# Flask 안 쓰는 독립 스크립트라서 DB 정보를 직접 적어줌
DB_CONFIG = {
    "host": "192.168.60.136",
    "user": "jwh",
    "password": "ezen",
    "db": "aezen",
    "cursorclass": pymysql.cursors.DictCursor,
}

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def build_embedding(text: str):
    return model.encode(text).tolist()

def main():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 1) 활성화된 광고만 가져오기
    cursor.execute("""
        SELECT ad_id, ad_title, description, ad_keywords
        FROM ad
        WHERE is_active = 1
    """)
    ads = cursor.fetchall()

    for ad in ads:
        text = f"{ad['ad_title']} {ad['description'] or ''} {ad['ad_keywords'] or ''}"
        vec = build_embedding(text)

        cursor.execute(
            "UPDATE ad SET ad_embedding = %s WHERE ad_id = %s",
            (json.dumps(vec), ad["ad_id"])
        )
        print("updated ad_id:", ad["ad_id"])

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ 광고 임베딩 업데이트 완료")

if __name__ == "__main__":
    main()
