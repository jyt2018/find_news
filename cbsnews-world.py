"""
功能:
1. 发起GET请求获取网页内容 cbsnews.com world
2. 解析网页内容，提取特定的div标签中的文本
3. 获取当前日期，用于生成文件名
4. 将提取的内容写入以当前日期命名的Markdown文件
5. X 翻译Markdown文件内容为中文并保存为另一个文件
6. 将最终的中文内容保存到剪贴板
"""

import requests
from bs4 import BeautifulSoup
# from my_memory_tr import MyMemoryTranslator
from datetime import datetime
import pyperclip

# 发起GET请求获取网页内容
url = "https://www.cbsnews.com/world/"
response = requests.get(url)

if response.status_code == 200:
    # 解析网页内容
    soup = BeautifulSoup(response.text, 'html.parser')
    first_div = soup.find_all('div', class_='component__item-wrapper')
    articles = first_div[1].find_all('article')
    print(len(first_div))
    print(len(articles))
    # 获取当前日期，用于生成文件名
    current_date = datetime.now().strftime('%Y%m%d')

    # 将提取的内容写入以当前日期命名的Markdown文件
    english_content = f"# {current_date} CBS News World\n\n"
    with open(f'{current_date}-e.md', 'w', encoding='utf-8') as file:
        for article in articles:
            title_wrapper = article.find('div', class_='item__title-wrapper')
            if title_wrapper:
                title = title_wrapper.find('h4', class_='item__hed').text.strip()
                summ = title_wrapper.find('p', class_='item__dek').text.strip()
                if title and summ:
                    english_content += f'## {title}\n{summ}\n\n'
        file.write(english_content)
    print(f"English Web content has been saved to {current_date}-e.md")

    # 翻译Markdown文件内容为中文并保存为另一个文件
    # translator = MyMemoryTranslator(source='en', target='zh')
    # chinese_content = f"# {current_date} CBS 世界新闻\n\n"
    # with open(f'{current_date}-c.md', 'w', encoding='utf-8') as file:
    #     for line in english_content.split('\n\n'):
    #         if line.strip():
    #             translated_text = translator.translate(line)
    #             chinese_content += translated_text + '\n\n'
    #     file.write(chinese_content)
    # print(f"Content has been translated and saved to {current_date}-c.md")

    # 将最终的中文内容保存到剪贴板
    # pyperclip.copy(chinese_content)
else:
    print("Failed to retrieve page content")
