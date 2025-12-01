import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

BASE_LIST = "https://okky.kr/questions/tech?page="
BASE_URL = "https://okky.kr"


# ---------------------------------------------------------
# 1) Selenium으로 페이지 로드 → BeautifulSoup 반환
# ---------------------------------------------------------
def get_soup(driver, url):
    driver.get(url)
    time.sleep(2)
    return BeautifulSoup(driver.page_source, "html.parser")


# ---------------------------------------------------------
# 2) 목록 페이지에서 질문 URL 100개 수집
# ---------------------------------------------------------
def get_question_links(driver, max_count=100):
    urls = []
    page = 1

    while len(urls) < max_count:
        print(f"[목록] {page} 페이지 로딩중...")

        soup = get_soup(driver, BASE_LIST + str(page))

        # OKKY 실제 렌더링 기준: 글 링크는 a[href^='/questions/숫자']
        links = soup.select("a[href^='/questions/']")

        if not links:
            print("더 이상 글 없음")
            break

        for a in links:
            href = a.get("href")

            # /questions/숫자 형태만
            if href.count("/") == 2 and href.split("/")[-1].isdigit():
                full = BASE_URL + href
                if full not in urls:
                    urls.append(full)

                if len(urls) >= max_count:
                    break

        page += 1
        time.sleep(1)

    print(f"[완료] 수집된 URL 수: {len(urls)}")
    return urls


# ---------------------------------------------------------
# 3) 각 글 상세 페이지 크롤링
# ---------------------------------------------------------
def parse_question(driver, url):
    print(f"[본문 크롤링] {url}")
    soup = get_soup(driver, url)

    # 제목
    title = soup.select_one("h1")
    title = title.get_text(strip=True) if title else ""

    # 본문 (에디터)
    content_tag = soup.select_one(".remirror-editor")
    content = content_tag.get_text("\n", strip=True) if content_tag else ""

    # 태그
    tag_list = soup.select("a[href^='/questions/tagged/']")
    tags = [t.get_text(strip=True).replace("#", "") for t in tag_list]

    return {
        "url": url,
        "title": title,
        "content": content,
        "tags": ", ".join(tags)
    }


# ---------------------------------------------------------
# 4) 전체 실행 + CSV 저장
# ---------------------------------------------------------
def crawl_okky(max_articles=100):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    urls = get_question_links(driver, max_articles)

    results = []
    for u in urls:
        data = parse_question(driver, u)
        results.append(data)
        time.sleep(1)

    driver.quit()

    df = pd.DataFrame(results)
    df.to_csv("okky_questions.csv", index=False, encoding="utf-8-sig")

    print("\n🎉 크롤링 완료!")
    print("저장파일: okky_questions.csv")


crawl_okky(100)
