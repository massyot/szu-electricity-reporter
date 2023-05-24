import crawler
import sc_sender

import json

import datetime
import time

import sys

import os



def getConfig():
    with open('config.json', encoding='utf-8') as f:
        config = json.load(f)
    return config

def checkWifi():
    res = os.system("ping baidu.com -n 1")
    return 1 if res == 0 else 0


# main函数
def main():
    # try:
        # 获取配置
        config = getConfig()
        room_name = config['room_name']
        room_id = config['room_id']
        client = config['client']
        interval_day = config['interval_day']
        sendKey_list = config['server_chan_key']
        remind_daily = config['remind_daily']
        remind_time = config['remind_time']

        #检查wifi，如果没连接等连上再继续
        while(1):
            time.sleep(10)
            if checkWifi():
                break

        if room_name == '' or room_id == '':
            print('[error] 未配置config.json!')
            sys.exit()
        # 获得数据
        table_data = crawler.crawlData(client, room_name, room_id, interval_day)
        if len(table_data) == 0:
            print('[爬取数据失败，请检查是否能访问电费查询网站"http://192.168.84.3:9090/cgcSims/"]')
            sys.exit()
        print('[爬取数据结束]')

        # 处理数据
        data = processingData(table_data)
        print('[数据处理结束]')
        # 在控制台格式化输出爬虫获得的数据
        printData(data)

        # 若 sc_key 存在，则发送微信提醒
        if sendKey_list != '':
            # describe参数内容会添加到内容详情最前端。
            # 在 f-string 中，可以通过在字符串中使用花括号 {} 来引用变量
            describe = f'{room_name}宿舍电量查询：'
            # 处理数据为要发送的表格格式信息
            send_msg = sc_sender.handle(data, describe)
            # 发送信息
            for i in range(len(sendKey_list)):
                sc_sender.send(
                    key_url="https://sctapi.ftqq.com/"+sendKey_list[i]+".send",
                    data=send_msg,
                )
            print('[已发送至微信]')
            sys.exit()
        
        if remind_daily is False or sendKey_list == '':
            sys.exit()
        today_date = datetime.date.today()
        next_day_date = today_date + datetime.timedelta(days=1)
        next_exec_time = datetime.datetime.combine(
            next_day_date, datetime.time(hour=remind_time))
        delta_time = (next_exec_time - datetime.datetime.now()).total_seconds()
        print(f'下次查询电量的时间：{next_exec_time}')
        time.sleep(delta_time)
    # except Exception as e:
    #     print("Error:出现错误:"+str(e)+"！")
    # finally:
    #     print("执行完毕。")

# 加工数据获得想要的数据格式
def processingData(table_data: list):
    data = []
    day_num = len(table_data)

    # 日期 | 当日用电量
    for i in range(day_num - 1):
        charge = table_data[i + 1][3] - table_data[i][3]
        data.append({
            'date': table_data[i][0],
            'cost': table_data[i][1] - table_data[i + 1][1],
            'rest': table_data[i][1],
            'charge': charge
        })
        if charge != 0:
            data[-1]['cost'] += charge  # 充了电，则需要修正耗电计算公式问题
        else:
            data[-1]['charge'] = '-'  # 没充电费

    # 最后一天需要单独赋值
    data.append({
        'date': table_data[day_num - 1][0],
        'cost': '-',
        'rest': table_data[day_num - 1][1],
        'charge': '-'
    })

    return data


# 格式化输出爬虫获得的数据
def printData(data: list):
    print('日期'.ljust(8, ' '), '当日用电'.ljust(8, ' '),
          '可用电量'.ljust(8, ' '), '当日充电'.ljust(8, ' '))
    for row in data:
        for datum in row:
            value = row[datum]
            # float型要转换为str才可以使用ljust函数
            if isinstance(value, float):
                value = '{:.2f}'.format(value)
            print(value.ljust(12, ' '), end='')  # 每个数据的长度为12字符宽
        print()
    return


if __name__ == '__main__':
    main()
