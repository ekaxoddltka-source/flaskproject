import re

def clean_text(text: str) -> str:
    if not text:
        return ""

    # 문자열 변환 및 공백 정리
    text = str(text).strip()

    # 이모지 제거
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F700-\U0001F77F"
        u"\U0001F780-\U0001F7FF"
        u"\U0001F800-\U0001F8FF"
        u"\U0001F900-\U0001F9FF"
        u"\U0001FA00-\U0001FA6F"
        u"\U0001FA70-\U0001FAFF"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(" ", text)

    # 괄호 제거
    text = re.sub(r"\([^)]*\)", " ", text)

    # 특수문자 제거 (기술명 형태는 최대한 유지)
    text = re.sub(r"[^\w가-힣\s\-]", " ", text)

    # 중복 공백 제거
    text = re.sub(r"\s+", " ", text).strip()

    return text
