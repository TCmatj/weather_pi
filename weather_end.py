import os
import sys
import socket
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')  # dirname去掉文件名，返回目录 获得你刚才所引用的模块所在的绝对路径
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd3in52
import time
from PIL import Image,ImageDraw,ImageFont

logging.basicConfig(level=logging.DEBUG, format = '%(asctime)s - %(levelname)s - %(message)s') # debug消息级别

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

        excel = {"time":list_date, "weather":list_weather, "temp":list_tem, "wind":list_wind, 
                 'sundown':list_sunDown, 'sunup':list_sunUp, 'today':list_today, 'lihot':list_lihot,
                 'text':list_clearfix, 'text_weather':list_clearfix_weather, 'text_temp':list_clearfix_temp}
        return excel


    def draw_weather_icon(data):
        logging.info("init and Clear")
        epd.init()  # 墨水屏初始化，再屏幕开始工作时和退出睡眠模式之后调用
        epd.display_NUM(epd.WHITE)
        epd.lut_GC()
        epd.refresh()
        
        epd.send_command(0x50)
        epd.send_data(0x17)

        font6 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 6)
        font8 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 8)
        font10 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 10)
        font11 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 11)
        font15 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 15)
        font25 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 25)
        i=0
        Himage = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame
        draw = ImageDraw.Draw(Himage)   # 绘图声明:告诉你就在这个图上绘图

        ## 绘制图框
        draw.rectangle((0,0,358,238),outline=0,width=2)
        draw.line((0,60,120,60),width=1)
        draw.line((0,120,120,120),width=1)
        draw.line((0,180,120,180),width=1)
        draw.line((0,240,120,240),width=1)
        draw.line((60,0,60,240),width=1)
        draw.line((120,0,120,240),width=1)
        for weather in data['weather']:
            if int(data['time'][i])>18 and (data['weather'][i] in ['晴','多云','少云','晴间多云']):
                weather_id = weather_iconnum_night.get(weather)
            else:
                weather_id = weather_iconnum.get(weather)
            path =  'icons_bmp/' + str(weather_id) + '.bmp'
            drawimg = Image.open(path)

            ## 绘制图标和文字
            Himage.paste(drawimg,(8+14+60*(i%2),5+int(i/2)*60))
            draw.text((2+(i%2)*60, 2+int(i/2)*60),'Time', font = font8, fill = 0)
            draw.text((2+(i%2)*60, 8+int(i/2)*60), data['time'][i], font = font15, fill = 0)
            draw.text((2+(i%2)*60, 40+int(i/2)*60), data['temp'][i], font = font15, fill = 0)
            draw.text((18+(i%2)*60, 40+int(i/2)*60), u'°C', font = font15, fill = 0)
            draw.text((40+(i%2)*60, 40+int(i/2)*60),'Wind', font = font8, fill = 0)
            draw.text((35+(i%2)*60, 48+int(i/2)*60), data['wind'][i], font = font10, fill = 0)
            
            i = i + 1

        ## 绘制图片
        import random
        count = 0
        path = 'picture/'
        for file in os.listdir(path): #file 表示的是文件名
            count = count+1
        path = 'picture/' + str(random.randint(1,count)) + '.bmp'
        picture = Image.open(path)
        Himage.paste(picture,(121,33))

        ## 绘制图框
        draw.line((358,0,358,240), fill=0, width=2) #图片有可能覆盖，补一条线
        draw.line((0,238,360,238), fill=0, width=2) #图片有可能覆盖，补一条线
        draw.rectangle((320,32, 357,237), fill = 255, outline=0, width=1)
        draw.line((120,32,320,32), fill=0, width=1)
        draw.line((320,100,360,100), fill=0, width=1)
        draw.line((320,125,360,125), fill=0, width=1)
        draw.line((320,200,360,200), fill=0, width=1)
        draw.line((330,220,360,220), fill=0, width=1)

        ## 绘制总览和实况
        draw.text((122, 5),data['today'][:6], font = font25, fill = 0)  #日期
        draw.text((240, 5),data['today'][10:12], font = font25, fill = 0)   #周几
        t = time.localtime()    #获取时间并标准化
        if(t.tm_hour<10):
            tm_hour = '0' + str(t.tm_hour)
        else:
            tm_hour = str(t.tm_hour)
        if(t.tm_min<10):
            tm_min = '0' + str(t.tm_min)
        else:
            tm_min = str(t.tm_min)
        times = str(tm_hour) + ':' + str(tm_min)
        draw.text((290, 5),times, font = font25, fill = 0)   #实时时间
        draw.text((320, 102),data['today'][14:-7], font = font10, fill = 0) #今日天气
        draw.text((325, 32),data['text'][0][-2:], font = font15, fill = 0)  #第一段时间名称
        draw.text((325, 180),data['text'][1][-2:], font = font15, fill = 0) #第二段时间名称
        draw.text((322, 78),data['text_temp'][0], font = font15, fill = 0)  #第一段温度
        draw.text((340, 78), u'°C', font = font15, fill = 0)
        draw.text((322, 130),data['text_temp'][1], font = font15, fill = 0) #第二段温度
        draw.text((340, 130), u'°C', font = font15, fill = 0)
        draw.text((320, 112), u'紫外:', font = font10, fill = 0)
        draw.text((340, 112),data['lihot'], font = font10, fill = 0)        #紫外线强度

        ## 日出日落
        draw.text((330, 203),data['sunup'], font = font11, fill = 0)
        draw.text((330, 223),data['sundown'], font = font11, fill = 0)
        draw.text((320, 200),'日', font = font10, fill = 0)
        draw.text((320, 210),'出', font = font10, fill = 0)
        draw.text((320, 220),'日', font = font10, fill = 0)
        draw.text((320, 230),'落', font = font10, fill = 0)

        #空余六个像素
        draw.text((120, 232),'2022.10.4TianC qq2216685752 TianC qq2216685752 TianC qq2216685752', font = font6, fill = 0)

        if int(data['today'][7:8])>18 and (data['text_weather'][0] in ['晴','多云','少云','晴间多云']):
            weather_id = weather_iconnum_night.get(data['text_weather'][0])
        else:
            weather_id = weather_iconnum.get(data['text_weather'][0])
        path =  'icons_bmp/' + str(weather_id) + '.bmp'
        drawimg = Image.open(path)
        Himage.paste(drawimg,(322, 50))
        if int(data['today'][7:8])>18 and (data['text_weather'][1] in ['晴','多云','少云','晴间多云']):
            weather_id = weather_iconnum_night.get(data['text_weather'][1])
        else:
            weather_id = weather_iconnum.get(data['text_weather'][1])
        path =  'icons_bmp/' + str(weather_id) + '.bmp'
        drawimg = Image.open(path)
        Himage.paste(drawimg,(322, 150))

        ## 旋转绘制
        Himage = Himage.rotate(180)
        epd.display(epd.getbuffer(Himage))
        epd.lut_GC()
        epd.refresh()


    def isNetOK(testserver):
        s = socket.socket()
        s.settimeout(3)
        try:
            status = s.connect_ex(testserver)
            if status == 0:
                s.close()
                return True
            else:
                return False
        except Exception as e:
            return False

    def main():
        if isNetOK(testserver=('www.baidu.com', 443)):
            url = 'http://www.weather.com.cn/weather1d/101210101.shtml'
            data = get_data(url)
            draw_weather_icon(data)
        
    if __name__ == '__main__':
        main()
        schedule.every(1).minutes.do(main)     # 每隔30minutes执行一次

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