import time
import pyupbit
import datetime as dt
import XnBase


access = "Oug97pOTCd6xN12mREWTo9GTQcmkzhMtnoW2Wqyo"          # 본인 값으로 변경
secret = "6IUBTLNU02rSGQux5cIMW11W05WnoW5rRKxxSE6Z"          # 본인 값으로 변경

k = 0.5
base = 21
current_ticker = 'KRW-EOS'
currency = current_ticker[-3:]
baseday = dt.datetime.now()


def get_target_price(ticker, k,base):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = XnBase.get_ohlcv_custom(ticker,20,base)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(-1)
    target_price = df.iloc[0]['target'] 
    return target_price

def get_start_time(base) :
    basetime = dt.datetime.now()

    start_time = basetime.replace(hour=base,minute=0,second=0)
    if start_time > basetime :
        nextday = start_time
        end_time = start_time - dt.timedelta(seconds=10)
        start_time = start_time - dt.timedelta(days=1)
        
    else :
        nextday = start_time + dt.timedelta(days=1)
        end_time = start_time + dt.timedelta(days=1) - dt.timedelta(seconds=10)

    # print(f'get_start_time:start_time = {start_time}, end_time = {end_time}, nextday={nextday}', flush=True)
    return start_time, end_time, nextday

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

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

# 로그인
XnBase.current_ticker = current_ticker
print(XnBase.current_ticker)

upbit = pyupbit.Upbit(access, secret)

print("Autotrader init.. ", flush=True)
# 자동매매 시작
while  True :
    print("best K, base simmulation.....", flush=True)
    k , base = XnBase.bestValue()
    print(f'k = {k}, base = {base}', flush=True)
    start_time, end_time, nextday  = get_start_time(base)
    print(f'Day START!..{start_time:%Y-%m-%d %H:%M:%S} ~ {end_time::%Y-%m-%d %H:%M:%S},  nextday : {nextday:%Y-%m-%d %H:%M:%S}', flush=True)

    target_price = get_target_price(current_ticker, k,base)
    print(f'target_price = {target_price}', flush=True)
    current_time = dt.datetime.now()
    loop_cnt = 0
    while current_time < nextday :
        try:
            loop_cnt +=1
            if start_time < current_time < end_time :
                current_price = get_current_price(current_ticker)
                if loop_cnt >= 10 :   # 운영모드로 가면 충분히 크게 바꿀것..
                    print(f'Now : {current_time:%Y-%m-%d %H:%M:%S}, start : {start_time:%Y-%m-%d %H:%M:%S}, end : {end_time:%Y-%m-%d %H:%M:%S}, target:{target_price:,.2f}, current:{current_price:,}', flush=True)
                    loop_cnt = 0
                if target_price < current_price:
                    krw = get_balance("KRW")
                    print(f'get_balance(KRW): {krw}', flush=True)
                    if krw > 5000:
                        print(f'buy_market_order {current_ticker}, {krw*0.9995:.2f}', flush=True)
                    #    upbit.buy_market_order(current_ticker, krw*0.9995)
            else:
                btc = get_balance(currency)
                print(f'get_balance(BTC): {btc}', flush=True)
                if btc > ( 5000 / current_price) :
                    print(f'sell_market_order {current_ticker}, {btc*0.9995:.2f}', flush=True)
                    upbit.sell_market_order(current_ticker, btc*0.9995)
            time.sleep(1)
        except Exception as e:
            print(e, flush=True)
            time.sleep(1)

        current_time = dt.datetime.now()

