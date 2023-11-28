import api
import datetime
import time
from multiprocessing import Process


f_data_address = "/home/ubuntu/code-server/project/stock/yj/data/"    # 파일 경로(접근 토근, 종목 리스트, 데이터 요청 리스트, 거래량)
f_line_address = "/home/ubuntu/code-server/project/stock/yj/line/"    # 파일 경로(저항선, 지지선)

class Stock_Info:
    def __init__(self, code: str="005930", term_of_bar: int=3, term_of_line: int=5, iteration: int=4, file_name: str="0"):
        self.code: str = code    # 종목 코드
        self.term_of_bar: int = term_of_bar    # 봉 생성 시간(분)
        self.term_of_line: int = term_of_line    # 지지선 및 저항선을 구할 때 필요한 봉의 개수
        self.iteration: int = iteration    # 반복 횟수
        self.file_name: str = file_name    # 파일 이름
        self.pr_low = list()    # 저점 리스트
        self.pr_high = list()    # 고점 리스트
        self.volume = 0    # 거래량
        self.support = 0    # 지지선
        self.resistant = 0    # 저항선

    def get_information(self):    # 종목의 저점, 고점, 거래량, 지지선, 저항선 구하기
        while self.support == 0:    # 지지선 및 저항선이 구해질 때까지 반복
            bar = list()    # 가격봉
            mmty_volume = 0    # 봉이 생성되는 동안의 거래량
            base = api.get_acml_volume(self.code)    # 현재까지의 누적 거래량(기준)
            end = time.time() + self.term_of_bar*60

            while time.time() <= end:    # 봉이 생성되는 시간 동안 현재가를 받아 가격봉 생성
                bar.append(api.get_current_price(self.code))
                acml = api.get_acml_volume(self.code)    # 현재까지의 누적 거래량(실시간)
                mmty_volume = acml-base    # 봉이 생성되는 동안의 거래량

            bar.sort()    # 오름차순 정렬
            self.pr_low.append(bar[0])    # 최저가를 리스트에 추가
            self.pr_high.append(bar[-1])    # 최고가를 리스트에 추가
            self.volume = mmty_volume    # 거래량

            f_volume = open(f_data_address+"volume"+self.file_name+".txt", "a")    # 거래량을 저장할 파일 열기
            f_volume.write(str(self.volume)+"\n")    # 거래량 파일에 쓰기
            f_volume.close()    # 파일 닫기

            if len(self.pr_low) >= self.term_of_line:    # 지지선 및 저항선을 구하는 조건
                self.get_support_resistant()    # 지지선 및 저항선 구하기

    def get_support_resistant(self):    # 종목의 지지선 및 저항선 구하기
        self.support = 0    # 지지선 초기화
        self.resistant = 0    # 저항선 초기화

        for i in range(len(self.pr_low)):    # 저점 리스트의 길이만큼 반복
            self.support += int(self.pr_low[i])    # 데이터 중 저점들의 합
            self.resistant += int(self.pr_high[i])    # 데이터 중 고점들의 합
        self.support /= self.term_of_line    # 지지선
        self.resistant /= self.term_of_line    #저항선

        self.pr_low = list()    # 저점 리스트 초기화
        self.pr_high = list()    # 고점 리스트 초기화

        f_sup = open(f_line_address+"support"+self.file_name+".txt", "a")    # 지지선 값을 저장할 파일 열기
        f_res = open(f_line_address+"resistant"+self.file_name+".txt", "a")    # 저항선 값을 저장할 파일 열기
        f_sup.write(str(self.support)+"\n")    # 지지선 값 파일에 쓰기
        f_res.write(str(self.resistant)+"\n")    # 저항선 값 파일에 쓰기
        f_sup.close()    # 파일 닫기
        f_res.close()    # 파일 닫기

        api.send_message(api.DISCORD_WEBHOOK_INFO_URL, self.code+" "+"support: "+str(self.support))    # 지지선 값 메시지로 보내기
        api.send_message(api.DISCORD_WEBHOOK_INFO_URL, self.code+" "+"resistant: "+str(self.resistant))    # 저항선 값 메시지로 보내기


try:
    api.open_config_file(True)    # 설정 파일 열기
    
    while True:
        time_now = datetime.datetime.now()    # 현재 시각
        time_close = time_now.replace(hour=15, minute=20, second=0, microsecond=0)    # 장이 끝나는 시각 = 프로그램 종료 시각

        if time_now < time_close:    # 장이 마칠 때까지 프로그램 실행
            f_req = open(f_data_address+"request.txt", "r")    # 요청 사항 파일 열기
            req = f_req.readlines()    # 요청 사항 읽기
            f_req.close()    # 파일 닫기
            for idx, r in enumerate(req):
                    req[idx] = r.strip()    # 요청 사항 내용 중 개행 문자 제거

            info = list()    # 종목 정보 리스트
            for i in range(0, len(req)-1, 2):
                info.append(Stock_Info(req[i], int(req[i+1]), int(req[-2]), 4, str(i//2)))    # 각 종목에 대한 정보 클래스 인스턴스 생성

            procs = []    # CPU 작업 리스트
            for i in range(0, len(req)-1, 2):    # 요청 사항 중 종목 코드에만 접근
                proc = Process(target=info[i//2].get_information)    # 데이터 구하는 작업 병렬 수행
                procs.append(proc)
                proc.start()
            for proc in procs:
                proc.join()
            
            time_now = time_now = datetime.datetime.now()    # 작업 메시지 보낼 시간인지 알아보기 위해 현재 시각 받아오기
            flag: bool = False    # 1분 내에 반복적으로 메시지를 보내지 않도록 제어
            if (time_now.minute in [0, 20, 40]) and (flag==False):    # 정각, 20분, 40분에 작업 메시지 보내기
                for i in range(len(procs)-6, len(procs)):    # 최근 5개의 작업만 메시지로 보내기
                    api.send_message(api.DISCORD_WEBHOOK_INFO_URL, procs[i])
                flag = True
            if time_now.minute not in [0, 20, 40]:    # 제어 변수 초기화
                flag = False

        else:
            break

except Exception as e:
    api.send_message(api.DISCORD_WEBHOOK_INFO_URL, f"오류 발생{e}")
    time.sleep(1)