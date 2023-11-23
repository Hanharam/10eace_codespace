import requests
import json
import yaml
import datetime
import time
from multiprocessing import Process


def get_access_token():    # 접근 토큰 발급
    headers = {"content-type":"application/json"}
    body = {"grant_type":"client_credentials",
    "appkey":APP_KEY, 
    "appsecret":APP_SECRET}
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    ACCESS_TOKEN = res.json()["access_token"]
    return ACCESS_TOKEN

config_path_gcs = '/workspaces/codespaces-blank/project/stock/config.yaml'

with open(config_path_gcs, encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
ACCESS_TOKEN = ""
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_INFO_URL']
URL_BASE = _cfg['URL_BASE']
ACCESS_TOKEN = get_access_token()

def send_message(msg):    # discord 메시지 보내기
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)
    print(message)

def get_acml_volume(code: str="005930"):    # 일간 누적 거래량
    PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey":APP_KEY,
            "appSecret":APP_SECRET,
            "tr_id":"FHKST01010100"}
    params = {
    "fid_cond_mrkt_div_code":"J",
    "fid_input_iscd":code,
    }
    res = requests.get(URL, headers=headers, params=params)

    return int(res.json()['output']['acml_vol'])

def get_current_price(code: str="005930"):    # 현재가 조회
    PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey":APP_KEY,
            "appSecret":APP_SECRET,
            "tr_id":"FHKST01010100"}
    params = {
    "fid_cond_mrkt_div_code":"J",
    "fid_input_iscd":code,
    }
    res = requests.get(URL, headers=headers, params=params)
    return int(res.json()['output']['stck_prpr'])

def get_information(code: str="005930", term_of_bar: int=3, term_of_line: int=5, file_name: str="0"):    # 종목의 저점, 고점, 거래량, 지지선, 저항선 구하기
    bar = list()    # 봉
    low = 0    # 봉의 최저
    high = 0    # 봉의 최고
    f_data = open("/workspaces/codespaces-blank/project/stock/national/yj/data/data"+file_name+".txt", "a")    # 구한 정보를 저장할 파일 열기

    mmty_volume = 0    # 봉이 생성되는 동안의 거래량
    base = get_acml_volume(code)    # 현재까지의 누적 거래량(기준)

    end = time.time() + term_of_bar*30

    while time.time() <= end:    # 봉이 생성되는 시간 동안 현재가를 받아 가격봉 생성
        bar.append(get_current_price(code))
        acml = get_acml_volume(code)    # 현재까지의 누적 거래량(실시간)
        mmty_volume = acml-base    # 봉이 생성되는 동안의 거래량

    bar.sort()    # 오름차순 정렬
    low += bar[0]    # 최저가
    high += bar[-1]    # 최고가
    info = [low, high, mmty_volume]
    for i in range(3):
        data = str(info[i])+"\n"    # 저장할 정보
        f_data.write(data)    # 파일에 정보 쓰기
    f_data.close()    # 파일 닫기

    f_data = open("/workspaces/codespaces-blank/project/stock/national/yj/data/data"+file_name+".txt", "r")
    acml_data = f_data.readlines()    # 지지선을 구할 때인지 판단하기 위해 데이터 파일의 내용 읽기
    f_data.close()    # 파일 닫기
    if len(acml_data) >= term_of_line*3:    # 저지선을 구하는 조건
        get_support_resistant(code, term_of_line, file_name)    # 지지선 구하기

        f_data = open("/workspaces/codespaces-blank/project/stock/national/yj/data/data"+file_name+".txt", "w")    # 데이터 파일 초기화를 위해 파일 열기
        data = ""
        f_data.write(data)    # 데이터 파일 초기화
        f_data.close()    # 파일 닫기


def get_support_resistant(code: str="005930", num_of_bar: int=5, file_name: str="0"):    # 종목의 지지선 및 저항선 구하기
    support = 0    # 지지선
    resistant = 0    # 저항선
    f_data = open("/workspaces/codespaces-blank/project/stock/national/yj/data/data"+file_name+".txt", "r")    # 지지선 및 저항선을 구하기 위한 데이터를 얻기 위해 데이터 파일 열기
    acml_data = f_data.readlines()    # 현재까지 쌓인 데이터
    f_sup = open("/workspaces/codespaces-blank/project/stock/national/yj/line/support"+file_name+".txt", "a")    # 지지선 값을 저장할 파일 열기
    f_res = open("/workspaces/codespaces-blank/project/stock/national/yj/line/resistant"+file_name+".txt", "a")    # 저항선 값을 저장할 파일 열기

    for i in range(0, len(acml_data), 3):
        support += int(acml_data[i])    # 데이터 중 저점들의 합
        resistant += int(acml_data[i+1])    # 데이터 중 고점들의 합
    support /= num_of_bar    # 지지선
    resistant /= num_of_bar    #지저항선
    f_sup.write(str(support)+"\n")    # 지지선 값 파일에 쓰기
    f_res.write(str(resistant)+"\n")    # 저항선 값 파일에 쓰기

    send_message(code+" "+"support: "+str(support))    # 지지선 값 메시지로 보내기
    send_message(code+" "+"resistant: "+str(resistant))    # 저항선 값 메시지로 보내기
    
    f_data.close()    # 파일 닫기
    f_sup.close()    # 파일 닫기
    f_res.close()    # 파일 닫기


try:
    while True:
        time_now = datetime.datetime.now()    # 현재 시각
        time_end = time_now.replace(hour=15, minute=15, second=0, microsecond=0)    # 장이 끝나는 시각 = 프로그램 종료 시각

        if time_now < time_end:    # 장이 마칠 때까지 프로그램 실행
            f_req = open("/workspaces/codespaces-blank/project/stock/national/yj/data/request.txt", "r")    # 요청 사항 파일 열기
            req = f_req.readlines()    # 요청 사항 읽기
            f_req.close()    # 파일 닫기

            for i in range(len(req)):
                req[i] = req[i].strip()    # 요청 사항 내용 중 개행 문자 제거

            procs = []    # CPU 작업 리스트
            for i in range(0, len(req)-1, 2):    # 요청 사항 중 종목 코드에만 접근
                proc = Process(target=get_information, args=(req[i], int(req[i+1]), int(req[-1]), str(i//2)))    # 데이터 구하는 작업 병렬 수행
                procs.append(proc)
                proc.start()
            for proc in procs:
                proc.join()
            
            time_now = time_now = datetime.datetime.now()    # 작업 메시지 보낼 시간인지 알아보기 위해 현재 시각 받아오기
            flag: bool = False    # 1분 내에 반복적으로 메시지를 보내지 않도록 제어
            if (time_now.minute in [0, 20, 40]) and (flag==False):    # 정각, 20분, 40분에 작업 메시지 보내기
                for i in range(len(procs)-6, len(procs)):    # 최근 5개의 작업만 메시지로 보내기
                    send_message(procs[i])
                flag = True
            if time_now.minute not in [0, 20, 40]:    # 제어 변수 초기화
                flag = False

        else:
            break

except Exception as e:
    send_message(f"오류 발생{e}")
    time.sleep(1)