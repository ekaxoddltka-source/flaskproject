# posts_data/build_topic_labels.py

import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT

print("📌 파일 로딩...")
articles = json.load(open("posts_data/aezen_articles_full.json", encoding="utf-8"))
doc_vectors = np.load("posts_data/aezen_embeddings_full.npy")
cluster_centers = np.load("posts_data/cluster_centers.npy")

texts = [f"{a['title']} {a['content']}" for a in articles]

bert = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
kw_model = KeyBERT(model=bert)

topic_labels = []

print("📌 자동 라벨 생성중...")
for center in cluster_centers:
    sims = cosine_similarity([center], doc_vectors)[0]
    top_idx = sims.argsort()[-5:][::-1]

    merged_text = " ".join(texts[i] for i in top_idx)
    keywords = kw_model.extract_keywords(merged_text, top_n=3)

    if keywords:
        label = " / ".join(k[0] for k in keywords)
    else:
        label = "Topic"

    topic_labels.append(label)

with open("posts_data/topic_labels.json", "w", encoding="utf-8") as f:
    json.dump(topic_labels, f, ensure_ascii=False, indent=2)

print("✅ topic_labels.json 저장 완료")
print(topic_labels)
