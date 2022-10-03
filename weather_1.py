
# -*- coding: UTF-8 -*-
import chardet
import requests
from lxml import etree
from fake_useragent import UserAgent
import time
import schedule

# 随机产生请求头
ua = UserAgent(verify_ssl=False)
# 随机切换请求头
def random_ua():
    headers = {
        "user-agent": ua.random
    }
    return headers


def city_num():
    city = "杭州"
    num = 101210101
    return city, num


# 解析页面
def res_text(url='http://www.weather.com.cn/weather1d/101210101.shtml'):
    res = requests.get(url=url, headers=random_ua())
    res.encoding = chardet.detect(res.content)['encoding']  # 获取编码
    response = res.text
    html = etree.HTML(response) # 解析字符串格式的HTML文档对象
    return html


# 获取今天的天气情况
def get_data(url):
    html = res_text(url)
    list_s = html.xpath('//script/text()')[0][22:-4]  # 获取天气数据列表/ul/li *[@id="today"]/div
    list_t = list_s.split('","')[:8]
    list_a ,list_date, list_tem, list_weather, list_wind= [], [], [], [], []
    for i in range(8):
        list_a.append(list_t[i].split(','))

        list_date.append(list_a[i][0][-3:-1])  # 获取时间
        list_tem.append(list_a[i][3]) # 获取气温
        list_weather.append(list_a[i][2])  # 获取天气情况，如：小雨转雨夹雪
        list_wind.append(list_a[i][5])

    excel = {"time":list_date, "temp":list_weather, "weather":list_tem, "wind":list_wind}
    return excel


def main():
    url = 'http://www.weather.com.cn/weather1d/101210101.shtml'
    data = get_data(url)
    print(data["time"][0],data['temp'][0],data['weather'][0],data['wind'][0],sep='\t\t')
    localtime = time.asctime( time.localtime(time.time()) )
    print(localtime)


if __name__ == '__main__':
    main()
    schedule.every(0.1).minutes.do(main)     # 每隔30minutes执行一次

    while True:
        schedule.run_pending()  # run_pending：运行所有可以运行的任务 

