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
    _all_keywords = None   # 🔥 병합 키워드 캐시

    # --------------------------------------------------
    # lazy load (post vectors / articles)
    # --------------------------------------------------
    @classmethod
    def _load_posts(cls):
        if cls._post_vectors is None:
            cls._post_vectors = np.load("posts_data/aezen_embeddings.npy")

        if cls._post_infos is None:
            with open("posts_data/aezen_articles.json", encoding="utf-8") as f:
                cls._post_infos = json.load(f)

    # --------------------------------------------------
    # 🔥 TECH_KEYWORDS + auto_tech_keywords.json 병합
    # --------------------------------------------------
    @classmethod
    def _load_all_keywords(cls):
        if cls._all_keywords is not None:
            return cls._all_keywords

        keywords = set(TECH_KEYWORDS)

        try:
            with open("posts_data/auto_tech_keywords.json", encoding="utf-8") as f:
                auto_keywords = json.load(f)
                keywords.update(auto_keywords)
        except FileNotFoundError:
            # 자동 키워드 파일 없으면 기존 키워드만 사용
            pass

        cls._all_keywords = keywords
        return cls._all_keywords

    # --------------------------------------------------
    # 텍스트 정규화
    # --------------------------------------------------
    @staticmethod
    def _normalize(text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"[^a-z0-9가-힣\s\+\#\-]", " ", text)
        for kr, en in KOREAN_TO_ENGLISH.items():
            text = text.replace(kr, en)
        return text

    # --------------------------------------------------
    # 🔥 본문 기반 키워드 추출 (자동 확장 포함)
    # --------------------------------------------------
    @classmethod
    def _extract_from_text(cls, text: str):
        if not text:
            return Counter()

        text = cls._normalize(text)
        counter = Counter()

        all_keywords = cls._load_all_keywords()

        # 길이 긴 키워드 우선 (react native > react)
        sorted_keywords = sorted(all_keywords, key=len, reverse=True)

        for kw in sorted_keywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            hits = re.findall(pattern, text)
            if hits:
                counter[kw] += len(hits) + (len(kw) * 0.2)

        return counter

    # --------------------------------------------------
    # 유저 벡터 → top keywords
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

    # --------------------------------------------------
    # 단일 게시글 키워드 추출 (태그 포함)
    # --------------------------------------------------
    @classmethod
    def extract_keywords_from_post(cls, title, content, tags):
        text = f"{title} {content} {' '.join(tags or [])}"
        return cls._extract_from_text(text)
