# app/filters/slang_filter.py
import re

_slang_words = []
_pattern = None


def load_slang_terms_from_db(app):
    """
    DB에서 core 욕설 문자열만 불러오는 원래 버전(rollback 버전).
    """
    global _slang_words, _pattern

    conn = app.get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT slang_word FROM slang_words")
            rows = cursor.fetchall()
    finally:
        conn.close()

    # 단일 문자열 리스트
    _slang_words = [
        row["slang_word"].strip()
        for row in rows
        if row["slang_word"] and row["slang_word"].strip()
    ]

    if not _slang_words:
        _pattern = None
        print("[SLANG FILTER] No slang words loaded.")
        return

    # 정규식: 긴 단어 먼저
    escaped = [re.escape(w) for w in _slang_words]
    escaped.sort(key=len, reverse=True)

    pattern = "(" + "|".join(escaped) + ")"
    _pattern = re.compile(pattern, re.IGNORECASE)

    print(f"[SLANG FILTER] Loaded {len(_slang_words)} slang words.")


def is_boundary(c):
    """
    단어 경계 체크 — 한글/영문/숫자 아닌 경우 '경계'로 간주
    """
    if not c:
        return True
    return not (c.isalnum() or ('가' <= c <= '힣'))


def mask_slang(text: str) -> str:
    """
    욕설을 *로 마스킹하되, 오탐 방지를 위한 기본 경계 로직 포함.
    prefix/suffix 로직 없음 — rollback 버전
    """
    if not text or not _pattern:
        return text

    def replacer(match):
        word = match.group(0)
        start, end = match.span()

        before = text[start - 1] if start > 0 else ""
        after = text[end] if end < len(text) else ""

        # 오탐 방지 — 년도가 "10년", "30년"인 경우 등 경계 체크
        if not is_boundary(before) and not is_boundary(after):
            return word  # 그대로 둔다 (오탐 방지)

        return "*" * len(word)

    return _pattern.sub(replacer, text)
