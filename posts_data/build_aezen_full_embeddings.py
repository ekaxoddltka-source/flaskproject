# posts_data/build_aezen_full_embeddings.py

import json
import numpy as np
from sentence_transformers import SentenceTransformer

print("📌 JSON 로딩...")
with open("posts_data/aezen_articles_full.json", encoding="utf-8") as f:
    data = json.load(f)

print("📌 BERT 모델 로딩...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

texts = [f"{d['title']} {d['content']}" for d in data]

print("📌 임베딩 생성중... (시간 조금 걸림)")
embeds = model.encode(texts, show_progress_bar=True)

np.save("posts_data/aezen_embeddings_full.npy", embeds)
print("✅ aezen_embeddings_full.npy 저장 완료")
