import json
import pymysql
from flask import current_app

def save_ad_list(ad_list):
    conn = current_app.get_db_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO ad (ad_title, description, ad_image_url, landing_url, ad_embedding, ad_keywords, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, 1)
    """

    for ad in ad_list:
        cursor.execute(sql, (
            ad["title"],
            ad["description"],
            ad["image"],
            ad["url"],
            json.dumps(ad["embedding"], ensure_ascii=False),
            ",".join(ad["keywords"])
        ))

    conn.commit()
    cursor.close()
    conn.close()
