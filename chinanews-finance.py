"""
功能:
1. 发起GET请求获取XML数据
2. 解析XML数据，提取item标签中的title内容
3. 获取当前日期，用于生成文件名
4. 将提取的内容写入文件，并在文件末尾写入特定内容
5. 将文件内容保存到剪贴板
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pyperclip

# 发起GET请求获取XML数据
url = 'https://www.chinanews.com.cn/rss/finance.xml'
response = requests.get(url)

if response.status_code == 200:
    # 解析XML数据
    root = ET.fromstring(response.content)

    # 提取item标签中的title内容
    items = root.findall('.//channel/item')

    # 获取当前日期，用于生成文件名
    today = datetime.today()
    file_name = today.strftime('%y%m%d') + '财经.txt'

    content = today.strftime('%Y-%m-%d') + '财经\n\n'
    i = 0
    for item in items:
        i += 1
        title = item.find('title').text
        # description = item.find('description').text

        if title:
            content += f'{i}. {title}\n'
            # if description:
            #     content += description + '\n'

    # 写入特定内容到文件末尾
    content += '🙋钛酸钾（镁）晶须请联系：钛经理📞1123451796'

    # 将内容写入文件
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(content)

    # 将内容保存到剪贴板
    pyperclip.copy(content)

    print("Processed data saved as '{}'".format(file_name))
else:
    print("Failed to retrieve XML data from the provided URL")
