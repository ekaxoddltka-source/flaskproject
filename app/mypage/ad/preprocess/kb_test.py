import time
import json
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def create_driver():
    options = Options()
    # options.add_argument("--headless=new")
    options.add_argument("--window-size=1400,1000")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


def test_kyobo_page(page=1):
    url = f"https://store.kyobobook.co.kr/bestseller/online/daily/domestic/33?page={page}"
    driver = create_driver()
    driver.get(url)
    time.sleep(3)

    # 레이지 로딩 방지
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    items = driver.find_elements(By.CSS_SELECTOR, "li.mt-9")

    print("아이템 개수:", len(items))

    data = []

    for i, item in enumerate(items, start=1):
        try:
            # -----------------------------
            # 제목 + 상세링크
            # -----------------------------
            title_link = item.find_element(By.CSS_SELECTOR, "div.ml-4 a.prod_link")
            title = title_link.text.strip()
            detail_url = title_link.get_attribute("href")

            # -----------------------------
            # 이미지 (정확한 책 이미지)
            # -----------------------------
            img_tag = item.find_element(
                By.CSS_SELECTOR,
                "div.w-\\[144px\\] img"
            )
            image_url = img_tag.get_attribute("src")

            print(f"[{i}] 제목: {title}")
            print(f"    링크: {detail_url}")
            print(f"    이미지: {image_url}")

            data.append({
                "title": title,
                "url": detail_url,
                "image": image_url
            })

        except Exception as e:
            print("오류:", e)
            continue

    driver.quit()

    path = r"D:\jeong\flaskproject\app\mypage\ad\preprocess\kyobo_test_fixed3.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("저장됨:", path)


if __name__ == "__main__":
    test_kyobo_page(1)
