#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')  # dirname去掉文件名，返回目录 获得你刚才所引用的模块所在的绝对路径
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
#print(picdir,'\n',libdir)

if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd3in52
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

logging.basicConfig(level=logging.DEBUG) # debug消息级别

try:
    logging.info("天气")
    
    import chardet
    import requests
    from lxml import etree
    from fake_useragent import UserAgent
    import schedule
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM

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

        excel = {"time":list_date, "weather":list_weather, "temp":list_tem, "wind":list_wind}
        return excel


    def show_weather(data):
        epd = epd3in52.EPD()
        logging.info("init and Clear")
        epd.init()  # 墨水屏初始化，再屏幕开始工作时和退出睡眠模式之后调用
        epd.display_NUM(epd.WHITE)
        epd.lut_GC()
        epd.refresh()

        epd.send_command(0x50)
        epd.send_data(0x17)
        time.sleep(2)   # 进程挂起2秒

        font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)   # 第一个参数是字体文件
        font18 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 18)
        font30 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 40)
    
        # Drawing on the Horizontal image
        logging.info("更新信息")
        Himage = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame
        draw = ImageDraw.Draw(Himage)   # 绘图声明:告诉你就在这个图上绘图
        
        draw.text((10, 0), data['time'][0], font = font24, fill = 0)
        draw.text((50, 0), data['temp'][0], font = font24, fill = 0)
        draw.text((80, 0), data['weather'][0], font = font24, fill = 0)
        draw.text((150, 0), data['wind'][0], font = font24, fill = 0)
        localtime = time.asctime( time.localtime(time.time()) )
        draw.text((10, 30), localtime, font = font24, fill = 0)
        
        Himage = Himage.rotate(180)
        epd.display(epd.getbuffer(Himage))
        epd.lut_GC()
        epd.refresh()


    def weather_icon(weatherid):
        path_null = 'weather_icons/' + str(weatherid) + '.bmp'
        drawimg = svg2rlg(path_fill)
        return drawimg

    def main():
        url = 'http://www.weather.com.cn/weather1d/101210101.shtml'
        data = get_data(url)
        show_weather(data)

        
    if __name__ == '__main__':
        main()
        schedule.every(0.1).minutes.do(main)     # 每隔30minutes执行一次

       
        while True:
            schedule.run_pending()  # run_pending：运行所有可以运行的任务 


       
    logging.info("Clear...")
    epd.Clear()
    
    logging.info("Goto Sleep...")
    epd.sleep()
    
except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:   # 捕获使用快捷键Ctrl+C的异常 
    logging.info("ctrl + c:")
    epd3in52.epdconfig.module_exit()
    exit()
