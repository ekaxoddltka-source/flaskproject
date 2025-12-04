"""
광고 파이프라인 실행 스크립트

1) 크롤링 JSON 로드
2) 텍스트 정제(clean_text)
3) 키워드 추출(extract_keywords)
4) 임베딩 생성(embed_text)
5) DB 저장(save_ad_list)
"""
from app import create_app
import json
import os
import numpy as np

from app.mypage.ad.preprocess.clean_text import clean_text
from app.mypage.ad.preprocess.keyword_extract import extract_keywords
from app.mypage.ad.embedding.embedding_utils import embed_text
from app.mypage.ad.db.ad_repository import save_ad_list

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RAW_FILE = os.path.join(BASE_DIR, "preprocess", "inflearn_courses.json")
PROCESSED_FILE = os.path.join(BASE_DIR, "preprocess", "inflearn_courses_preprocessed.json")


print("[1/5] 광고 JSON 불러오는 중...")

with open(RAW_FILE, "r", encoding="utf-8") as f:
    ads = json.load(f)

print(f" - 로드됨: {len(ads)}개")


# ----------------------------------------------------------------------
# 2) 텍스트 정제 + 키워드
# ----------------------------------------------------------------------
print("[2/5] 텍스트 정제 및 키워드 추출 중...")

processed_ads = []
for idx, ad in enumerate(ads):
    if idx % 20 == 0:
        print(f"  - 처리 {idx}/{len(ads)}")

    title = clean_text(ad.get("title", ""))
    desc = clean_text(ad.get("description", ""))
    url = ad.get("url", "")
    image = ad.get("image", "")

    keywords = extract_keywords(f"{title} {desc}")

    processed_ads.append({
        "title": title,
        "description": desc,
        "keywords": keywords,
        "url": url,
        "image": image
    })

with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
    json.dump(processed_ads, f, ensure_ascii=False, indent=4)

print(" - 저장 완료:", PROCESSED_FILE)


# ----------------------------------------------------------------------
# 3) 임베딩 생성
# ----------------------------------------------------------------------
print("[3/5] 광고 임베딩 생성 중...")

embedded_ads = []
for idx, ad in enumerate(processed_ads):
    if idx % 20 == 0:
        print(f"  - 임베딩 {idx}/{len(processed_ads)}")

    text = f"{ad['title']} {ad['description']} {' '.join(ad['keywords'])}"
    vec = embed_text(text)

    if hasattr(vec, "tolist"):
        vec = vec.tolist()

    ad["embedding"] = vec
    embedded_ads.append(ad)

print(" - 임베딩 완료")


# -------------------------------------------------------------
# 4) DB 저장
# -------------------------------------------------------------
from app.mypage.ad.db.ad_repository import save_ad_list

app = create_app()

with app.app_context():
    save_ad_list(embedded_ads)

print("광고 Pipeline 완료.")

