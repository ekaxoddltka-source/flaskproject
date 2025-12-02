# app/home/chat_recommend/recommender.py
from .db import get_top_posts_last_3_days
from .keywords import extract_keywords_from_posts

def build_chat_topic(app, limit=10, keyword_top_n=5):
    """
    최근 3일 게시글 TOP10을 조회하고,
    제목+내용에서 키워드 추출 후 대화 주제 문장 생성
    """
    # 1) DB에서 TOP 게시글 가져오기
    posts = get_top_posts_last_3_days(app, limit=limit)
    print(f"[DEBUG] get_top_posts_last_3_days returned {len(posts)} posts")  # 🔥
    if not posts:
        return None, []

    # 2) 키워드 추출
    keywords_data = extract_keywords_from_posts(posts, top_n=keyword_top_n)

    # 3) 키워드 통합 (중복 제거)
    all_keywords = set()
    for k in keywords_data:
        all_keywords.update(k['keywords'])

    if not all_keywords:
        topic_text = "최근 인기 게시글을 분석했지만 유의미한 키워드를 찾지 못했습니다."
    else:
        topic_text = "오늘의 대화 주제 후보: " + ", ".join(list(all_keywords))

    print(f"[DEBUG] topic_text generated: {topic_text}")  # 🔥

    return topic_text, list(all_keywords)
