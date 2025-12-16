# recommend/okky_cluster.py

import numpy as np
from sklearn.cluster import KMeans
import joblib  # 모델 저장용


# --------------------------------
# 1) OKKY 임베딩 로드
# --------------------------------
def load_okky_embeddings():
    print("OKKY 임베딩 불러오는 중...")
    embeddings = np.load("okky_embeddings.npy")
    print("임베딩 shape:", embeddings.shape)
    return embeddings


# --------------------------------
# 2) K-Means 클러스터링 실행
# --------------------------------
def train_cluster_model(n_clusters=6):
    embeddings = load_okky_embeddings()

    print(f"{n_clusters}개 클러스터로 학습 시작...")

    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    kmeans.fit(embeddings)

    print("클러스터링 완료!")

    # 모델과 클러스터 중심 저장
    joblib.dump(kmeans, "okky_cluster_model.pkl")
    np.save("okky_cluster_centers.npy", kmeans.cluster_centers_)

    print("💾 모델 저장 완료:")
    print("- okky_cluster_model.pkl")
    print("- okky_cluster_centers.npy")


# --------------------------------
# 실행
# --------------------------------
if __name__ == "__main__":
    train_cluster_model(n_clusters=6)
