import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

TECH_CATEGORY = {
    "Frontend": ["react", "vue", "javascript", "typescript", "nextjs", "svelte"],
    "Backend": ["python", "java", "spring", "django", "fastapi", "flask", "node"],
    "AI/ML": ["ai", "machine learning", "pytorch", "tensorflow", "deep learning"],
    "Database": ["mysql", "oracle", "postgres", "mongodb", "sql"],
    "DevOps": ["docker", "kubernetes", "aws", "gcp", "azure", "k8s"],
}

category_vectors = {}

for cat, words in TECH_CATEGORY.items():
    vecs = model.encode(words)
    category_vectors[cat] = np.mean(vecs, axis=0)

np.save("posts_data/category_vectors.npy", category_vectors)
print("Saved:", list(category_vectors.keys()))
