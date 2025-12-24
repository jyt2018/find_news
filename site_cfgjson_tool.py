import json
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime
from lxml import etree  # 新增：支持 XPath

def parse_articles(html, config_path, c_tag):
    """解析网页内容，提取文章条目信息，使用配置文件定义提取规则"""

    articles = []
    soup = BeautifulSoup(html, 'html.parser')
    tree = etree.HTML(html)  # 新增：lxml 树，用于 XPath
    
    # 加载配置文件, config's type is dict
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)['extractors']
    

    
    # 辅助函数：应用过滤规则, 支持 startswith, not_in
    # e.g. {'attr': 'href', 'startswith': '/category/applications/autonomous/'}
    def apply_filters(elements, filters):
        for filt in filters:
            attr = filt.get('attr')
            if 'startswith' in filt:
                elements = [el for el in elements if el.get(attr, '').startswith(filt['startswith'])]
            elif 'not_in' in filt:
                elements = [el for el in elements if not any(sub in el.get(attr, '') for sub in filt['not_in'])]
        return elements
    
    # 辅助函数：后处理
    def post_process(value, processes, extra=None):
        for proc in processes:
            if proc == 'make_absolute':
                if not value.startswith('http'):
                    value = f"{self.site_cfg['site_url']}{value}"
            elif proc == 'strip_prefix' and extra:
                prefix = extra.get('prefix', '')
                value = value.replace(prefix, '') if value.startswith(prefix) else value
        return value.strip() if isinstance(value, str) else value
    

    def extract_field(context, conf, fallback_parent=None): # field大 element小
        """
        递归提取字段，支持嵌套、回退父元素、默认值等。
        :param context: 当前上下文，通常是 BeautifulSoup 元素或 lxml 元素。
        :param conf: 配置字典，定义了提取规则。是scrapy_cfg.json中的extractors中的一个item，例如：
        {
            "title": {
                "type": "bs4_find",
                "selector": "h2.entry-title a",
                "extract": "text"
            }
        }
        :param fallback_parent: 回退父元素的标志，用于处理递归调用。
        :return: 提取到的字段值，或默认值。
        """

        if 'parent' in conf: # 递归处理父元素，因为父元素容易定位
            parent_conf = conf['parent']
            parent = extract_element(context, parent_conf)
            if not parent:
                return conf.get('default', '')
            context = parent
        
        if 'methods' in conf:
            for method in conf['methods']:
                val = extract_field(context, method, fallback_parent)
                if val:
                    return val
            return conf.get('default', '')
        
        elem = extract_element(context, conf)
        if not elem:
            if fallback_parent == 'container':
                elem = extract_element(soup, conf)  # 回退到容器
            if not elem:
                return conf.get('default', '')
        
        extract_key = conf.get('extract', 'text')
        if extract_key == 'text':
            val = elem.get_text(strip=True)
        else:
            val = elem.get(extract_key, '')
        
        processes = conf.get('post_process', [])
        val = post_process(val, processes, extra=conf.get('post_process_extra'))
        
        if 'sub_selectors' in conf:
            for sub in conf['sub_selectors']:
                sub_val = extract_field(elem, sub)
                if sub_val and 'key' in sub:
                    article[sub['key']] = sub_val
        
        return val
    
    # 辅助函数：定位元素
    def extract_element(context, conf): # field大 element小
        typ = conf['type'] # 提取手段，例如 bs4_find, bs4_find_all, xpath 等
        sel = conf['selector'] # 提取目标，例如 'h2.entry-title a' or ('h2.entry-title', {'class': 'entry-title'}) or {'class': 'entry-title'}

        if typ == 'bs4_find':
            return context.find(sel) if isinstance(sel, str) else context.find(*sel) if isinstance(sel, list) else context.find(**sel)
        elif typ == 'bs4_find_all':
            elems = context.find_all(sel) if isinstance(sel, str) else context.find_all(*sel) if isinstance(sel, list) else context.find_all(**sel)
            if 'filters' in conf:
                elems = apply_filters(elems, conf['filters'])
            limit = conf.get('limit', None)
            return elems[0] if limit == 1 else elems
        elif typ == 'xpath':
            elems = tree.xpath(sel) if context is soup else context.xpath(sel)  # lxml 支持相对 XPath
            return elems[0] if elems else None
        return None
    
    # 查找所有 article 容器
    article_containers = soup.find_all('article')
    
    for article_item_node in article_containers: # 遍历每个 article 容器, article_item_node is a single article with html tags, type is bs4.element.Tag
        article = {}
        card_body = article_item_node.find('div', class_='card-body')  # 保留原 card_body 查找，可配置化
        
        # 动态提取配置中的字段
        for field, conf in config.items():
            # field is the key in config(eg. title, url, author etc.), type is str; mapping to db columns
            # conf is the value in config, datatype is dict(eg. {'type': 'bs4_find', 'selector': 'h2.entry-title a'}) type is dict.
            article[field] = extract_field(article_item_node, conf) # article['title'] = 'title text'

        # 添加固定元信息
        article['tag'] = c_tag
        
        articles.append(article)
    
    return articles

if __name__ == '__main__':
    html = open('index.html', 'r', encoding='utf-8').read()    
    config_path = 'scrapy_cfg.json'
    c_tag = 'autonomous'
    # 应该分两步，第一步确定文章条目的标签，应该是一个列表，例如10个<article>标签, article也应该在配置文件里，因为有可能是li
    # 第二步，遍历每个文章条目，提取各个文章条目的通用7要素element(标题 作者 日期 摘要 链接 分类标签 小图片)
    articles = parse_articles(html, config_path, c_tag) # c_tag的作用是把版块信息传递给文章
    print("\n")
    print(articles)

