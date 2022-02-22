import time
import pyupbit
import datetime as dt
from ticker import Ticker
import warnings

warnings.filterwarnings('ignore')
access = "Oug97pOTCd6xN12mREWTo9GTQcmkzhMtnoW2Wqyo"          # 본인 값으로 변경
secret = "6IUBTLNU02rSGQux5cIMW11W05WnoW5rRKxxSE6Z"          # 본인 값으로 변경

baseday = dt.datetime.now()
current_ticker = Ticker('KRW-EOS')

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_ask_price(ticker):  # 현재 매수가.
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def get_current_bid_price(ticker):  #현재 매도가
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["bid_price"]


# 로그인
upbit = pyupbit.Upbit(access, secret)
print("Autotrader init.. ", flush=True)
# 자동매매 시작
while  True :
    print("best K, base simmulation.....", flush=True)
    current_ticker.bestValue()
    current_ticker.make_df()
    print(f'ticker= {current_ticker.name}, k = {current_ticker.k}, base = {current_ticker.base}, target_price = {current_ticker.target_price}', flush=True)
    current_ticker.get_start_time()
    print(f'Day START!..{current_ticker.start_time:%Y-%m-%d %H:%M:%S} ~ {current_ticker.end_time::%Y-%m-%d %H:%M:%S},  nextday : {current_ticker.nextday:%Y-%m-%d %H:%M:%S}', flush=True)
    
    current_time = dt.datetime.now()
    loop_cnt = 0
    while current_time < current_ticker.nextday :
        try:
            if not current_ticker.isgood :
                print(f'{current_ticker.name} not good situation. may be not ascending ...',flush=True)
                time.sleep(600)   # 약 5분대기
                continue

            loop_cnt +=1
            if  current_ticker.start_time < current_time < current_ticker.end_time :
                current_price = get_current_ask_price(current_ticker.name)
                if loop_cnt >= 10 :   # 운영모드로 가면 충분히 크게 바꿀것..
                    print(f'Now : {current_time:%Y-%m-%d %H:%M:%S}, start : {current_ticker.start_time:%Y-%m-%d %H:%M:%S}, end : {current_ticker.end_time:%Y-%m-%d %H:%M:%S}, target:{current_ticker.target_price:,.2f}, current:{current_price:,}', flush=True)
                    loop_cnt = 0
                if current_ticker.target_price < current_price:
                    krw = get_balance("KRW")
                    print(f'get_balance(KRW): {krw}', flush=True)
                    krw = 0
                    if krw > 5000:
                        ret = upbit.buy_limit_order(current_ticker.name, current_price, (krw*0.9995)//current_price )
                        print(f'buy_limit_order {current_ticker.name}, {krw*0.9995:.2f}', flush=True)
                        print(f'buy_limit_order ret = {ret}' , flush=True)
            else:
                btc = get_balance(current_ticker.currency)
                print(f'get_balance(BTC): {btc}', flush=True)
                current_price = get_current_bid_price(current_ticker.name)
                if btc > ( 5000 / current_price) :
                    ret = upbit.sell_limit_order(current_ticker.name, current_price, (btc*0.9995)//current_price )
                    print(f'sell_limit_order {current_ticker.name}, {btc*0.9995:.2f}', flush=True)
                    print(f'sell_limit_order ret = {ret}' , flush=True)
            time.sleep(1)
        except Exception as e:
            print(e, flush=True)
            time.sleep(1)

        current_time = dt.datetime.now()

