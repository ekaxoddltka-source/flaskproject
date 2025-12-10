from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time, json

def crawl_wanted_jobs(max_scroll=12):
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1600,1000")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    url = "https://www.wanted.co.kr/wdlist?job=developer&country=kr"
    driver.get(url)
    time.sleep(3)

    # ----- 스크롤 다운 -----
    last_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(max_scroll):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2.2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # ----- 공고 추출 -----
    cards = driver.find_elements(By.CSS_SELECTOR, "li.Card_Card__aaatv")
    print("감지된 JobCard 개수:", len(cards))

    ads = []

    for card in cards:
        try:
            # card 안에서 data-cy="job-card" 찾기
            wrapper = card.find_element(By.CSS_SELECTOR, "div[data-cy='job-card']")

            # 상세 URL
            link = wrapper.find_element(By.CSS_SELECTOR, "a").get_attribute("href")

            # 이미지
            img = wrapper.find_element(By.CSS_SELECTOR, "img").get_attribute("src")

            # 제목 (position)
            title = wrapper.find_element(By.CSS_SELECTOR, "span[class*='position']").text

            # 회사명
            company = wrapper.find_element(By.CSS_SELECTOR, "span[class*='company']").text

            ads.append({
                "ad_title": f"{company} {title}",
                "ad_image_url": img,
                "landing_url": link,
                "description": ""
            })

        except Exception as e:
            # debug(원한다면 메시지 출력 가능)
            # print("Error:", e)
            continue

    driver.quit()
    return ads


if __name__ == "__main__":
    data = crawl_wanted_jobs()

    with open("wanted_ads_final.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("총", len(data), "개 크롤링 완료")
