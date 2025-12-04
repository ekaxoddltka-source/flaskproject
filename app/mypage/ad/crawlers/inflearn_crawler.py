from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time, json, os

def crawl_inflearn_courses():
    """
    인프런 'IT 프로그래밍' 강의 페이지 크롤링
    필요한 데이터: ad_title, ad_image_url, landing_url, description
    """
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    courses = []

    try:
        for page in range(1, 63):  # 1~62페이지
            url = f"https://www.inflearn.com/courses/it-programming?page_number={page}"
            driver.get(url)
            time.sleep(3)  # 페이지 렌더링 대기

            course_items = driver.find_elements(By.CSS_SELECTOR, "li.css-8atqhb")

            for item in course_items:
                try:
                    link_tag = item.find_element(By.TAG_NAME, "a")
                    landing_url = link_tag.get_attribute("href")

                    title_tag = item.find_element(By.CSS_SELECTOR, "p.css-10bh5qj")
                    ad_title = title_tag.text if title_tag else ""

                    img_tag = item.find_element(By.CSS_SELECTOR, "img")
                    ad_image_url = img_tag.get_attribute("src") if img_tag else ""

                    try:
                        desc_container = item.find_element(By.CSS_SELECTOR,
                            "article.mantine-Card-root > div:nth-child(2) > div:nth-child(3) > div:nth-child(1) > p")
                        description = desc_container.get_attribute("textContent")
                    except:
                        description = ""  # description이 없으면 빈 문자열

                    courses.append({
                        "ad_title": ad_title,
                        "ad_image_url": ad_image_url,
                        "landing_url": landing_url,
                        "description": description
                    })
                except Exception as e:
                    print("Error:", e)
                    continue
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"\n총 {len(data)}개의 강의 데이터를 {file_path}에 저장했습니다.")        
    finally:
        driver.quit()

    return courses

# 테스트
if __name__ == "__main__":
    data = crawl_inflearn_courses()

# 저장할 폴더 경로
folder_path = r"D:\jwh\flaskproject\app\home\ad\preprocess"

# 폴더가 없으면 생성
os.makedirs(folder_path, exist_ok=True)

# 파일 경로
file_path = os.path.join(folder_path, "inflearn_courses.json")

