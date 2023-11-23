import sys
sys.path.append('/workspaces/codespaces-blank/project/stock/national/yj')

import api
import get_symbol as gsym
import datetime
import time
import numpy as np
from multiprocessing import Process, Manager

api.open_config_file(False)

def refresh_symbol():    # 종목 리스트 갱신
    gsym.open_config_file(False)    # 종목 리스트 파일 열기
    gsym.initialize_symbol()    # 종목 리스트 초기화
    symbol_list = gsym.get_entire_symbol()    # 전체 종목 리스트 가져오기
    gsym.get_symbol_by_distance(symbol_list)    # 이동 평균선 간격에 따른 종목 선별
    final_symbol = gsym.get_final_symbol_list()    # 최종 선별된 종목 리스트 가져오기
    gsym.write_symbol_file(final_symbol)    # 최종 선별된 종목 리스트 파일에 쓰기

def make_request(term_of_bar: str="3", term_of_line: str="5"):
    f_symbol = open("/workspaces/codespaces-blank/project/stock/national/yj/data/symbol.txt", "r")
    symbol_list = f_symbol.readlines()
    f_symbol.close()
    for symbol in symbol_list:
            symbol = symbol.strip()
    #symbol_list.remove("")
    
    f_request = open("/workspaces/codespaces-blank/project/stock/national/yj/data/request.txt", "w")
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
        self.qty_to_buy: int = 0
        self.qty_to_sell: int = self.bought_qty


def get_trade_line(attributes: dict, status: Status, trading: str="short"):
    if trading == "short":
        f_line = open("/workspaces/codespaces-blank/project/stock/national/yj/line/support"+status.file_name+".txt", "r")
        trading_ratio: float = status.short_ratio
    else:
        f_line = open("/workspaces/codespaces-blank/project/stock/national/yj/line/resistant"+status.file_name+".txt", "r")
        trading_ratio: float = status.long_ratio
    
    line_list = f_line.readlines()
    for line in line_list:
        line = line.strip()
    f_line.close()
    
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
            f_line = open("/workspaces/codespaces-blank/project/stock/national/yj/line/support"+status.file_name+".txt", "w")
            f_line.write("")
            f_line.close()

        return trading_line
    else:
        return 0.0

def get_decision(attributes: dict, status: Status):
    while attributes["decision"] == False:
        flag = get_trade_line(attributes, status, "short")
        get_trade_line(attributes, status, "long")

        if flag != 0.0:
            price = api.get_current_price(attributes["code"])
            if price <= attributes["short_line"]:
                attributes["decision"] = True
                attributes["short"] = True
            elif price >= attributes["long_line"]:
                attributes["decision"] = True
                attributes["long"] = True
        else:
            attributes["decision"] = False

def get_qty_score(status: Status):
    price = api.get_current_price(status.code)
    status.qty_score = price/status.long_line

def get_qty_to_buy(status_li: list=[]):
    Status.max_budget = api.get_balance(msg=False)*0.7
    num_of_status: int = len(status_li)
    status_li.sort(key=lambda x: x.qty_score, reverse=True)
    for idx, status in enumerate(status_li):
        rank = idx+1
        status.budget = Status.max_budget*(num_of_status+1-rank)/(num_of_status*(num_of_status+1)/2)
    
    for status in status_li:
        price = api.get_current_price(status.code)
        status.qty_to_buy = int(status.budget/price)


term_of_bar = "3"
term_of_line = "3"
symbol_list = make_request(term_of_bar, term_of_line)

status_instances = [Status(symbol_list[i], str(i), 0.4, 0.4) for i in range(len(symbol_list))]

with Manager() as manager:
    shared_attributes = manager.dict()

    for i in range(len(symbol_list)):
        shared_attributes[i] = {'decision': False, 'long': False, 'short': False, 'long_line': 0.0, 'short_line': 0.0, 'qty_score': 0.0, 'budget': 0.0, 'qty_to_buy': 0}

    while True:
        procs = []
        for idx, status_instance in enumerate(status_instances):
            proc = Process(target=get_decision, args=(shared_attributes[idx], status_instance))
            procs.append(proc)
            proc.start()
        for proc in procs:
            proc.join()

        for idx, status_instance in enumerate(status_instances):
            attributes = shared_attributes[idx]
            status_instance.decision = attributes['decision']
            status_instance.long = attributes['long']
            status_instance.short = attributes['short']
            status_instance.long_line = attributes['long_line']
            status_instance.short_line = attributes['short_line']
            status_instance.qty_score = attributes['qty_score']
            status_instance.budget = attributes['budget']
            status_instance.qty_to_buy = attributes['qty_to_buy']
        
        for idx, status_instance in enumerate(status_instances):
            if status_instance.decision:
                if status_instance.long:
                    #api.buy(symbol_list[idx], str(status_instance.qty_to_buy))
                    print(status_instance.qty_to_buy)
                    status_instance.bought = True
                    status_instance.bought_qty += status_instance.qty_to_buy
                elif status_instance.short and status_instance.bought:
                    #api.sell(symbol_list[idx], str(status_instance.qty_to_sell))
                    status_instance.bought = False
                    status_instance.bought_qty = 0
                    #refresh_symbol()
                    #make_request(term_of_bar, term_of_line)
            #time.sleep(1)