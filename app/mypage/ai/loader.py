import numpy as np
import pandas as pd

# 1) OKKY 글 CSV 로드
okky_df = pd.read_csv("okky_questions.csv")

# 2) 임베딩 로드
okky_embeddings = np.load("okky_embeddings.npy")

print("OKKY 글 개수:", len(okky_df))
print("임베딩 shape:", okky_embeddings.shape)
