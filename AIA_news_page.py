import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import lib_findbook as fb

def read_urls_from_file(file_path):
    """
    从文件中读取URL列表
    """
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    # 去除每行的空白字符，并取第[-1]项作为URL
    list_urls = [line.strip().split("|")[-1] for line in lines]
    return list_urls

def fetch_and_parse_url(url):
    """
    访问URL，解析响应，并提取标题和内容
    """
    try:
        # 发送HTTP请求
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        # 使用BeautifulSoup解析响应内容
        soup = BeautifulSoup(response.text, "html.parser")
        # 查找<h1 class='pg-title'>标签
        title_tag = soup.find("h1", class_="pg-title")
        if title_tag:
            dates = "[date:]" + title_tag.find("span").text.strip() + "\n"  # 提取标题中的日期
            title_tag.span.decompose()  # 删除标题中的日期
            return_txt = "[title:]" + fb.clean_unicode(title_tag.text.strip()) + "\n" + dates  # 返回标题文本
            txtcontent = soup.find("div", class_="post")  # 查找文章内容
            if txtcontent:
                return_txt += "[content:]" + txtcontent.text.strip().replace("###", "")  # 返回文章内容
            return return_txt
        else:
            return None  # 如果未找到标题，返回None
    except Exception as e:
        print(f"访问URL {url} 时出错: {e}")
        return None

def process_url(url):
    """
    处理单个URL，并返回结果
    """
    print(f"正在处理URL: {url}")
    result = fetch_and_parse_url(url)
    if result:
        print(f"标题: {result[:30]}")  # 打印前30个字符作为标题摘要
        return result
    else:
        print("未找到标题")
        return None

def main():
    # 文件路径
    file_path = r"E:\project\find_news\AIA_before2025.txt"
    # 读取URL列表
    list_urls = read_urls_from_file(file_path)
    # 使用ThreadPoolExecutor进行多线程处理
    with ThreadPoolExecutor(max_workers=10) as executor:  # 设置最大线程数为10
        futures = {executor.submit(process_url, url): url for url in list_urls}
        # 将结果写入文件
        with open("AIA_before2025news.txt", "a", encoding="utf-8") as file:
            for future in as_completed(futures):
                url = futures[future]
                try:
                    result = future.result()
                    if result:
                        file.write(result + "\n")
                except Exception as e:
                    print(f"处理URL {url} 时出错: {e}")

# 调用主函数
if __name__ == "__main__":
    main()