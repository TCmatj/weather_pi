from waveshare_epd import epd3in52

epd = epd3in52.EPD()
epd.init()  # 墨水屏初始化，再屏幕开始工作时和退出睡眠模式之后调用
epd.display_NUM(epd.WHITE)
epd.lut_GC()
epd.refresh()