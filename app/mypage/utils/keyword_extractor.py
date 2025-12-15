# app/mypage/utils/keyword_extractor.py

import re
from collections import Counter

# 이미 routes.py 에 있는 TECH_KEYWORDS 그대로 사용 가능
from app.mypage.routes import TECH_KEYWORDS
from app.filters.tech_translate import KOREAN_TO_ENGLISH


def normalize_text(text: str) -> str:
    """한글 기술명 → 영어 + 소문자"""
    if not text:
        return ""

    text = text.lower()
    for kr, en in KOREAN_TO_ENGLISH.items():
        text = text.replace(kr, en)
    return text


def extract_keywords_from_text(text: str, top_n=5):
    """
    게시글 본문에서 기술 키워드 추출
    """
    text = normalize_text(text)

    sorted_keywords = sorted(TECH_KEYWORDS, key=len, reverse=True)
    counter = Counter()

    for kw in sorted_keywords:
        pattern = r"\b" + re.escape(kw) + r"\b"
        matches = re.findall(pattern, text)
        if matches:
            # 길이 가중치 → react native > react
            counter[kw] += len(matches) + (len(kw) * 0.1)

    return [kw for kw, _ in counter.most_common(top_n)]
