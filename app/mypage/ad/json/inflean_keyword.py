import os
import json

BASE_DIR = os.path.dirname(__file__)

INPUT = os.path.join(BASE_DIR, "keywords_tfidf_uppercase_safe.json")
OUTPUT = os.path.join(BASE_DIR, "update_keywords.sql")

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

sql_lines = []

for item in data:
    title = item["ad_title"]
    keywords = item.get("keywords", [])
    
    keyword_str = ",".join(keywords)
    title_esc = title.replace("'", "''")
    keywords_esc = keyword_str.replace("'", "''")

    sql = f"UPDATE ad SET ad_keywords = '{keywords_esc}' WHERE ad_title = '{title_esc}';"
    sql_lines.append(sql)

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(sql_lines))

print("✔ SQL 생성 완료 :", OUTPUT)
