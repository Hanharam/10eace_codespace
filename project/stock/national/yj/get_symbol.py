import api
import requests
import json
import yaml
import datetime
import time
import pandas as pd
from urllib import request
from bs4 import BeautifulSoup
import FinanceDataReader as fdr
from multiprocessing import Process

def open_config_file(get_new_token: bool=False):
    api.open_config_file(get_new_token)    # 설정 파일 열기

def get_data(code: str='252670'):    # finance-datareader로 일정 기간 내 종목 데이터 가져오기
    time_now = datetime.datetime.now()
    period = time_now-datetime.timedelta(days=200)    # 200일 전부터 오늘까지의 데이터 가져오기
    period = period.strftime('%Y-%m-%d')
    data = fdr.DataReader(code, period)

    return data

def initialize_symbol():    # 종목 리스트 초기화
    f_symbol = open("/workspaces/codespaces-blank/project/stock/national/yj/data/symbol.txt", "w")
    f_symbol.write("")    # 종목 리스트 초기화하고 프로그램 시작
    f_symbol.close()

def read_symbol_file():
    f_symbol = open("/workspaces/codespaces-blank/project/stock/national/yj/data/symbol.txt", "r")
    symbol_list = f_symbol.readlines()
    f_symbol.close()
    for idx, symbol in enumerate(symbol_list):
        symbol_list[idx] = symbol.strip()
    
    return symbol_list

def get_entire_symbol():
    url = "https://kr.investing.com/etfs/south-korea-etfs"    # investing.com에서 국내 etf 종목 코드 가져올 것
    user_agent_fox84 = 'Mozilla/5.0 (X11; Ubuntu 20.04; Linux arm; rv:99.0) Gecko/20100101 Firefox/99.0'
    user_agent_fox99 = 'Mozilla/5.0 (X11; Ubuntu 20.04; Linux arm; rv:99.0) Gecko/20100101 Firefox/99.0'
    user_agent_chrome = 'Mozilla/5.0 (X11; Ubuntu 20.10; Linux x86_64) AppleWebKit/537.36.0 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36.0'

    headers = {'User-Agent':user_agent_fox84}
    req = request.Request(url, data=None, headers=headers)
    fp = request.urlopen(req)
    source = fp.read()
    fp.close()

    html = BeautifulSoup(source, "html.parser")

    symbol_source = html.find_all('td', attrs={'class':'left symbol'})

    symbol_list = list()
    for sym in symbol_source:
        symbol_list.append(sym.get_text())    # 전체 etf 종목 코드 가져오기

    symbol_to_remove = list()    # 종목 코드 중 한국투자증권 api를 통해 구매를 시도할 때 오류가 나는 코드(etn 종목 코드)를 모을 list
    for sym in symbol_list:
        for i in sym:
            if i.isalpha():    # etn 종목 코드는 알파벳이 있는 코드이므로 종목 코드 내에 알파벳이 있는지 확인
                symbol_to_remove.append(sym)    # 알파벳이 있는 종목 코드는 제거할 종목 리스트에 추가
    for sym in symbol_to_remove:    # 제거할 종목 리스트를 순회하며 etn 종목이 종목 리스트에 있으면 종목 리스트에서 해당 종목 제거
        if sym in symbol_list:
            symbol_list.remove(sym)
    
    return symbol_list

def get_distance_of_MovingAverage(code: str="005930", period: list=[5, 20, 120], col: str="Close", distance: float=10.0):    # 이동 평균선 간의 간격을 판단하여 기준을 만족하는 종목은 파일에 쓰기
    data = get_data(code)
    
    ma = list()
    for i in range(3):    # 이동 평균선 구하기
        data['ma_'+str(period[i])] = data[col].rolling(period[i]).mean()
        ma.append(float(data['ma_'+str(period[i])][-1]))
    
    f_symbol = open("/workspaces/codespaces-blank/project/stock/national/yj/data/symbol.txt", "a")
    if abs(ma[0]-ma[1])<=distance and abs(ma[1]-ma[2])<=distance:    # 이동 평균선 간격이 일정한 범위 내에 있으면 해당 종목 파일에 쓰기
        f_symbol.write(code+"\n")
    f_symbol.close()

def get_symbol_by_distance(symbol_list: list=[]):
    procs = []
    for sym in symbol_list:    # 병렬처리로 각 종목 코드에 대해 이동 평균선 간격 판단
        proc = Process(target=get_distance_of_MovingAverage, args=(sym, [5, 20, 120], "Close", 50.0))
        procs.append(proc)
        proc.start()
    for proc in procs:
        proc.join()

def get_trash_symbol():    # 거래량이 없는 쓸모없는 종목 리스트
    f_symbol = open("/workspaces/codespaces-blank/project/stock/national/yj/data/symbol.txt", "r")
    symbol_list = f_symbol.readlines()
    f_symbol.close()
    for idx, symbol in enumerate(symbol_list):
        symbol_list[idx] = symbol.strip()
    
    trash_list = list()
    for symbol in symbol_list:
        if api.get_acml_volume(symbol) == 0:
            trash_list.append(symbol)
        else:
            continue
    
    return trash_list

def get_final_symbol_list():    # 최종 선별된 종목 리스트
    trash_list = get_trash_symbol()
    symbol_list = read_symbol_file()

    for trash in trash_list:
        if trash in symbol_list:
            symbol_list.remove(trash)
    
    return symbol_list

def write_symbol_file(symbol_list: list=[]):    # 최종 선별된 종목 리스트 파일에 쓰기
    f_symbol = open("/workspaces/codespaces-blank/project/stock/national/yj/data/symbol.txt", "w")
    for symbol in symbol_list:
        f_symbol.write(symbol+"\n")
    f_symbol.close()


if __name__ == "__main__":
    try:
        open_config_file(False)    # 설정 파일 열기

        initialize_symbol()    # 종목 리스트 초기화

        symbol_list = get_entire_symbol()    # 전체 종목 리스트 가져오기

        get_symbol_by_distance(symbol_list)    # 이동 평균선 간격에 따른 종목 선별

        final_symbol = get_final_symbol_list()    # 최종 선별된 종목 리스트 가져오기

        write_symbol_file(final_symbol)    # 최종 선별된 종목 리스트 파일에 쓰기

        f_symbol = open("/workspaces/codespaces-blank/project/stock/national/yj/data/symbol.txt", "r")
        symbol_list = f_symbol.readlines()
        f_symbol.close()
        api.send_message(api.DISCORD_WEBHOOK_SYMBOL_URL, "내일 매수할 종목 리스트")
        for idx, symbol in enumerate(symbol_list):
            symbol_list[idx] = symbol.strip()
            api.send_message(api.DISCORD_WEBHOOK_SYMBOL_URL, symbol)
        api.send_message(api.DISCORD_WEBHOOK_SYMBOL_URL, "----------------------------")


    except Exception as e:
        api.send_message(api.DISCORD_WEBHOOK_SYMBOL_URL, f"오류 발생{e}")
        time.sleep(1)