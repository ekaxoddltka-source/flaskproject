import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class PostRecommender:
    _post_vectors = None
    _post_infos = None

    # ---------------------------------
    # lazy load (요청 최초 1회)
    # ---------------------------------
    @classmethod
    def _load_data(cls):
        if cls._post_vectors is None:
            cls._post_vectors = np.load("posts_data/aezen_embeddings.npy")

        if cls._post_infos is None:
            with open("posts_data/aezen_articles.json", encoding="utf-8") as f:
                cls._post_infos = json.load(f)

    # ---------------------------------
    # 추천
    # ---------------------------------
    @classmethod
    def recommend(cls, user_vector, top_n=5):
        if user_vector is None:
            return []

        cls._load_data()

        user_vec = np.asarray(user_vector, dtype=float).reshape(1, -1)

        if user_vec.shape[1] != cls._post_vectors.shape[1]:
            return []

        sims = cosine_similarity(user_vec, cls._post_vectors)[0]
        top_idx = sims.argsort()[-top_n:][::-1]

        results = []
        for i in top_idx:
            post = cls._post_infos[i]
            results.append({
                "board_no": post.get("board_no"),
                "title": post.get("title"),
                "content": post.get("content"),
                "score": float(sims[i])
            })

        return results
