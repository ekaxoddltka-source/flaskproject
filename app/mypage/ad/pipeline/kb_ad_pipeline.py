import pymysql
import json
from sentence_transformers import SentenceTransformer
import os
from app.mypage.ad.preprocess.clean_text import clean_text


# ==========================
#  DB 설정
# ==========================
DB_CONFIG = {
    "host": "192.168.60.136",
    "user": "jwh",
    "password": "ezen",
    "db": "aezen",
    "cursorclass": pymysql.cursors.DictCursor,
}

# ==========================
#  파일 경로
# ==========================
BASE_DIR = r"D:\jeong\flaskproject\app\mypage\ad\preprocess"
RAW_FILE = os.path.join(BASE_DIR, "kyobo_raw.json")
KW_FILE = os.path.join(BASE_DIR, "kyobo_keywords.json")

# ==========================
#  임베딩 모델
# ==========================
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def build_embedding(text: str):
    return model.encode(text).tolist()


# =====================================================================
#  1) 기존 광고 유지 + 새로운 raw.json 광고만 INSERT (카테고리 = 1)
# =====================================================================
def insert_new_ads(cursor):
    with open(RAW_FILE, "r", encoding="utf-8") as f:
        raw_ads = json.load(f)

    print(f"📌 kyobo_raw.json 로드됨: {len(raw_ads)}개")

    # 기존 제목 가져오기
    cursor.execute("SELECT ad_title FROM ad")
    existing_titles = {row["ad_title"] for row in cursor.fetchall()}

    sql = """
        INSERT INTO ad
            (ad_title, description, landing_url, ad_image_url, ad_category, ad_priority, is_active)
        VALUES
            (%s, %s, %s, %s, 1, 0, 1)
    """

    insert_count = 0

    for ad in raw_ads:
        title = clean_text(ad["ad_title"].strip())

        # 기존 광고면 skip
        if title in existing_titles:
            continue

        cursor.execute(sql, (
            title,
            ad.get("description", "") or "",
            ad["landing_url"],
            ad["ad_image_url"],
        ))

        insert_count += 1

    print(f"✔ 신규 교보 광고 {insert_count}개 DB 삽입 완료")


# =====================================================================
#  2) 교보 광고(ad_category=1)에만 keywords 업데이트
# =====================================================================
def update_keywords(cursor):
    with open(KW_FILE, "r", encoding="utf-8") as f:
        kw_data = json.load(f)

    # DB title → ad_id 매핑
    cursor.execute("SELECT ad_id, ad_title FROM ad WHERE ad_category = 1")
    ad_map = {row["ad_title"]: row["ad_id"] for row in cursor.fetchall()}

    sql = """
        UPDATE ad
        SET ad_keywords = %s
        WHERE ad_id = %s
    """

    update_count = 0

    for item in kw_data:
        title = clean_text(item["ad_title"].strip())

        if title not in ad_map:
            continue  

        kw_str = ", ".join(item["keywords"])
        cursor.execute(sql, (kw_str, ad_map[title]))
        update_count += 1

    print(f"✔ 교보 광고 키워드 업데이트 완료: {update_count}개")


# =====================================================================
#  3) 교보 광고(ad_category=1)에만 embedding 업데이트
# =====================================================================
def update_embeddings(cursor):
    # 교보 광고만 가져오기
    cursor.execute("""
        SELECT ad_id, ad_title, ad_keywords, description
        FROM ad
        WHERE ad_category = 1
    """)
    ads = cursor.fetchall()

    # 이미 embedding 존재하는 광고 제외
    cursor.execute("SELECT ad_id FROM ad WHERE ad_embedding IS NOT NULL")
    embedded_ids = {row["ad_id"] for row in cursor.fetchall()}

    sql = """
        UPDATE ad
        SET ad_embedding = %s
        WHERE ad_id = %s
    """

    count = 0

    for ad in ads:
        if ad["ad_id"] in embedded_ids:
            continue  

        text = f"{ad['ad_title']} {ad['ad_keywords'] or ''} {ad['description'] or ''}"
        vec = build_embedding(text)

        cursor.execute(sql, (json.dumps(vec), ad["ad_id"]))
        count += 1
        print(f"  - 임베딩 생성 완료: ad_id={ad['ad_id']}")

    print(f"✔ 교보 광고 신규 임베딩 생성 완료: {count}개")


# =====================================================================
#  전체 실행
# =====================================================================
def main():
    print("🚀 교보 광고 파이프라인 시작")

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    insert_new_ads(cursor)
    update_keywords(cursor)
    update_embeddings(cursor)

    conn.commit()
    cursor.close()
    conn.close()

    print("🎉 교보 광고 파이프라인 완료 — 기존 광고 유지 + 신규 광고 추가 완료")


if __name__ == "__main__":
    main()
