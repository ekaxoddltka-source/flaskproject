# app/mypage/recommend/okky_recommender.py

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ------------------------------
# ① CSV & 임베딩 로딩 (서버 시작 시 1번)
# ------------------------------
OKKY_DF = pd.read_csv("okky_questions.csv")
OKKY_EMB = np.load("okky_embeddings.npy")

MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


# ------------------------------
# ② 추천 함수
# ------------------------------
def recommend_okky_articles(user_keywords, top_k=5):
    if not user_keywords:
        return []

    # 유저 관심을 하나의 문장으로
    user_text = " ".join(user_keywords)

    # 임베딩 생성
    user_vec = MODEL.encode(user_text).reshape(1, -1)

    # 모든 OKKY 글과 유사도 계산
    scores = cosine_similarity(user_vec, OKKY_EMB)[0]

    # 상위 5개 index
    best_idx = scores.argsort()[::-1][:top_k]

    results = []
    for idx in best_idx:
        results.append({
            "title": OKKY_DF.iloc[idx]["title"],
            "url": OKKY_DF.iloc[idx]["url"]
        })

    return results
