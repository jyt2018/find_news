import requests
import json
import datetime
from datetime import datetime
import requests
import qrcode
from PIL import Image


def get_current_date_lunar():
    """
    返回当前日期，格式 年 月 日 星期 农历
    """
    today = datetime.today()
    year = today.year
    month = today.month
    day = today.day

    # 获取星期，Monday is 0, Sunday is 6
    weekday = today.weekday()
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    week = weekday_cn[weekday]

    # 获取农历日期（需要第三方库如lunarcalendar）
    # try:
    #     from lunarcalendar import Solar
    #     solar_date = Solar(year, month, day)
    #     lunar_year, lunar_month, lunar_day = solar_date.get_lunar_date()
    #     lunar_date = f"{lunar_year}年{lunar_month}月{lunar_day}日"
    # except ImportError:
    #     lunar_date = "农历转换库未安装或失败"

    return year, month, day, week


# 打印当前日期，格式年月日星期农历
ret = get_current_date_lunar()
print("📅",ret[1], "/", ret[2], f" {ret[3]}", end="|")
input_string = "📅" + f"{ret[1]}/{ret[2]} {ret[3]}|"


def fetch_historical_events(date, out_count):
    """
    该函数用于根据提供的 API 地址、API 密钥和日期获取历史上的今天的事件列表。https://www.juhe.cn/docs/api/id/63
    849-历史上的今天-事件列表(v2.0推荐) - 代码参考（根据实际业务情况修改）
    参数:
    apiUrldate (str): 接口请求的 URL
    apiKey (str): API 密钥
    date (str): 日期，格式为 "mm/dd"
    out_count: 返回的条数，不能太多，太多了烦人
    返回:
    str: 包含历史事件信息的字符串，如果请求异常则返回 "请求异常"
    """
    apiUrldate = 'http://v.juhe.cn/todayOnhistory/queryEvent'  # 接口请求URL
    apiKeys = '********'  # 在个人中心->我的数据,接口名称上方查看

    # 接口请求入参配置
    requestParamsdate = {
        'key': apiKeys,
        'date': date  # "mm/dd"
    }

    # 发起接口网络请求
    responses = requests.get(apiUrldate, params=requestParamsdate)

    if responses.status_code == 200:
        input_string = ""
        responseResults = responses.json()
        his = responseResults.get("result")  # 所有事件列表
        print("🔔历史上的今天：%s 条" % len(his))
        for i, his1 in enumerate(his):
            if i==out_count:
                break
            print(his1.get("date"), his1.get("title"), end="|")
            input_string += his1.get("date") + his1.get("title") + "|"
        return input_string
    else:
        # 网络异常等因素，解析结果异常。可依据业务逻辑自行处理。
        print('todayOnhistory请求异常')
        return 'todayOnhistory请求异常'


def query_news_list(api_key='1e9f3a1783fb78bdf88b707ef15f68fa', news_type='guoji', page=1, page_size=12, is_filter=''):
    """
    此函数用于查询新闻列表。
    参数:
    api_key (str): 接口调用的密钥，默认为'1e9f3a1783fb78bdf88b707ef15f68fa'。
    news_type (str): 新闻类型，可选值有'top'(推荐,默认)、'guonei'(国内)、'guoji'(国际)、'yule'(娱乐)、'tiyu'(体育)、'junshi'(军事)、
                    'keji'(科技)、'caijing'(财经)、'youxi'(游戏)、'qiche'(汽车)、'jiankang'(健康)，默认为'guoji'。
    page (int): 当前页数，默认是 1，最大值为 50。
    page_size (int): 每页返回的新闻条数，默认是 30，最大值为 30。
    is_filter (str): 是否只返回有内容详情的新闻，'1'表示是，默认是'0'。

    返回:
    dict: 接口返回的 JSON 响应结果，如果请求异常则返回 None。
    """
    # 接口请求 URL
    apiUrl = 'http://v.juhe.cn/toutiao/index'
    # 接口请求入参配置
    requestParams = {
        'key': api_key,
        'type': news_type,
        'page': str(page),
        'page_size': str(page_size),
        'is_filter': is_filter,
    }
    try:
        # 发起接口网络请求
        response = requests.get(apiUrl, params=requestParams)
        # 解析响应结果
        if response.status_code == 200:
            return response.json()
        else:
            print('请求异常')
            return None
    except requests.RequestException as e:
        print(f"请求异常，异常信息: {e}")
        return None


hise = fetch_historical_events(f"{ret[1]}/{ret[2]}", 2)
input_string += hise
responseResult = query_news_list()
res = responseResult.get("result").get("data")
input_string += "🌏新闻："+"|"
for i, n in enumerate(res):
    print(f"{i+1}. " + n.get("title"), end="|")
    input_string += f"{i+1}. " + n.get("title") + "|"
    # long_url = n.get("url")
    # response = requests.post(f"http://tinyurl.com/api-create.php?url={long_url}")
    # short_url = response.text
    # print(" " + long_url)
print("买钛酸钾镁找我 白色 灰色 质优价廉")
input_string += "13. 卖钛酸钾晶须和钛酸钾镁片晶的我已经起床"


qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)

# Add the converted string to the QR code instance
qr.add_data(input_string.replace("|", "\n"))
qr.make(fit=True)

# Create an image from the QR code instance
img = qr.make_image(fill_color="black", back_color="white")

# Display the QR code
img.show()
