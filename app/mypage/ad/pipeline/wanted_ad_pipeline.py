import pymysql
import json
import os
from sentence_transformers import SentenceTransformer
from app.mypage.ad.preprocess.clean_text import clean_text
from app.mypage.ad.preprocess.keyword_extract import extract_keywords


# ==========================
# DB CONFIG
# ==========================
DB_CONFIG = {
    "host": "192.168.60.136",
    "user": "jwh",
    "password": "ezen",
    "db": "aezen",
    "cursorclass": pymysql.cursors.DictCursor,
}

# ==========================
# FILE PATH
# ==========================
BASE_DIR = r"D:\jeong\flaskproject\app\mypage\ad\crawlers"
JSON_FILE = os.path.join(BASE_DIR, "wanted_ads_final.json")

# ==========================
# EMBEDDING MODEL
# ==========================
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed(text: str):
    return model.encode(text).tolist()


# ==========================
# 1) 신규 광고 INSERT
# ==========================
def insert_new_ads(cursor, ads):
    cursor.execute("SELECT ad_title FROM ad")
    existing_titles = {row["ad_title"] for row in cursor.fetchall()}

    sql = """
        INSERT INTO ad (ad_title, description, landing_url, ad_image_url, ad_category, ad_priority, is_active)
        VALUES (%s, %s, %s, %s, 2, 0, 1)
    """

    insert_count = 0

    for ad in ads:
        title = clean_text(ad["ad_title"])

        if title in existing_titles:
            continue

        cursor.execute(sql, (
            title,
            "",  # description은 사용 안함
            ad["landing_url"],
            ad["ad_image_url"]
        ))

        insert_count += 1

    print(f"✔ 신규 원티드 광고 {insert_count}개 INSERT 완료")


# ==========================
# 2) keyword 업데이트
# ==========================
def update_keywords(cursor):
    cursor.execute("""
        SELECT ad_id, ad_title 
        FROM ad 
        WHERE ad_category = 2
    """)
    ads = cursor.fetchall()

    sql = """
        UPDATE ad SET ad_keywords = %s WHERE ad_id = %s
    """

    count = 0
    for ad in ads:
        keywords = extract_keywords(ad["ad_title"])
        kw_str = ", ".join(keywords)
        cursor.execute(sql, (kw_str, ad["ad_id"]))
        count += 1

    print(f"✔ 원티드 광고 키워드 업데이트 완료: {count}개")


# ==========================
# 3) embedding 업데이트
# ==========================
def update_embeddings(cursor):
    cursor.execute("""
        SELECT ad_id, ad_title, ad_keywords
        FROM ad
        WHERE ad_category = 2
    """)
    ads = cursor.fetchall()

    sql = """
        UPDATE ad SET ad_embedding = %s WHERE ad_id = %s
    """

    count = 0
    for ad in ads:
        text = f"{ad['ad_title']} {ad['ad_keywords'] or ''}"
        vec = embed(text)

        cursor.execute(sql, (json.dumps(vec), ad["ad_id"]))
        count += 1

    print(f"✔ 원티드 광고 임베딩 업데이트 완료: {count}개")


# ==========================
# MAIN PIPELINE
# ==========================
def main():
    print("🚀 원티드 광고 파이프라인 시작")

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        ads = json.load(f)

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    insert_new_ads(cursor, ads)
    update_keywords(cursor)
    update_embeddings(cursor)

    conn.commit()
    cursor.close()
    conn.close()

    print("🎉 원티드 광고 파이프라인 완료 — 기존 광고 유지 + 신규 광고 추가 완료!")


if __name__ == "__main__":
    main()
