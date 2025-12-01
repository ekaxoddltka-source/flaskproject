# recommend/aezen_embed.py

import pymysql
import json
import numpy as np
from sentence_transformers import SentenceTransformer


# -----------------------------------------
# 1) DB 연결 함수 (너의 init.py 구조 그대로 반영)
# -----------------------------------------
def get_conn():
    return pymysql.connect(
        host="192.168.60.187",
        user="jwh",
        password="ezen",
        db="aezen",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )


# -----------------------------------------
# 2) DB에서 게시글 + 태그 가져오기
# -----------------------------------------
def load_aezen_articles():
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        SELECT b.board_no, b.board_title, b.board_content,
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

    print("총 게시글:", len(rows))
    return rows


# -----------------------------------------
# 3) Sentence-BERT 로딩
# -----------------------------------------
def load_model():
    print("BERT 모델 로딩 중...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print("모델 로딩 완료")
    return model


# -----------------------------------------
# 4) 게시글 임베딩 생성
# -----------------------------------------
def create_embeddings():
    articles = load_aezen_articles()
    model = load_model()

    embeddings = []
    meta_info = []  # board_no, title 저장

    print("\n임베딩 생성 시작...\n")

    for idx, art in enumerate(articles):
        text = f"{art['board_title']} {art['board_content']} tags: {art.get('tags','')}"
        vector = model.encode(text)

        embeddings.append(vector)
        meta_info.append({
            "board_no": art["board_no"],
            "title": art["board_title"]
        })

        if (idx + 1) % 20 == 0:
            print(f"{idx+1} / {len(articles)} 완료")

    embeddings = np.array(embeddings)

    # 저장
    np.save("aezen_embeddings.npy", embeddings)
    with open("aezen_articles.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)

    print("\n=== 저장 완료 ===")
    print("aezen_embeddings.npy")
    print("aezen_articles.json")
    print("임베딩 shape:", embeddings.shape)


# -----------------------------------------
# 실행
# -----------------------------------------
if __name__ == "__main__":
    create_embeddings()
