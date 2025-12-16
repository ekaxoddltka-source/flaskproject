# posts_data/cluster_builder.py
import numpy as np
from sklearn.cluster import KMeans

# -----------------------------
# 1) 임베딩 로드
# -----------------------------
aezen = np.load("posts_data/aezen_embeddings.npy")
okky = np.load("posts_data/okky_embeddings.npy")

print("AEZEN:", aezen.shape)
print("OKKY:", okky.shape)

# -----------------------------
# 2) 전체 병합
# -----------------------------
all_embeddings = np.vstack([aezen, okky])
print("TOTAL:", all_embeddings.shape)

# -----------------------------
# 3) KMeans 클러스터 생성
# -----------------------------
NUM_CLUSTERS = 5  # Radar Chart용 (5개가 안정적이고 시각적으로 적당)

kmeans = KMeans(
    n_clusters=NUM_CLUSTERS,
    random_state=42,
    n_init=10
)
kmeans.fit(all_embeddings)

cluster_centers = kmeans.cluster_centers_
print("Cluster centers shape:", cluster_centers.shape)

# -----------------------------
# 4) 저장
# -----------------------------
np.save("posts_data/cluster_centers.npy", cluster_centers)

print("✔ cluster_centers.npy 생성 완료!")
