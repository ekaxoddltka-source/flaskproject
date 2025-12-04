import os, json, time, re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def create_driver():
    options = Options()   
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("window-size=1400,1000")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


def crawl_kyobo_bestseller(start_page=1, end_page=41):
    base_url = "https://store.kyobobook.co.kr/bestseller/online/daily/domestic/33?page="
    driver = create_driver()
    books = []

    try:
        for page in range(start_page, end_page + 1):
            print(f"[크롤링 중] 페이지: {page}")
            driver.get(base_url + str(page))
            time.sleep(2)

            items = driver.find_elements(By.CSS_SELECTOR, "li.prod_item")
            for item in items:
                try:
                    # 제목, 상세 URL
                    tag = item.find_element(By.CSS_SELECTOR, ".prod_name a")
                    title = tag.text.strip()
                    url = tag.get_attribute("href")

                    # 이미지
                    image = item.find_element(By.CSS_SELECTOR, ".thumbnail img").get_attribute("src")

                    # 상세페이지로 이동해서 설명 추출
                    driver.execute_script("window.open(arguments[0]);", url)
                    driver.switch_to.window(driver.window_handles[1])
                    time.sleep(1.2)

                    try:
                        desc = driver.find_element(By.CSS_SELECTOR, ".intro_bottom").text
                    except:
                        desc = ""

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                    books.append({
                        "ad_title": title,
                        "ad_image_url": image,
                        "landing_url": url,
                        "description": desc.strip()
                    })

                except Exception as e:
                    print("오류:", e)
                    continue

    finally:
        driver.quit()

    return books


def save_json(data, filename):
    folder = r"D:\jeong\flaskproject\app\mypage\ad\preprocess"
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"{len(data)}개 저장 → {path}")


if __name__ == "__main__":
    data = crawl_kyobo_bestseller(1, 41)
    save_json(data, "kyobo_raw.json")
print("크롤링 완료.")