# posts_data/build_clusters.py

import numpy as np
from sklearn.cluster import KMeans

print("📌 임베딩 로딩...")
embeds = np.load("posts_data/aezen_embeddings_full.npy")

K = 8  # 원하는 클러스터 개수
print(f"📌 {K}개 클러스터링 시작...")

model = KMeans(n_clusters=K, random_state=42)
model.fit(embeds)

np.save("posts_data/cluster_centers.npy", model.cluster_centers_)

print("✅ cluster_centers.npy 저장 완료")
