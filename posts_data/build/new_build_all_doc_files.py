# new_build_all_doc_files.py

import numpy as np
import json

# 1) 임베딩 불러오기
aezen_vecs = np.load("posts_data/aezen_embeddings.npy")
okky_vecs = np.load("posts_data/okky_embeddings.npy")

# 2) 합치기
all_vecs = np.concatenate([aezen_vecs, okky_vecs], axis=0)

# 3) 저장
np.save("posts_data/all_doc_embeddings.npy", all_vecs)
print("all_doc_embeddings.npy 생성 완료! shape =", all_vecs.shape)
