import json
import re
from collections import Counter
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.filters.tech_translate import KOREAN_TO_ENGLISH
from app.mypage.utils.tech_keywords import TECH_KEYWORDS


class KeywordService:
    _post_vectors = None
    _post_infos = None

    # --------------------------------------------------
    # lazy load (init.py 수정 없음)
    # --------------------------------------------------
    @classmethod
    def _load_posts(cls):
        if cls._post_vectors is None:
            cls._post_vectors = np.load("posts_data/aezen_embeddings.npy")

        if cls._post_infos is None:
            with open("posts_data/aezen_articles.json", encoding="utf-8") as f:
                cls._post_infos = json.load(f)

    # --------------------------------------------------
    # 텍스트 정규화
    # --------------------------------------------------
    @staticmethod
    def _normalize(text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)  
        for kr, en in KOREAN_TO_ENGLISH.items():
            text = text.replace(kr, en)
        return text

    # --------------------------------------------------
    # 본문 기반 키워드 추출
    # --------------------------------------------------
    @classmethod
    def _extract_from_text(cls, text: str):
        text = cls._normalize(text)
        counter = Counter()

        sorted_keywords = sorted(TECH_KEYWORDS, key=len, reverse=True)

        for kw in sorted_keywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            hits = re.findall(pattern, text)
            if hits:
                counter[kw] += len(hits) + (len(kw) * 0.1)

        return counter

    # --------------------------------------------------
    # 유저 벡터 → top_keywords
    # --------------------------------------------------
    @classmethod
    def build_top_keywords(
        cls,
        user_vector,
        top_n_posts=10,
        top_n_keywords=5
    ):
        if user_vector is None:
            return None

        cls._load_posts()

        user_vec = np.asarray(user_vector, dtype=float).reshape(1, -1)

        if user_vec.shape[1] != cls._post_vectors.shape[1]:
            return None

        sims = cosine_similarity(user_vec, cls._post_vectors)[0]
        top_idx = sims.argsort()[-top_n_posts:][::-1]

        total_counter = Counter()

        for i in top_idx:
            post = cls._post_infos[i]
            text = f"{post.get('title','')} {post.get('content','')}"
            total_counter += cls._extract_from_text(text)

        if not total_counter:
            return None

        keywords = [
            kw for kw, _ in total_counter.most_common(top_n_keywords)
        ]

        return ",".join(keywords)


    @staticmethod
    def extract_keywords_from_post(title, content, tags):
        text = f"{title} {content} {' '.join(tags or [])}".lower()

        counter = Counter()
        for kw in TECH_KEYWORDS:
            if kw in text:
                counter[kw] += 1

        return counter
