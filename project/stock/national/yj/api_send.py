import requests
import json
import datetime
import time
import yaml


f_data_address = "/home/ubuntu/code-server/project/stock/yj/data/"    # 파일 경로(접근 토근, 종목 리스트, 데이터 요청 리스트, 거래량)


def get_access_token(get_new_token: bool=False):
    if get_new_token:
        headers = {"content-type":"application/json"}
        body = {"grant_type":"client_credentials",
        "appkey":APP_KEY, 
        "appsecret":APP_SECRET}
        PATH = "oauth2/tokenP"
        URL = f"{URL_BASE}/{PATH}"
        res = requests.post(URL, headers=headers, data=json.dumps(body))
        ACCESS_TOKEN = res.json()["access_token"]

        f_access_token = open(f_data_address+"access_token.txt", "w")
        f_access_token.write("")
        f_access_token.write(ACCESS_TOKEN)
        f_access_token.close()
    else:
        f_access_token = open(f_data_address+"access_token.txt", "r")
        ACCESS_TOKEN = f_access_token.readline()
        f_access_token.close()

    return ACCESS_TOKEN

def open_config_file(get_new_token: bool=False):
    config_path_cs = '/home/coder/project/project/stock/config.yaml'
    config_path_lo = '/home/ubuntu/code-server/project/stock/config_kr.yaml'
    config_path_gcs = '/workspaces/10eace_codespace/project/stock/config.yaml'

    with open(config_path_lo, encoding='UTF-8') as f:
        _cfg = yaml.load(f, Loader=yaml.FullLoader)
    global APP_KEY, APP_SECRET, CANO, ACNT_PRDT_CD, DISCORD_WEBHOOK_URL, DISCORD_WEBHOOK_INFO_URL, DISCORD_WEBHOOK_SYMBOL_URL, URL_BASE, ACCESS_TOKEN
    APP_KEY = _cfg['APP_KEY']
    APP_SECRET = _cfg['APP_SECRET']
    CANO = _cfg['CANO']
    ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
    DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_URL']
    DISCORD_WEBHOOK_INFO_URL = _cfg['DISCORD_WEBHOOK_INFO_URL']
    DISCORD_WEBHOOK_SYMBOL_URL = _cfg['DISCORD_WEBHOOK_SYMBOL_URL']
    URL_BASE = _cfg['URL_BASE']
    ACCESS_TOKEN = get_access_token(get_new_token)


def send_message(webhook_url: str="", msg: str=""):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(webhook_url, data=message)
    print(message)
    
def hashkey(datas):
    """암호화"""
    PATH = "uapi/hashkey"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
    'content-Type' : 'application/json',
    'appKey' : APP_KEY,
    'appSecret' : APP_SECRET,
    }
    res = requests.post(URL, headers=headers, data=json.dumps(datas))
    hashkey = res.json()["HASH"]
    return hashkey

def get_current_price(code: str="005930"):
    """현재가 조회"""
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

def get_stock_balance():
    """주식 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8434R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    send_message(DISCORD_WEBHOOK_URL, f"====주식 보유잔고====")
    for stock in stock_list:
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = stock['hldg_qty']
            send_message(DISCORD_WEBHOOK_URL, f"{stock['prdt_name']}({stock['pdno']}): {stock['hldg_qty']}주")
            time.sleep(0.1)
    send_message(DISCORD_WEBHOOK_URL, f"주식 평가 금액: {evaluation[0]['scts_evlu_amt']}원")
    time.sleep(0.1)
    send_message(DISCORD_WEBHOOK_URL, f"평가 손익 합계: {evaluation[0]['evlu_pfls_smtl_amt']}원")
    time.sleep(0.1)
    send_message(DISCORD_WEBHOOK_URL, f"총 평가 금액: {evaluation[0]['tot_evlu_amt']}원")
    time.sleep(0.1)
    send_message(DISCORD_WEBHOOK_URL, f"=================")
    return stock_dict

def get_balance(msg: bool=True):    # 현금 잔고 조회
    PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8908R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "005930",
        "ORD_UNPR": "65500",
        "ORD_DVSN": "01",
        "CMA_EVLU_AMT_ICLD_YN": "Y",
        "OVRS_ICLD_YN": "Y"
    }
    res = requests.get(URL, headers=headers, params=params)
    cash = res.json()['output']['ord_psbl_cash']
    if msg:
        send_message(DISCORD_WEBHOOK_URL, f"주문 가능 현금 잔고: {cash}원")
    
    return float(cash)

def buy(code: str="005930", qty: str="1"):
    """주식 시장가 매수"""  
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": str(int(qty)),
        "ORD_UNPR": "0",
    }
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC0802U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(DISCORD_WEBHOOK_URL, f"[매수 성공]{str(res.json())}")
        return True
    else:
        send_message(DISCORD_WEBHOOK_URL, f"[매수 실패]{str(res.json())}")
        return False

def sell(code: str="005930", qty: str="1"):
    """주식 시장가 매도"""
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": qty,
        "ORD_UNPR": "0",
    }
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC0801U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(DISCORD_WEBHOOK_URL, f"[매도 성공]{str(res.json())}")
        return True
    else:
        send_message(DISCORD_WEBHOOK_URL, f"[매도 실패]{str(res.json())}")
        return False