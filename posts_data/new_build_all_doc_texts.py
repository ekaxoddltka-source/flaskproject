import json

aezen_path = "posts_data/aezen_articles.json"
okky_path = "posts_data/okky_questions.csv"

all_texts = []

# 1) AEZEN JSON
with open(aezen_path, "r", encoding="utf-8") as f:
    aezen = json.load(f)

for art in aezen:
    title = art.get("title", "")
    content = art.get("board_content", "") or ""
    text = f"{title} {content}".strip()
    all_texts.append(text)

# 2) OKKY CSV
import csv

with open(okky_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        title = row.get("title", "")
        content = row.get("content", "") or ""
        text = f"{title} {content}".strip()
        all_texts.append(text)

# 저장
with open("posts_data/all_doc_texts.json", "w", encoding="utf-8") as f:
    json.dump(all_texts, f, ensure_ascii=False, indent=2)

print("완료: posts_data/all_doc_texts.json 생성됨")
