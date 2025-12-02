# recommend/aezen_recommender.py

import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT

# ---------------------------------------------------------
# Lazy Loading
# ---------------------------------------------------------
MODEL = None
ARTICLE_EMBEDDINGS = None
ARTICLE_META = None

TOPIC_LABELS = None   # ← 라벨도 lazy 로딩
KW_MODEL = None       # KeyBERT 모델 캐싱


# ---------------------------------------------------------
# 1) BERT 모델 로드
# ---------------------------------------------------------
def load_model():
    global MODEL
    if MODEL is None:
        print("🔥 BERT 모델 최초 로딩 중... (약 4~7초)")
        MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return MODEL


# ---------------------------------------------------------
# 2) AEZEN 게시글 임베딩 로딩
# ---------------------------------------------------------
def load_aezen_embeddings():
    global ARTICLE_EMBEDDINGS, ARTICLE_META
    if ARTICLE_EMBEDDINGS is None:
        print("🔥 게시글 임베딩 최초 로딩 중...")

        ARTICLE_EMBEDDINGS = np.load("posts_data/aezen_embeddings.npy")

        with open("posts_data/aezen_articles.json", "r", encoding="utf-8") as f:
            ARTICLE_META = json.load(f)

    return ARTICLE_EMBEDDINGS, ARTICLE_META


# ---------------------------------------------------------
# 3) 사용자 벡터 생성
# ---------------------------------------------------------
def build_user_vector(texts):
    if not texts:
        return None

    model = load_model()

    vectors = [model.encode(t) for t in texts if t.strip()]
    if not vectors:
        return None

    return np.mean(vectors, axis=0)


# ---------------------------------------------------------
# 4) AEZEN 추천 계산
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


# ---------------------------------------------------------
# 5) KeyBERT 라벨링 (Lazy)
# ---------------------------------------------------------
def auto_label_topics():
    """서버 시작 시 자동 실행 금지. 필요할 때만 1번 실행."""
    global TOPIC_LABELS, KW_MODEL

    if TOPIC_LABELS is not None:
        return TOPIC_LABELS

    print("🔥 Topic labels FIRST-TIME generating...")

    # KeyBERT 모델 1회만 로드
    if KW_MODEL is None:
        KW_MODEL = KeyBERT("sentence-transformers/all-MiniLM-L6-v2")

    cluster_centers = np.load("posts_data/cluster_centers.npy")
    doc_vectors = np.load("posts_data/all_doc_embeddings.npy")

    with open("posts_data/all_doc_texts.json", "r", encoding="utf-8") as f:
        doc_texts = json.load(f)

    labels = []
    for center in cluster_centers:
        sims = cosine_similarity([center], doc_vectors)[0]
        top_idx = sims.argsort()[-5:][::-1]
        candidate_text = " ".join([doc_texts[i] for i in top_idx])

        keywords = KW_MODEL.extract_keywords(candidate_text, top_n=3)

        if keywords:
            label = " / ".join([kw[0] for kw in keywords])
        else:
            label = "Topic"

        labels.append(label)

    TOPIC_LABELS = labels
    print("🔥 Topic labels generated:", TOPIC_LABELS)
    return TOPIC_LABELS
