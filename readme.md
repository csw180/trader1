변동성 돌파전략을 이용한 비트코인 자동매매 프로그램              
===============================================


구성
------------------------------------------
1. autotrader.py : main program             
2. upbit_trade.py : 잔고와 매수매도 주문을 처리하는 메서드 보유           
3. ticker.py : 개별종목에 해당하는 element class (Ticker class)            

기존의 전력과 다른 전력을 감안한 부문
-------------------------------------------
K 값을 이용하여 range를 구할때  (고가-저가)*K  대신 (고가-종가)*K 로 수정하고 양봉 일 경우만 대상으로 함
일봉상 5이평선이 우상향일것
프로그램기동시 고가가 목표가를 이미 넘어서 있는 경우는 대상에서 제외

Ubuntu 서버 명령어 주요 명령어 정리
------------------------------------------          
1. (*추가)한국 기준으로 서버 시간 설정: sudo ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime      
2.  현재 경로 상세 출력: ls -al                      
3. 경로 이동: cd 경로
4. vim 에디터로 파일 열기: vim bitcoinAutoTrade.py
5. vim 에디터 입력: i
6. vim 에디터 저장: :wq!
7. 패키지 목록 업데이트: sudo apt update
8. pip3 설치: sudo apt install python3-pip
9. pip3로 pyupbit 설치: pip3 install pyupbit
10. 백그라운드 실행: nohup python3 bitcoinAutoTrade.py > output.log &
11. 실행되고 있는지 확인: ps ax | grep .py
12. 프로세스 종료(PID는 ps ax | grep .py를 했을때 확인 가능): kill -9 PID
13. git clone https://github.com/csw180/trader1.git
14. nohup python3 autotrader.py > output.log &
15. ssh -i "romanticCoder.pem" ubuntu@ec2-18-205-238-89.compute-1.amazonaws.com
