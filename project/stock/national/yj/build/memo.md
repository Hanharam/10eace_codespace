## 현 상황  

- - -  

### info.py  
&rarr; 3분마다 가격봉을 생성하고 해당 봉의 최저, 최고, 거래량을 계속해서 업데이트  
&rarr; 그러다가 가격봉이 3개 쌓였을 때 지지선과 저항선을 구함  
&rarr; 이 과정을 계속 반복함  


### trading.py
&rarr; 프로그램이 시작하자마자, request 파일을 만듦  
&rarr; 그리고 무한루프를 돌며 종목마다 클래스를 생성하고 각 종목의 가격이 info.py가 구한 저항선의 일정 수준을 넘으면 long을 True, 지지선의 일정 수준 밑으로 내려가면 short를 True로 지정

<br/>  

## 해야할 것들  

- - -  

### 매매  
자, 각 종목의 클래스 변수에 따라 매수, 매도를 결정하면 매우 간단하고 좋을 것.  
매수는 이게 가능한데, 매도는 일단 사 놓은게 있어야 매도를 할 것 아닌가.  
아...  
멍청...ㅋ  
지지선의 일정 수준 밑으로 내려가면 매도도 맞기는 한데, 매수를 하지 않은 단계에서는 손절이다.  
즉, 해당 종목 자체를 떨군다.  
그리고 종목 리스트를 다시 짠다.  


그러면, 이를 위해 필요한 것은 매수를 한 종목을 기록할 리스트  
&rarr; 그런데... 이를 대충 buy함수를 호출한 다음에 해당 코드를 리스트에 추가할 수도 있겠지만,  
&rarr; 종목 클래스에 따로 클래스 변수를 만들어 buy함수를 호출한 다음에 해당 변수에 매수 여부를 기록하면 되지 않겠는가...  
&rarr; 그러면 따로 리스트를 만들지 않아도 되고, 매도를 할 때도 해당 변수의 매수 여부를 보고 판단하면 될 것  

<br/>  

자, 문제가 하나 더 있다.  
수량을 어떻게 정하지?  
매도 수량은 매수한 전량을 팔아버리면 그만...오... 매수한 수량을 기록하는 클래스 변수도 필요할 것 같다.  
매수 수량은 어떻게 정할까?  
1. 간단한 방법:  
    조건을 만족한 모든 종목에 대해서 동일한 예산을 할당
2. 복잡한 방법1:  
    각 종목의 이동 평균선 간격에 따라 이동 평균선 거리가 짧은 친구들에 더 많은 예산을 할당  
3. 복잡한 방법2:  
    저항선을 더 많이 넘어선 종목에 더 많은 예산을 할당
4. 복잡한 방법3:  
    거래량이 많은 종목에 더 많은 예산을 할당

<br/>  

자, 또 다른 문제가 있다  
장이 열려있는 중에, 종목들을 살펴보다가 손절할 종목이 보여서 손절을 한 다음에 다시 살펴볼 종목 리스트를 짜야 하는데, 이것이 프로그램을 따로 실행하기가 좀 그렇다.  
&rarr; 그래서 종목 리스트를 짜는 프로그램을 따로 돌리는 것은 장이 마감한 후에 하는 것으로 하고,  
&rarr; 이 로직을 따로 라이브러리로 만들어 trading.py에서 해당 라이브러리를 불러와 종목 리스트를 짜게 하는 것이 좋을 것 같다.

<br/>  

### 데이터  
trading.py에서 클래스를 적용하니 굉장히 편한 것 같다.  
&rarr; info.py에서도 클래스를 적용해보자.  
&rarr; 대공사ㅋ  


자, 일단 지금은 data 파일을 종목 별로 만들어 정보를 관리하고 있다.  
이를 클래스로 바꾸려고 한다.  
지지선, 저항선도 클래스 변수 안에 담을 거기는 한데, 일단 이 친구들은 trading.py에도 전달이 되어야 하므로 파일을 없애지는 않을 것  


그럼 또 하나 고민해야 할 것이 있는데...  
바로 get_information 함수이다.  
이 함수를 클래스 함수 즉, 메소드로 만들지, 아니면 그대로 둘지가 관건.
어케하지...?ㅋ


#### 그대로 함수로 둔다  
음....  
일단 클래스 변수에 가격값과 거래량, 지지선, 저항선 값을 모두 저장해야 하므로, 함수에 인자로 전달해야 할 변수가 좀 많아질 것.  
오... 탈락ㅋ


#### 메소드로 만든다  
일단 앞선 방법(그대로 두는)보다 전달해야 할 인자가 확 준다.  
클래스 메소드이기 때문에 바로 attribute에 접근할 수 있기 때문  
좋은데...?ㅋㅋㅋ  
개뿔...
안됨  
리스트가 이상하게 계속 초기화 됨...ㅋ  
리스트를 쓰지 않고 조져보자  
안됨ㅋㅋㅋㅋ  
문제를 찾았음  
클래스 문제가 아니라, multiprocessing문제였음  
process를 여러번 실행할 수 없으므로, 함수 자체에서 반복을 수행해야 할 것 같다.  
자, 그럼 어떻게, 얼마나 반복해야 하는가?  
원래는 무한반복이다....?ㅋㅋㅋㅋ 조짐ㅋㅋㅋㅋ  
무한루프를 하면 조질 게 분명하니... 지지선과 저항선이 특정 개수만큼 쌓였을 때마다 process를 초기화 해주는 걸로 하자  
해결 봤다.  
함수내 루프는 지지선이 생길 때까지 반복하게 설정함  
&rarr; 지지선이 하나라도 생기면 process 초기화하고 새로운 process 시작  
&rarr; process 하나당 지지선 및 저항선 1개 생성

<br/>

### 매매  
자, 다시 매매ㅋㅋㅋㅋ
데이터 파트에서 수정한 것처럼 매매파트도 고쳐야 함  
일단 메소드 호출 부분은 데이터 파트처럼 고쳐놓음  
&rarr; 메소드 내 루프 알고리즘을 짜야 함  
&rarr; 어떻게 반복할까?  
음...근데...이거...  
반복할 필요가 없음ㅋㅋㅋㅋ  
데이터를 받아오는 것도 아니고, 그냥 살지 말지를 판단하는 메소드라 변수가 죄다 초기화 되도 상관이 없음ㅋㅋㅋㅋ  
근데 문제가 하나 있음...  
클래스 인스턴스 변수 중에 bought_qty는 계속 살아있어야 함  
근데 메소드를 반복하면 bought_qty가 초기화 되나...?  
메소드에서 bought_qty를 건들지는 않는다...  
그래도 혹시 모르니 바꾸는게 나을 것 같다.  
get_decision 메소드를 그냥 함수로 바꾸겠다.