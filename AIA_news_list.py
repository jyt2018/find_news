# author: jyt2018@github
# date: 2023-10-10
# 该脚本用于抓取www.aia-aerospace.org/news，并将结果保存到本地文件
# 使用Selenium模拟浏览器操作，BeautifulSoup解析HTML，并支持多线程抓取
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import threading
import lib_findbook as fb
def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    service = Service()  # 替换为实际的chromedriver路径
    return webdriver.Chrome(service=service, options=options)

def process_page(page):
    driver = init_driver()
    try:
        url = f"https://www.aia-aerospace.org/news/page/{page}/"
        print(f"Processing URL: {url}")
        driver.get(url)
        
        # 动态等待页面加载完成
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "posts-sidebar-wrap"))
        )
        
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, "html.parser")
        feature_container = soup.find("div", class_="posts-sidebar-wrap")
        
        if feature_container:
            links = feature_container.find_all("div", class_="post-copy")
            with lock:  # 使用线程锁确保文件写入的原子性
                with open("AIA_2025.txt", "a", encoding="utf-8") as file:
                    for link in links:
                        title = fb.clean_unicode(link.find("a").text.strip())
                        href = link.find("a")["href"].strip()
                        date = link.find("span", class_="post-date").text.strip()
                        print(f"{date} - {title} - {href}")
                        file.write(f"{date}|{title}|{href}\n")
        else:
            print("No feature-template-container found on this page.")
    except Exception as e:
        print(f"Error processing page {page}: {e}")
    finally:
        driver.quit()

def main():
    global lock
    lock = threading.Lock()
    
    start_page = 1
    end_page = 3  # include this page
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_page, page) for page in range(start_page, end_page + 1)]
        for future in futures:
            future.result()  # 等待所有任务完成
    
    print("All done! Href values have been saved to txt")

if __name__ == "__main__":
    main()