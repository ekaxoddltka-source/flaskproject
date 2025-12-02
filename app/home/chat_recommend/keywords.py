# app/home/chat_recommend/keywords.py
import re
from konlpy.tag import Okt
from sklearn.feature_extraction.text import TfidfVectorizer
from itertools import combinations
import numpy as np
import warnings

# sklearn UserWarning 무시
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

okt = Okt()

def preprocess_board_post(post):
    """
    board_title, board_content 전처리
    """
    # 1) 제목 전처리
    title = post.get('board_title', '').strip()
    title = re.sub(r'\([^)]*\)', '', title)        # 괄호 안 제거
    title = re.sub(r'[^\w가-힣\s\-]', '', title)    # 한글/영어/숫자/공백/- 제외 제거
    title = re.sub(r'\s+', ' ', title)
    post['board_title'] = title.strip()

    # 2) 내용 전처리
    content = post.get('board_content', '').strip()
    content = re.sub(r'\n+', ' ', content)
    content = re.sub(r'[^\w가-힣\s\.,!?]', '', content)  # 의미 있는 특수문자만
    content = re.sub(r'\s+', ' ', content)
    post['board_content'] = content.strip()

    return post

def extract_keywords_tfidf(text, top_n=5, ngram_range=(1,2)):
    """
    전처리된 텍스트에서 한국어 명사 + 영어/외래어 추출
    TF-IDF 기반 키워드 추출
    """
    if not text:
        return []

    # 1) 형태소 분석 및 영어 추출
    words = [word for word, pos in okt.pos(text) if pos in ["Noun", "Alpha", "Foreign"]]
    english_words = re.findall(r'\b[a-zA-Z]+\b', text)
    words.extend(english_words)

    if not words:
        return []

    # 2) n-gram 후보 생성
    candidates = set(words)
    for r in range(2, ngram_range[1]+1):
        for comb in combinations(words, r):
            candidates.add(" ".join(comb))
    candidates = list(candidates)

    # 3) TF-IDF 계산
    doc = [" ".join(words)]
    vectorizer = TfidfVectorizer(vocabulary=candidates, lowercase=False)
    tfidf_matrix = vectorizer.fit_transform(doc)
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray()[0]

    # 4) 상위 top_n 키워드 선택
    keyword_scores = dict(zip(feature_names, scores))
    top_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return [word for word, _ in top_keywords]

def extract_keywords_from_posts(posts, top_n=5):
    """
    board 게시글 리스트에서 키워드 추출
    """
    all_keywords = []

    for post in posts:
        post = preprocess_board_post(post)
        text = f"{post.get('board_title','')} {post.get('board_content','')}"
        keywords = extract_keywords_tfidf(text, top_n=top_n)
        all_keywords.append({
            "board_no": post.get("board_no"),
            "board_title": post.get("board_title"),
            "keywords": keywords
        })

    return all_keywords
