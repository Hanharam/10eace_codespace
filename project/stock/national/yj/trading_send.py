#import sys
#sys.path.append('/workspaces/10eace_codespace/project/stock/national/yj')

import api
import get_symbol as gsym
import datetime
import time
import numpy as np
from multiprocessing import Process, Manager, Queue


f_data_address = "/home/ubuntu/code-server/project/stock/yj/data/"    # 파일 경로(접근 토근, 종목 리스트, 데이터 요청 리스트, 거래량)
f_line_address = "/home/ubuntu/code-server/project/stock/yj/line/"    # 파일 경로(저항선, 지지선)


def refresh_symbol(keep_dict: dict, num_of_symbol: int=3, refresh_count: int=0):
    gsym.get_ma_distances_multiprocessing()    # 이동 평균선 간격 구하기
    gsym.get_symbol_by_distance()    # 이동 평균선 간격에 따른 종목 선별
    gsym.write_symbol_file(keep_dict, num_of_symbol, refresh_count)    # 최종 선별된 종목 리스트 파일에 쓰기
    
def make_request(term_of_bar: str="3", term_of_line: str="5"):
    f_symbol = open(f_data_address+"symbol.txt", "r")
    symbol_list = f_symbol.readlines()
    f_symbol.close()
    for idx, symbol in enumerate(symbol_list):
        symbol_list[idx] = symbol.strip()
    
    f_request = open(f_data_address+"request.txt", "w")
    f_request.write("")
    for symbol in symbol_list:
        req: str = symbol+"\n"+term_of_bar+"\n"
        f_request.write(req)
    f_request.write(term_of_line)
    f_request.close()

    return symbol_list


class Status:
    max_budget: float = api.get_balance(msg=False)*0.7

    def __init__(self, code: str="005930", file_name: str="0", short_ratio: float=0.4, long_ratio: float=0.4):
        self.code: str = code
        self.file_name: str = file_name

        self.short_ratio: float = short_ratio
        self.long_ratio: float = long_ratio

        self.decision: bool = False
        self.long: bool = False
        self.short: bool = False

        self.long_line: float = 0.0
        self.short_line: float = 0.0
        self.qty_score: float = 0.0

        self.budget: float = 0.0

        self.bought: bool = False
        self.bought_qty: int = 0
        self.bought_price: float = 0.0
        self.qty_to_buy: int = 0
        self.qty_to_sell: int = self.bought_qty

        self.stop_loss: bool = False


def get_trade_line(attributes: dict, status: Status, trading: str="short"):
    if trading == "short":
        f_line = open(f_line_address+"support"+status.file_name+".txt", "r")
        trading_ratio: float = status.short_ratio
    else:
        f_line = open(f_line_address+"resistant"+status.file_name+".txt", "r")
        trading_ratio: float = status.long_ratio
    
    line_list = f_line.readlines()
    for idx, line in enumerate(line_list):
        line_list[idx] = line.strip()
    f_line.close()
    if "" in line_list:
        line_list.remove("")
    
    if len(line_list) >= 3:
        basis_line_list = list()
        for line in line_list:
            basis_line_list.append(float(line))
        
        basis_line: float = np.mean(basis_line_list)
        trading_line: float = basis_line*trading_ratio

        if trading == "short":
            attributes["short_line"] = trading_line
        else:
            attributes["long_line"] = trading_line

        if len(line_list) >= 4:
            f_line = open(f_line_address+"support"+status.file_name+".txt", "w")
            f_line.write("")
            f_line.close()

        return trading_line
    else:
        return 0.0

def get_qty_score(attributes, status: Status):
    price = api.get_current_price(status.code)
    attributes["qty_score"] = price/attributes["long_line"]

def get_decision(queue, status: Status):
    attributes = {
        'decision': False,
        'long': False,
        'short': False,
        'long_line': 0.0,
        'short_line': 0.0,
        'qty_score': 0.0
    }
    #while attributes["decision"] == False:
    get_trade_line(attributes, status, "short")
    flag = get_trade_line(attributes, status, "long")

    if flag != 0.0:
        attributes["decision"] = True
        price = api.get_current_price(status.code)
        if price <= attributes["short_line"]:
            attributes["short"] = True
        elif price >= attributes["long_line"]:
            attributes["long"] = True
            get_qty_score(attributes, status)
    else:
        attributes["decision"] = False
    
    queue.put(attributes)
    #print(f"Debug: {status.code} - Decision: {attributes['decision']}, Long: {attributes['long']}, Short: {attributes['short']}, short_line: {attributes['short_line']}, long_line: {attributes['long_line']}, qty_score: {attributes['qty_score']}")

def get_qty_to_buy(status_li: list=[]):
    Status.max_budget = api.get_balance(msg=False)*0.7
    status_li.sort(key=lambda x: x.qty_score, reverse=True)
    long_list = list()
    for status in status_li:
        if status.long:
            long_list.append(status)
    
    num_of_status: int = len(long_list)
    for idx, status in enumerate(long_list):
        rank = idx+1
        status.budget = Status.max_budget*(num_of_status+1-rank)/(num_of_status*(num_of_status+1)/2)
    
    for idx, status in enumerate(long_list):
        price = api.get_current_price(status.code)
        if status.budget < price: 
            shortfall = price - status.budget
            if idx < len(long_list)-1 and long_list[idx+1].budget >= shortfall:
                status.budget = price
                long_list[idx+1].budget -= shortfall
        status.qty_to_buy = status.budget//price
        #print(f"Debug: {status.code} - score: {status.qty_score}, budget: {status.budget}, price:{price}, qty to buy: {status.qty_to_buy}")


try:
    api.open_config_file(False)
    refresh_count = False
    
    while True:
        time_now = datetime.datetime.now()
        time_close = time_now.replace(hour=15, minute=23, second=0, microsecond=0)
        
        if time_now < time_close:
            symbol_to_keep = {}
            term_of_bar = "2"
            term_of_line = "3"
            symbol_list = make_request(term_of_bar, term_of_line)
            num_of_symbol = len(symbol_list)

            if refresh_count == False:
                status_instances = [Status(symbol_list[i], str(i), 0.4, 0.4) for i in range(len(symbol_list))]
            else:
                file_name_list_of_keep = list(symbol_to_keep.values())
                for symbol in symbol_list:
                    if symbol in symbol_to_keep:
                        continue
                    else:
                        for i in range(num_of_symbol):
                            if i not in file_name_list_of_keep:
                                status_instances.append(Status(symbol, str(i), 0.4, 0.4))

            with Manager() as manager:
                status_queues = [manager.Queue() for _ in range(len(symbol_list))]

                while True:
                    procs = []
                    for idx, status_instance in enumerate(status_instances):
                        proc = Process(target=get_decision, args=(status_queues[idx], status_instance))
                        procs.append(proc)
                        proc.start()

                    for proc in procs:
                        proc.join()

                    for idx, status_instance in enumerate(status_instances):
                        attributes = status_queues[idx].get()
                        status_instance.decision = attributes['decision']
                        status_instance.long = attributes['long']
                        status_instance.short = attributes['short']
                        status_instance.long_line = attributes['long_line']
                        status_instance.short_line = attributes['short_line']
                        status_instance.qty_score = attributes['qty_score']
                        #status_instance.budget = attributes['budget']
                        #status_instance.qty_to_buy = attributes['qty_to_buy']
                        #rint(status_instance.decision, status_instance.long, status_instance.short, status_instance.long_line, status_instance.short_line, status_instance.qty_score)
                    
                    get_qty_to_buy(status_instances)

                    #for status_instance in status_instances:
                        #print(status_instance.code, status_instance.budget, status_instance.qty_to_buy)

                    for idx, status_instance in enumerate(status_instances):
                        if status_instance.decision:
                            if status_instance.long:
                                api.buy(status_instance.code, str(status_instance.qty_to_buy))
                                status_instance.long = False
                                status_instance.bought = True
                                status_instance.bought_qty += status_instance.qty_to_buy
                            elif status_instance.short:
                                status_instance.stop_loss = True
                                if status_instance.bought:
                                    api.sell(status_instance.code, str(status_instance.qty_to_sell))
                                    status_instance.bought = False
                                    status_instance.bought_qty = 0
                                else:
                                    pass
                    time.sleep(1)

                    stop_loss_count = 0
                    for status_instance in status_instances:
                        if status_instance.stop_loss:
                            stop_loss_count += 1
                    if stop_loss_count >= num_of_symbol//2:
                        break
                    
                    #break    # 임시로 1번만 돌리기
                
                #status_instances[2].bought = False    # 테스트를 위한 임시 코드
                #status_instances[2].stop_loss = True    # 테스트를 위한 임시 코드
                refresh_count = 0
                for status_instance in status_instances:
                    if status_instance.bought==True or status_instance.stop_loss==False:
                        symbol_to_keep[status_instance.code] = status_instance.file_name
                    if status_instance.stop_loss:
                        status_instances.remove(status_instance)
                        refresh_count += 1
                
                if refresh_count == num_of_symbol:
                    refresh_symbol({}, num_of_symbol, 0)
                    #print(f"degug: keep: {symbol_to_keep}, num_of_symbol: {num_of_symbol}, refresh_count: {refresh_count}")
                elif refresh_count > 0:
                    refresh_symbol(symbol_to_keep, num_of_symbol, refresh_count)
                    #print(f"degug: keep: {symbol_to_keep}, num_of_symbol: {num_of_symbol}, refresh_count: {refresh_count}")
                elif refresh_count == 0:
                    #refresh_symbol(symbol_to_keep, num_of_symbol, 0)
                    #print(f"degug: keep: {symbol_to_keep}, num_of_symbol: {num_of_symbol}, refresh_count: {refresh_count}")
                    pass

                #print(f"Debug: - {status_instances[0].code} - Decision: {status_instances[0].decision}, Long: {status_instances[0].long}, Short: {status_instances[0].short}, short_line: {status_instances[0].short_line}, long_line: {status_instances[0].long_line}, stop_loss: {status_instances[0].stop_loss}, qty_score: {status_instances[0].qty_score}")
                
            #break    # 임시로 1번만 돌리기
        else:
            break

except Exception as e:
    api.send_message(api.DISCORD_WEBHOOK_URL, f"오류 발생{e}")
    time.sleep(1)