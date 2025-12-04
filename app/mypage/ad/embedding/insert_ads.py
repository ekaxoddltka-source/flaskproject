import pymysql
import json

DB_CONFIG = {
    "host": "192.168.60.136",
    "user": "jwh",
    "password": "ezen",
    "db": "aezen",
    "cursorclass": pymysql.cursors.DictCursor,
}

JSON_FILE = r"D:\jeong\flaskproject\app\mypage\ad\preprocess\inflearn_courses_preprocessed.json"

def main():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 기존 광고 삭제 (원하면 유지 가능)
    cursor.execute("DELETE FROM ad")
    conn.commit()

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        ads = json.load(f)

    sql = """
        INSERT INTO ad (ad_title, description, landing_url, ad_image_url, ad_category, ad_priority, is_active)
        VALUES (%s, %s, %s, %s, 1, 0, 1)
    """

    for ad in ads:
        cursor.execute(sql, (
            ad["ad_title"],
            ad["description"],
            ad["url"],
            ad["image"]
        ))

    conn.commit()
    cursor.close()
    conn.close()

    print(f"{len(ads)}개의 광고를 DB에 삽입 완료했습니다.")

if __name__ == "__main__":
    main()
