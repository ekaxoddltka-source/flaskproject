from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np

# ------------------------------------
# 1) CSV 파일 불러오기
# ------------------------------------
df = pd.read_csv("okky_questions.csv")

print("CSV 로딩 완료!")
print("총 글 수 :", len(df))


# ------------------------------------
# 2) BERT 임베딩 모델 불러오기
# ------------------------------------
print("BERT 모델 로딩중... (약 3초)")

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

print("모델 로딩 완료!")


# ------------------------------------
# 3) 글마다 임베딩 벡터 생성
# ------------------------------------
embeddings = []

print("임베딩 생성 시작...")

for idx, row in df.iterrows():
    # 하나의 텍스트로 합치기
    text = f"{row['title']} {row['content']} tags: {row['tags']}"

    vector = model.encode(text)
    embeddings.append(vector)

    # 진행 상황 출력
    if (idx + 1) % 10 == 0:
        print(f"{idx+1} / {len(df)} 완료")

# numpy 배열로 변환
embeddings = np.array(embeddings)


# ------------------------------------
# 4) 임베딩 파일 저장
# ------------------------------------
np.save("okky_embeddings.npy", embeddings)

print("\n임베딩 생성 완료!")
print("저장 파일: okky_embeddings.npy")
print("임베딩 shape:", embeddings.shape)
