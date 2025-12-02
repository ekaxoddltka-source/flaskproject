import json
import re
import os

# 전처리 함수
def preprocess_course(course):
    # 1. 타이틀 전처리
    title = course.get('ad_title', '').strip()
    # 괄호, 특수문자, 불필요한 공백 제거
    title = re.sub(r'\([^)]*\)', '', title)  # 괄호 안 내용 제거
    title = re.sub(r'[^\w가-힣\s\-]', '', title)  # 한글, 영어, 숫자, 공백, - 제외 제거
    title = re.sub(r'\s+', ' ', title)  # 연속 공백 -> 단일 공백
    course['ad_title'] = title.strip()

    # 2. 설명 전처리
    desc = course.get('description', '').strip()
    desc = re.sub(r'\n+', ' ', desc)  # 줄바꿈 제거
    desc = re.sub(r'\d+명 수강생.*?강의!?', '', desc)  # 수강생 문구 제거
    desc = re.sub(r'[^\w가-힣\s\.,!?]', '', desc)  # 의미 있는 특수문자만 남김
    desc = re.sub(r'\s+', ' ', desc)  # 연속 공백 -> 단일 공백
    course['description'] = desc.strip()

    return course

# JSON 파일 불러오기
folder_path = r"D:\jwh\flaskproject\app\home\ad\preprocess"
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