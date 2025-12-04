import os
import time
import json
import re
import numpy as np

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from sentence_transformers import SentenceTransformer


# 저장 위치
SAVE_DIR = r"D:\jeong\flaskproject\app\mypage\ad\preprocess"
BASE_URL = "https://store.kyobobook.co.kr/bestseller/online/daily/domestic/33?page="


# -------------------------------------------------------------
# 1) Selenium 드라이버 생성
# -------------------------------------------------------------
def create_driver(headless=True):
    options = Options()
    # headless = False → 디버깅 모드
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1400,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


# -------------------------------------------------------------
# 2) 리스트 페이지 크롤링 (title, url, image)
# -------------------------------------------------------------
def crawl_list_pages(start=1, end=41):
    os.makedirs(SAVE_DIR, exist_ok=True)

    driver = create_driver(headless=True)
    results = []

    try:
        for page in range(start, end + 1):
            print(f"[리스트 크롤링] {page} 페이지")
            driver.get(BASE_URL + str(page))
            time.sleep(2)

            # lazy load 로딩 위해 스크롤
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            items = driver.find_elements(By.CSS_SELECTOR, "li.mt-9")
            print("  - 책 개수:", len(items))

            for item in items:
                try:
                    # 1) 제목 + 링크
                    title_link = item.find_element(By.CSS_SELECTOR, "div.ml-4 a.prod_link")
                    title = title_link.text.strip()
                    url = title_link.get_attribute("href")

                    # 2) 이미지
                    img_tag = item.find_element(
                        By.CSS_SELECTOR,
                        "div.w-\\[144px\\] img"
                    )
                    image = img_tag.get_attribute("src")

                    results.append({
                        "title": title,
                        "url": url,
                        "image": image
                    })
                except:
                    continue

    finally:
        driver.quit()

    save_path = os.path.join(SAVE_DIR, "kyobo_list.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"[완료] 리스트 크롤링 {len(results)}개 → {save_path}")
    return save_path


# -------------------------------------------------------------
# 3) 상세페이지 description 수집
# -------------------------------------------------------------
def add_descriptions(list_path):
    driver = create_driver(headless=True)

    with open(list_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    results = []

    try:
        for idx, book in enumerate(items, start=1):
            print(f"[상세 크롤링] {idx}/{len(items)} → {book['title']}")
            driver.get(book["url"])
            time.sleep(2)

            desc = ""
            # 1순위 selector
            try:
                desc = driver.find_element(By.CSS_SELECTOR, "p.prod_introduction").text.strip()
            except:
                pass

            # 백업 selector
            if not desc:
                try:
                    desc = driver.find_element(By.CSS_SELECTOR, "div.prod_introduction").text.strip()
                except:
                    desc = ""

            results.append({
                "ad_title": book["title"],
                "ad_image_url": book["image"],
                "landing_url": book["url"],
                "description": desc
            })

    finally:
        driver.quit()

    raw_path = os.path.join(SAVE_DIR, "kyobo_raw.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"[완료] 상세 수집 완료 → {raw_path}")
    return raw_path


# -------------------------------------------------------------
# 4) 텍스트 전처리
# -------------------------------------------------------------
def clean_text(text):
    if not text:
        return ""
    emoji_pattern = re.compile(
        "["  
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub("", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def preprocess(raw_path):
    with open(raw_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    cleaned = []
    for b in raw:
        cleaned.append({
            "ad_title": clean_text(b["ad_title"]),
            "description": clean_text(b["description"]),
            "url": b["landing_url"],
            "image": b["ad_image_url"]
        })

    clean_path = os.path.join(SAVE_DIR, "kyobo_clean.json")
    with open(clean_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=4)

    print(f"[완료] 전처리 완료 → {clean_path}")
    return clean_path


# -------------------------------------------------------------
# 5) 키워드 추출
# -------------------------------------------------------------
def extract_keywords(text, top_n=5):
    try:
        from konlpy.tag import Okt
        okt = Okt()
        nouns = okt.nouns(re.sub(r"[^가-힣a-zA-Z0-9 ]", " ", text))
        nouns = [n for n in nouns if len(n) > 1]
        freq = {}
        for n in nouns:
            freq[n] = freq.get(n, 0) + 1
        sorted_kw = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [k for k, _ in sorted_kw[:top_n]]

    except Exception:
        # fallback (konlpy 미설치 시)
        tokens = re.sub(r"[^가-힣a-zA-Z0-9 ]", " ", text).split()
        tokens = [t for t in tokens if len(t) > 1]
        return tokens[:top_n]


def make_keywords(clean_path):
    with open(clean_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = []

    for item in data:
        all_text = item["ad_title"] + " " + item["description"]
        keywords = extract_keywords(all_text, 5)
        result.append({
            "ad_title": item["ad_title"],
            "keywords": keywords
        })

    kw_path = os.path.join(SAVE_DIR, "kyobo_keywords.json")
    with open(kw_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(f"[완료] 키워드 생성 → {kw_path}")
    return kw_path


# -------------------------------------------------------------
# 6) 임베딩 생성
# -------------------------------------------------------------
def create_embeddings(keyword_path):
    with open(keyword_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    result = []

    for item in data:
        text = " ".join(item["keywords"])
        vec = model.encode(text).tolist()

        result.append({
            "ad_title": item["ad_title"],
            "keywords": item["keywords"],
            "embedding": vec
        })

    emb_path = os.path.join(SAVE_DIR, "kyobo_embeddings.json")
    with open(emb_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(f"[완료] 임베딩 생성 → {emb_path}")
    return emb_path


# -------------------------------------------------------------
# 실행
# -------------------------------------------------------------
if __name__ == "__main__":
    list_path = crawl_list_pages(1, 41)
    raw_path = add_descriptions(list_path)
    clean_path = preprocess(raw_path)
    kw_path = make_keywords(clean_path)
    emb_path = create_embeddings(kw_path)

    print("\n=== 전체 파이프라인 완료 ===")
