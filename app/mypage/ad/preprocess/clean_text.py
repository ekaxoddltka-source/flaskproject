import json
import re
import os

# 전처리 함수
def preprocess_course(course):
    # 1. 타이틀 전처리 (정확한 필드 ad_title 사용)
    raw_title = course.get("ad_title", "").strip()
    title = re.sub(r'\([^)]*\)', '', raw_title)              # 괄호 안 제거
    title = re.sub(r'[^\w가-힣\s\-]', '', title)             # 의미 없는 문자 제거
    title = re.sub(r'\s+', ' ', title)                      # 공백 정리
    clean_title = title.strip()

    # 2. 설명 전처리 (description 그대로)
    raw_desc = course.get("description", "").strip()
    desc = re.sub(r'\n+', ' ', raw_desc)                    # 줄바꿈 제거
    desc = re.sub(r'\d+명 수강생.*?강의!?', '', desc)        # 노이즈 제거
    desc = re.sub(r'[^\w가-힣\s\.,!?]', '', desc)            # 필요한 문자만
    desc = re.sub(r'\s+', ' ', desc)
    clean_desc = desc.strip()

    # 3. URL, 이미지 (절대 건드리지 않음)
    url = course.get("landing_url", "").strip()
    image = course.get("ad_image_url", "").strip()

    # JSON 형태로 반환
    return {
        "ad_title": clean_title,
        "description": clean_desc,
        "url": url,
        "image": image
    }


# JSON 파일 불러오기
folder_path = r"D:\jeong\flaskproject\app\mypage\ad\preprocess"
file_path = os.path.join(folder_path, "inflearn_courses.json")

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 전처리 적용
preprocessed_data = [preprocess_course(course) for course in data]

# 전처리 결과 저장
preprocessed_file_path = os.path.join(folder_path, "inflearn_courses_preprocessed.json")
with open(preprocessed_file_path, "w", encoding="utf-8") as f:
    json.dump(preprocessed_data, f, ensure_ascii=False, indent=4)

print(f"총 {len(preprocessed_data)}개의 강의를 전처리하여 {preprocessed_file_path}에 저장했습니다.")
