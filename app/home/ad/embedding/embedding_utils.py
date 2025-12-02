import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer

# -------------------------------------------------------------
# SBERT 모델 로드 (한글 + 영어)
# -------------------------------------------------------------
sbert_model = SentenceTransformer("jhgan/ko-sroberta-multitask")

# -------------------------------------------------------------
# JSON 파일 불러오기
# -------------------------------------------------------------
input_file = r"D:\jwh\flaskproject\app\home\ad\embedding\keywords_tfidf_uppercase_safe.json"
with open(input_file, "r", encoding="utf-8") as f:
    ad_data = json.load(f)

# 저장 경로
save_path = r"D:\jwh\flaskproject\app\home\ad\embedding"
os.makedirs(save_path, exist_ok=True)
output_file = os.path.join(save_path, "keywords_embeddings.json")

# -------------------------------------------------------------
# 키워드 임베딩 함수
# -------------------------------------------------------------
def embed_keywords(keywords_list):
    """
    키워드 리스트를 SBERT 벡터로 변환
    """
    if not keywords_list:
        return []
    embeddings = sbert_model.encode(keywords_list)
    # numpy array → list로 변환 (JSON 저장용)
    return embeddings.tolist()

# -------------------------------------------------------------
# 광고별 임베딩 생성
# -------------------------------------------------------------
all_embedded = []

for idx, ad in enumerate(ad_data):
    if idx % 20 == 0:
        print(f"{idx}/{len(ad_data)} 처리 중...")

    keywords = ad.get("keywords", [])
    embeddings = embed_keywords(keywords)

    all_embedded.append({
        "ad_title": ad.get("ad_title", ""),
        "keywords": keywords,
        "embeddings": embeddings  # 키워드별 임베딩
    })

# -------------------------------------------------------------
# 결과 저장
# -------------------------------------------------------------
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_embedded, f, ensure_ascii=False, indent=4)

print(f"모든 광고 키워드 임베딩을 {output_file} 에 저장했습니다.")
