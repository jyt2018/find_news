import json
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime
from lxml import etree  # 新增：支持 XPath

def parse_article(article_item_node, article_meta_conf):
    """解析文章条目节点，提取文章条目信息，使用配置参数2定义提取规则
    :param article_item_node: 文章条目节点，通常是 BeautifulSoup 元素或 lxml 元素。
    :param article_meta_conf: 文章元信息配置字典，定义了提取文章7个通用要素的规则。
    :return: article提取到的文章条目信息字典。
    """

    # 初始化文章字典, 包含7个通用要素,key is same as article_meta_conf and db's column name
    article = {
        "article_url": None,
        "article_title": None,
        "article_tag": None,
        "article_date": None,
        "author": None,
        "excerpt": None,
        "thumbnail": None,
    }

    def apply_filters(elements, filters):
        """
        应用过滤规则到元素列表。支持 startswith, not_in
        e.g. {'attr': 'href', 'startswith': '/category/applications/autonomous/'}
        :param elements: 元素列表，通常是 BeautifulSoup 元素或 lxml 元素。
        :param filters: 过滤规则列表，每个规则是一个字典，包含 'attr' 和 'startswith' 或 'not_in' 键。
        :return: 过滤后的元素列表。
        """
        for filt in filters:
            attr = filt.get('attr')
            if 'startswith' in filt:
                elements = [el for el in elements if el.get(attr, '').startswith(filt['startswith'])]
            elif 'not_in' in filt:
                elements = [el for el in elements if not any(sub in el.get(attr, '') for sub in filt['not_in'])]
        return elements
    
    def post_process(value, processes, extra=None):
        """
        针对str后处理，支持 'make_absolute' 和 'strip_prefix' 两种处理。用于地址补全和字符串简单替换。
        :param value: 提取到的字段值，通常是字符串。
        :param processes: 后处理规则列表，每个规则是一个字符串，包含 'make_absolute' 或 'strip_prefix'。如果传入空列表[], 则不进行后处理。
        :param extra: 额外参数，用于 'strip_prefix' 处理，包含 'prefix' 键。
        :return: 后处理后的字段值。
        """

        for proc in processes:
            if proc == 'make_absolute': # 绝对路径处理, 若不是绝对路径, 则添加站点URL前缀
                print('hello')
            elif proc.get('replace'): # replace str
                replace_conf = proc.get('replace')
                prefix = replace_conf.get('from', '')
                value = value.replace(prefix, replace_conf.get('to', '')) if value.startswith(prefix) else value

        return value.strip() if isinstance(value, str) else value
    

    def extract_field(context, field_conf): # context是传入的七要素之一的节点
        """
        递归提取字段，支持嵌套、回退父元素、默认值等。按conf从context中提取字段，若提取失败则回退到父元素。
        提取一个新闻要素（七要素之一）的配置信息，可以是2-6字段，see sitecfg_key.txt
        :param context: 当前上下文，通常是 BeautifulSoup 元素或 lxml 元素。最开始传入<article>元素, 后续递归调用时传入<article>的子元素例如<div class="card-body">。
        :param field_conf: 抓取策略字典，定义了提取规则。对应scrapy_cfg.json中的extractors中的一个item的value，例如：
        {
            "title": {
                "type": "bs4_find",
                "selector": "h2.entry-title a",
                "extract": "text"
            }
        }的value
        :return: 提取到的字段值，或默认值。
        """

        if 'parent' in field_conf: # 递归处理父元素，这样可以缩小搜索范围
            # 如果有爹，先提取爹
            parent_conf = field_conf['parent']
            parent = extract_element(context, parent_conf)
            print(f" --- 找到了他爹: {parent}\n")
            if not parent:
                return field_conf.get('default', '')
            # 如果找到了爹, 则以爹为上下文context, 继续提取
            context = parent
        
        elem = extract_element(context, field_conf)

        extract_key = field_conf.get('extract', 'text') # get extract key, default is 'text'
        print(f" -- extract_key: {extract_key}")
        if extract_key == 'text':
            val = elem.get_text(strip=True)
            print(f" -- text: {val}\n")
        else:
            val = elem.get(extract_key, '')
            print(f" -- val: {val}\n")
        
        processes = field_conf.get('post_process') # 如果没找到post_process, 则skip
        if not processes:
            return val

        print(f" -- post_process: {processes}\n")
        val = post_process(val, processes) # processes is list, extra is dict
        print(f" -- post_process: {val}\n")
        if 'sub_selectors' in field_conf:
            for sub in field_conf['sub_selectors']:
                sub_val = extract_field(elem, sub)
                if sub_val and 'key' in sub:
                    article[sub['key']] = sub_val
        
        return val
    
    # 辅助函数：定位元素
    def extract_element(context, conf):
        # context被一级调用时, 传入的是<article>元素, 后续递归调用时传入的是<article>的子元素例如<div class="card-body">
        typ = conf['type'] # 提取手段，例如 bs4_find, bs4_find_all, xpath 等
        print(f" -- type: {typ}")
        sel = conf['selector'] # 提取目标，例如 'h2.entry-title a' or ['h2', {'class': 'entry-title'}] or {'class_': 'card-bocy'} 
        print(f" -- selector: {sel}")
        
        # type 三选一
        if typ == 'bs4_find':
            # 如果是字典类型则使用**sel解包字典，形成context.find(name='div', class_='card-bocy')
            if isinstance(sel, dict):
                return context.find(**sel)
            elif isinstance(sel, list): # 如果是列表类型则使用*sel解包列表，形成context.find('h2', {'class': 'entry-title'})
                return context.find(*sel)
            else: # 如果是字符串类型则直接使用sel，形成context.find('h2.entry-title a')
                return context.find(sel)
        elif typ == 'bs4_find_all':
            # 如果是字典类型则使用**sel解包字典，形成context.find_all(name='div', class_='card-bocy')
            if isinstance(sel, dict):
                elems = context.find_all(**sel)
            elif isinstance(sel, list): # 如果是列表类型则使用*sel解包列表，形成context.find_all('h2', {'class': 'entry-title'})
                elems = context.find_all(*sel)
            else: # 如果是字符串类型则直接使用sel，形成context.find_all('h2.entry-title a')
                elems = context.find_all(sel)

            # find_all数量多会涉及到过滤
            print(f" -- 含有{sel}: {len(elems)}个")
            if 'filters' in conf:
                elems = apply_filters(elems, conf['filters'])
                # print(f" -- elems after filters: {elems}\n")
            limit = conf.get('limit', None)
            return elems[0] if limit == 1 else elems
        elif typ == 'xpath':
            elems = tree.xpath(sel) if context is soup else context.xpath(sel)  # lxml 支持相对 XPath
            print(f" -- elems: {elems}\n")
            return elems[0] if elems else None
        return None
    
    # ===========================================
    # parse_article 主干-依次提取7要素, 最多循环7次
    for field, field_conf in article_meta_conf.items():
        # field is the key in config(eg. title, url, author ), type is str; mapping to db columns
        # field_conf is 文章七要素的一个要素的配置字典
        print(f"✔️ 七要素    : {field}")
        print(f"✔️ 七要配conf: {field_conf}\n")

        # 最开始传入<article>
        article[field] = extract_field(article_item_node, field_conf) # article['title'] = 'title text'
        print(f" == {field}: {article[field]}\n")

    
    return article

if __name__ == '__main__':
    # 导入自定义库
    from lib_get_articletag import get_article_containers
    
    html_path = 'index2.html'  # 直接使用当前目录的文件，因为脚本在tools目录运行

    config_page = 'scrapy_page.json'
    config_meta = 'scrapy_article.json'

    c_tag = 'autonomous'
    
    # 加载页面配置文件 找article在哪
    with open(config_page, 'r', encoding='utf-8') as f:
        config_article = json.load(f)
        print(config_article.keys())


    # 加载配置文件
    with open(config_meta, 'r', encoding='utf-8') as f2:
        config = json.load(f2)
    article_meta_conf = config['article_meta'] # 文章元信息配置，用于提取文章的7个通用要素
    
    # 读取HTML文件
    with open(html_path, 'r', encoding='utf-8') as f3:
        html_content = f3.read()
    
    # 第一步：使用自定义库获取文章容器
    try:

        article_containers = get_article_containers(html_content, config_article)
        print(len(article_containers), "篇\n")
    except ValueError as e:
        print(f"错误: {e}")
        exit(1)
    except Exception as e:
        print(f"处理过程中出错: {e}")
        exit(1)

    # 第二步，遍历每个文章条目，提取各个文章条目的通用7要素element(标题 作者 日期 摘要 链接 分类标签 小图片)
    for article_item_node in article_containers:
        # 每次处理一篇文章
        article_item = parse_article(article_item_node, article_meta_conf) # article_meta_conf是字典，有7个item对应文章的七要素提取策略
        article_item['tag'] = c_tag # c_tag的作用是把版块信息传递给single文章，以后用这个字段拼接所有tag
        print("\n")
        # print("🖐️ ", article_item, "\n\n")

