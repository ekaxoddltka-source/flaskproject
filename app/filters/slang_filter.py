# app/filters/slang_filter.py
import re

_slang_words = []
_pattern = None
# 자음 욕설 패턴 (공백/특수문자 우회 대응)
_CONSONANT_SLANG_PATTERN = re.compile(
    r'(^|[ \t\n\r.,!?])'        # 공백 or 문장부호만
    r'(?:'
    r'[ㅅㅆ]\s*ㅂ|'             # ㅅㅂ, ㅆㅂ
    r'ㅂ\s*ㅅ|'                 # ㅂㅅ
    r'ㅄ|'                      # ㅄ
    r'ㅈ\s*ㄹ|'                 # ㅈㄹ
    r'ㅅ\s*ㄲ'                  # ㅅㄲ
    r')'
    r'(?=$|[ \t\n\r.,!?])'
)



def has_consonant_slang(text: str) -> bool:
    return bool(_CONSONANT_SLANG_PATTERN.search(text))

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
    1차: DB 기반 욕설 마스킹 (기존 로직)
    2차: 자음 욕설 패턴 마스킹
    """
    if not text:
        return text

    original_text = text

    # ---------- 1차: DB 욕설 ----------
    if _pattern:
        def replacer(match):
            word = match.group(0)
            start, end = match.span()

            before = original_text[start - 1] if start > 0 else ""
            after = original_text[end] if end < len(original_text) else ""

            if not is_boundary(before) and not is_boundary(after):
                return word  # 오탐 방지

            return "*" * len(word)

        text = _pattern.sub(replacer, text)
   
    # ---------- 2차: 자음 욕설 ----------
    if _CONSONANT_SLANG_PATTERN.search(text):
        return "***"


    return text
