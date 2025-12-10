import re
from konlpy.tag import Okt
from itertools import combinations
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

okt = Okt()

def extract_keywords(text, top_n=5, ngram_range=(1,2)):
    """
    텍스트에서 TF-IDF 기반 한국어 & 영어 키워드 상위 top_n 추출
    (파일 로드, 저장, 반복 처리 없음 — 순수 함수)
    """
    if not text:
        return []

    # 1) 형태소 분석 (명사, 영어)
    words = [w for w, pos in okt.pos(text) if pos in ["Noun", "Alpha", "Foreign"]]
    english_words = re.findall(r'\b[a-zA-Z]+\b', text)
    words.extend(english_words)

    if not words:
        return []

    # 2) n-gram 생성
    candidates = set(words)
    for n in range(2, ngram_range[1] + 1):
        for comb in combinations(words, n):
            candidates.add(" ".join(comb))
    candidates = list(candidates)

    # 3) TF-IDF 계산
    doc = [" ".join(words)]
    vectorizer = TfidfVectorizer(vocabulary=candidates, lowercase=False)
    tfidf_matrix = vectorizer.fit_transform(doc)

    scores = tfidf_matrix.toarray()[0]
    feature_names = vectorizer.get_feature_names_out()

    keyword_scores = list(zip(feature_names, scores))
    keyword_scores.sort(key=lambda x: x[1], reverse=True)

    return [kw for kw, score in keyword_scores[:top_n]]
