# app/mypage/utils/keyword_extractor.py

import re
from collections import Counter

# 이미 routes.py 에 있는 TECH_KEYWORDS 그대로 사용 가능
from app.mypage.utils.tech_keywords import TECH_KEYWORDS
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
    from collections import Counter
    import re
    from app.filters.tech_translate import KOREAN_TO_ENGLISH

    if not text:
        return []

    text = text.lower()

    # 한글 → 영어
    for kr, en in KOREAN_TO_ENGLISH.items():
        text = text.replace(kr, en)

    # 특수문자 정리
    text = re.sub(r"[^a-z0-9\s\+\#\-]", " ", text)

    counter = Counter()

    for kw in TECH_KEYWORDS:
        count = text.count(kw)
        if count:
            counter[kw] += count + (len(kw) * 0.1)

    return [kw for kw, _ in counter.most_common(top_n)]
