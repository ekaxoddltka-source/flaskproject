# posts_data/aezen_embed.py
import pymysql
import json
import numpy as np
import re
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

# -------------------------------------------------
# DB 연결 (app/__init__.py 설정과 동일하게)
# -------------------------------------------------
def get_conn():
    return pymysql.connect(
        host="192.168.60.136",
        user="jwh",
        password="ezen",
        db="aezen",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10
    )

# -------------------------------------------------
# 게시글 + 태그 로드
# -------------------------------------------------
def load_aezen_articles():
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        SELECT 
            b.board_no,
            b.board_title,
            b.board_content,
            GROUP_CONCAT(t.tag_name SEPARATOR ', ') AS tags
        FROM board b
        LEFT JOIN tag_board tb ON b.board_no = tb.board_no
        LEFT JOIN tag t ON tb.tag_no = t.tag_no
        WHERE b.board_deleted = 0
        GROUP BY b.board_no
        ORDER BY b.board_no DESC
    """

    cur.execute(sql)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    print(f"총 게시글 수: {len(rows)}")
    return rows

# -------------------------------------------------
# 텍스트 정규화
# -------------------------------------------------
def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9가-힣\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# -------------------------------------------------
# TF-IDF 기반 키워드 추출
# -------------------------------------------------
def extract_keywords(texts, top_k=5):
    if not texts:
        return []

    vectorizer = TfidfVectorizer(
        max_df=0.9,
        min_df=2,
        max_features=3000,
        ngram_range=(1, 2)
    )

    tfidf = vectorizer.fit_transform(texts)
    feature_names = np.array(vectorizer.get_feature_names_out())

    keywords_per_doc = []

    for row in tfidf:
        if row.nnz == 0:
            keywords_per_doc.append([])
            continue

        scores = row.toarray()[0]
        top_idx = scores.argsort()[-top_k:][::-1]
        kws = feature_names[top_idx].tolist()
        keywords_per_doc.append(kws)

    return keywords_per_doc

# -------------------------------------------------
# Sentence-BERT 로딩
# -------------------------------------------------
def load_model():
    print("Sentence-BERT 모델 로딩 중...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print("모델 로딩 완료")
    return model

# -------------------------------------------------
# 임베딩 + JSON 생성
# -------------------------------------------------
def create_embeddings():
    articles = load_aezen_articles()
    model = load_model()

    texts_for_tfidf = []
    embed_texts = []

    for art in articles:
        text = f"{art['board_title']} {art['board_content']}"
        norm = normalize_text(text)
        texts_for_tfidf.append(norm)
        embed_texts.append(text)

    print("키워드 추출 중 (TF-IDF)...")
    keywords_list = extract_keywords(texts_for_tfidf, top_k=5)

    embeddings = []
    meta_infos = []

    print("임베딩 생성 중...")
    for idx, art in enumerate(articles):
        vec = model.encode(embed_texts[idx])
        embeddings.append(vec)

        meta_infos.append({
            "board_no": art["board_no"],
            "title": art["board_title"],
            "content": art["board_content"],
            "keywords": keywords_list[idx]
        })

        if (idx + 1) % 20 == 0:
            print(f"{idx+1}/{len(articles)} 완료")

    embeddings = np.array(embeddings)

    np.save("posts_data/aezen_embeddings.npy", embeddings)
    with open("posts_data/aezen_articles.json", "w", encoding="utf-8") as f:
        json.dump(meta_infos, f, ensure_ascii=False, indent=2)

    print("\n=== 완료 ===")
    print("✔ aezen_embeddings.npy")
    print("✔ aezen_articles.json")
    print("임베딩 shape:", embeddings.shape)

# -------------------------------------------------
# 실행
# -------------------------------------------------
if __name__ == "__main__":
    create_embeddings()
