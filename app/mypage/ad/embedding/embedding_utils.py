from sentence_transformers import SentenceTransformer

model = SentenceTransformer("jhgan/ko-sroberta-multitask")

def embed_text(text: str):
    if not text:
        return []
    return model.encode(text)
