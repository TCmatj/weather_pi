import os
import sys
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')  # dirname去掉文件名，返回目录 获得你刚才所引用的模块所在的绝对路径
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd3in52
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

logging.basicConfig(level=logging.DEBUG) # debug消息级别

weather_iconnum = {'晴':100,"多云":101,"少云":102,'晴间多云':103,'阴':104,
                    '阵雨':300,'强阵雨':301,'雷阵雨':302,'强雷阵雨':303,'雷阵雨伴有冰雹':304,
                    '小雨':305,'中雨':306,'大雨':307,'极端降雨':308,'毛毛雨/细雨':309,'暴雨':310,
                    '大暴雨':311,'特大暴雨':312,'冻雨':313,'小到中雨':314,'中到大雨':315,'大到暴雨':316,
                    '暴雨到大暴雨':317,'大暴雨到特大暴雨':318,'阵雨':350,'强阵雨':351,'雨':399,
                    '小雪':400,'中雪':401,'大雪':402,'暴雪':403,'雨夹雪':404,'雨雪天气':405,'阵雨夹雪':406,
                    '阵雪':407,'小到中雪':408,'中到大雪':409,'大到暴雪':410,'阵雨夹雪':456,'阵雪':457,'雪':499,
                    '薄雾':500,'雾':501,'霾':502,'扬沙':503,'浮尘':504,'沙尘暴':507,'强沙尘暴':508,'浓雾':509,
                    '强浓雾':510,'中度霾':511,'重度霾':512,'严重霾':513,'大雾':514,'特强浓雾':515,
                    '新月':800,'蛾眉月':801,'上弦月':802,'盈凸月':803,'满月':804,'亏凸月':805,'下弦月':806,'残月':807,
                    '热':900,'冷':901}
weather_iconnum_night = {'晴':150,'多云':151,'少云':152,'晴间多云':153}
epd = epd3in52.EPD()

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
        res = requests.get(url=url, headers=random_ua(), timeout=10)
        res.encoding = chardet.detect(res.content)['encoding']  # 获取编码
        response = res.text
        html = etree.HTML(response) # 解析字符串格式的HTML文档对象
        return html


    # 获取今天的天气情况
    def get_data(url):
        html = res_text(url)
        list_sunDown = html.xpath('//*[@class="sun sunDown"]/span/text()')[0][-5:]   # 日落时间
        list_sunUp = html.xpath('//*[@class="sun sunUp"]/span/text()')[0][-5:]   # 日出时间
        list_today = html.xpath('//input[@id="hidden_title"]/@value')[0]    # 总览
        list_lihot = html.xpath('//*[@class="li1 hot"]/span/text()')[0]    #紫外线指数

        list_clearfix = html.xpath('//*[@class="clearfix"]/li/h1/text()')
        list_clearfix_weather = html.xpath('//*[@class="clearfix"]/li/p[1]/text()')[0:2]
        list_clearfix_temp = html.xpath('//*[@class="clearfix"]/li/p[2]/span/text()')
        
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


    def draw_weather_icon(data):
        logging.info("init and Clear")
        epd.init()  # 墨水屏初始化，再屏幕开始工作时和退出睡眠模式之后调用
        epd.display_NUM(epd.WHITE)
        epd.lut_GC()
        epd.refresh()
        
        epd.send_command(0x50)
        epd.send_data(0x17)

        font8 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 8)
        font10 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 10)
        font15 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 15)
        i=0
        Himage = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame
        draw = ImageDraw.Draw(Himage)   # 绘图声明:告诉你就在这个图上绘图
        for weather in data['weather']:
            if int(data['time'][i])>18 and (data['weather'][i] in ['晴','多云','少云','晴间多云']):
                weather_id = weather_iconnum_night.get(weather)
            else:
                weather_id = weather_iconnum.get(weather)
            path =  'icons_bmp/' + str(weather_id) + '.bmp'
            drawimg = Image.open(path)

            import random
            count = 0
            path = 'picture/'
            for file in os.listdir(path): #file 表示的是文件名
                count = count+1
            path = 'picture/' + str(random.randint(1,count)) + '.bmp'
            picture = Image.open(path)

            draw.rectangle((0,0,120,240),outline=0,width=2)
            draw.line((0,60,120,60),width=2)
            draw.line((0,120,120,120),width=2)
            draw.line((0,180,120,180),width=2)
            draw.line((0,240,120,240),width=2)
            draw.line((60,0,60,240),width=2)
            draw.text((18+(i%2)*60, 40+int(i/2)*60), u'°C', font = font15, fill = 0)

            # Himage.paste(drawimg,(14+60*(i%2),5+int(i/2)*60))
            # draw.text((5+(i%2)*60, 40+int(i/2)*60), data['time'][i], font = font10, fill = 0)
            # draw.text((20+(i%2)*60, 40+int(i/2)*60), data['temp'][i], font = font10, fill = 0)#+'°C'
            # draw.text((35+(i%2)*60, 40+int(i/2)*60), data['wind'][i], font = font10, fill = 0)

            Himage.paste(drawimg,(8+14+60*(i%2),5+int(i/2)*60))
            draw.text((2+(i%2)*60, 2+int(i/2)*60),'Time', font = font8, fill = 0)
            draw.text((2+(i%2)*60, 8+int(i/2)*60), data['time'][i], font = font15, fill = 0)
            draw.text((2+(i%2)*60, 40+int(i/2)*60), data['temp'][i], font = font15, fill = 0)
            draw.text((40+(i%2)*60, 40+int(i/2)*60),'Wind', font = font8, fill = 0)
            draw.text((35+(i%2)*60, 50+int(i/2)*60), data['wind'][i], font = font10, fill = 0)

            Himage.paste(picture,(120,0))
            i = i + 1

        Himage = Himage.rotate(180)
        epd.display(epd.getbuffer(Himage))
        epd.lut_GC()
        epd.refresh()

    def main():
        url = 'http://www.weather.com.cn/weather1d/101210101.shtml'
        data = get_data(url)
        draw_weather_icon(data)

        
    if __name__ == '__main__':
        main()
        schedule.every(0.2).minutes.do(main)     # 每隔30minutes执行一次

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