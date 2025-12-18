import json
from pathlib import Path

# 🔹 기존 수동 키워드 (네가 올린 그대로)
BASE_TECH_KEYWORDS = {
    "python", "java", "javascript", "typescript",
    "spring", "spring boot", "django", "flask", "fastapi",
    "react", "vue", "nextjs",
    "ai", "ml", "deep learning", "nlp", "cv",
    "pytorch", "tensorflow", "bert", "gpt",
    "sql", "mysql", "postgresql", "mongodb",
    "docker", "kubernetes", "aws", "gcp", "azure"
}

# 🔹 자동 확장 키워드 파일
AUTO_KEYWORD_PATH = Path("posts_data/auto_tech_keywords.json")

if AUTO_KEYWORD_PATH.exists():
    with open(AUTO_KEYWORD_PATH, encoding="utf-8") as f:
        AUTO_TECH_KEYWORDS = set(json.load(f))
else:
    AUTO_TECH_KEYWORDS = set()

# 🔥 최종 키워드 (중요)
TECH_KEYWORDS = sorted(
    BASE_TECH_KEYWORDS | AUTO_TECH_KEYWORDS,
    key=len,
    reverse=True
)
