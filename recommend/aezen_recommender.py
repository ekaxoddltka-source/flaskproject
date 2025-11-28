# recommend/aezen_recommender.py

import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------
# Lazy Loading: 전역 변수는 None으로 두고 최초 요청 때만 로딩
# ---------------------------------------------------------
MODEL = None
ARTICLE_EMBEDDINGS = None
ARTICLE_META = None


# ---------------------------------------------------------
# 1) BERT 모델 로드 (최초 1회만)
# ---------------------------------------------------------
def load_model():
    global MODEL
    if MODEL is None:
        print("🔥 BERT 모델 최초 로딩 중... (약 4~7초)")
        MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return MODEL


# ---------------------------------------------------------
# 2) AEZEN 게시글 임베딩 / 메타 로드 (최초 1회만)
# ---------------------------------------------------------
def load_aezen_embeddings():
    global ARTICLE_EMBEDDINGS, ARTICLE_META
    if ARTICLE_EMBEDDINGS is None:
        print("🔥 게시글 임베딩 최초 로딩 중...")

        ARTICLE_EMBEDDINGS = np.load("recommend/aezen_embeddings.npy")

        with open("recommend/aezen_articles.json", "r", encoding="utf-8") as f:
            ARTICLE_META = json.load(f)

    return ARTICLE_EMBEDDINGS, ARTICLE_META


# ---------------------------------------------------------
# 3) 사용자 벡터 생성
# ---------------------------------------------------------
def build_user_vector(texts):
    """
    texts = 사용자가 읽거나 쓴 글/댓글/태그 등의 문장 리스트
    """
    if not texts:
        return None

    model = load_model()

    vectors = [model.encode(t) for t in texts if t.strip()]
    if not vectors:
        return None

    return np.mean(vectors, axis=0)


# ---------------------------------------------------------
# 4) 추천 글 계산
# ---------------------------------------------------------
def recommend_articles(user_vector, top_n=5):
    if user_vector is None:
        return []

    article_embeddings, meta = load_aezen_embeddings()

    sims = cosine_similarity([user_vector], article_embeddings)[0]

    top_idx = sims.argsort()[::-1][:top_n]

    results = []
    for i in top_idx:
        results.append({
            "board_no": meta[i]["board_no"],
            "title": meta[i]["title"],
            "url": f"/board/{meta[i]['board_no']}",
            "score": float(sims[i])
        })

    return results
