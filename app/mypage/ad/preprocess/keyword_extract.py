import json
import os
import re
from konlpy.tag import Okt
from sklearn.feature_extraction.text import TfidfVectorizer
from itertools import combinations
import warnings

# sklearn UserWarning 무시
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

# 형태소 분석기
okt = Okt()

def extract_keywords_tfidf(text, top_n=5, ngram_range=(1,2)):
    # 1) 한국어 명사 + 영어/외래어 추출
    words = [word for word, pos in okt.pos(text) if pos in ["Noun", "Alpha", "Foreign"]]
    english_words = re.findall(r'\b[a-zA-Z]+\b', text)
    words.extend(english_words)

    if not words:
        return []

    # 2) n-gram 후보 생성 (1~2 단어 연속)
    candidates = set(words)  # 단일 단어
    for r in range(2, ngram_range[1]+1):
        for comb in combinations(words, r):
            candidates.add(" ".join(comb))
    candidates = list(candidates)

    # 3) TF-IDF 계산 (대문자 유지)
    doc = [" ".join(words)]
    vectorizer = TfidfVectorizer(vocabulary=candidates, lowercase=False)
    tfidf_matrix = vectorizer.fit_transform(doc)
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray()[0]

    # 4) 상위 top_n 키워드 선택
    keyword_scores = dict(zip(feature_names, scores))
    top_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return [word for word, _ in top_keywords]

# -------------------------------------------------------------
# JSON 파일 불러오기
# -------------------------------------------------------------
preprocessed_path = r"D:\jwh\flaskproject\app\home\ad\preprocess\inflearn_courses_preprocessed.json"
with open(preprocessed_path, "r", encoding="utf-8") as f:
    courses = json.load(f)

# 저장 경로
save_path = r"D:\jwh\flaskproject\app\home\ad\embedding"
os.makedirs(save_path, exist_ok=True)

all_keywords = []

# -------------------------------------------------------------
# TF-IDF 키워드 생성 루프
# -------------------------------------------------------------
for idx, course in enumerate(courses):
    if idx % 20 == 0:
        print(f"{idx}/{len(courses)} 처리 중...")

    text = course.get("ad_title", "") + " " + course.get("description", "")

    keywords_list = extract_keywords_tfidf(text, top_n=5)

    all_keywords.append({
        "ad_title": course.get("ad_title", ""),
        "keywords": keywords_list
    })

    # 테스트 출력
    if idx < 5:
        print(course.get("ad_title", "No Title"))
        print("Keywords:", keywords_list)
        print("-"*50)

# -------------------------------------------------------------
# 결과 저장
# -------------------------------------------------------------
output_file = os.path.join(save_path, "keywords_tfidf_uppercase_safe.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_keywords, f, ensure_ascii=False, indent=4)

print(f"TF-IDF 기반 키워드를 {output_file} 에 저장했습니다.")