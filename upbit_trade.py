import pyupbit
import datetime as dt

access = "Oug97pOTCd6xN12mREWTo9GTQcmkzhMtnoW2Wqyo"          # 본인 값으로 변경
secret = "6IUBTLNU02rSGQux5cIMW11W05WnoW5rRKxxSE6Z"          # 본인 값으로 변경
upbit = pyupbit.Upbit(access, secret)

def print_(ticker,msg)  :
    if  ticker :
        ret = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'#'+ticker+'# '+msg
    else :
        ret = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' '+msg
    print(ret, flush=True)

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

def sell_enough_price():
    """종가매도전이라도 목표수익율에 도달하면 즉시 매도"""
    ret = False   # 보유중인 코인이 없는 경우 False 로 리턴
    balances = upbit.get_balances()
    for b in balances:
        if  not (b['currency'] == 'KRW') :
            # 보유코인이 있으면 목표수익율(5%)를 넘어서면 즉시 판다.
            current_ticker = 'KRW-'+b['currency']
            btc, avg_buy_price, current_price = float(b['balance']), float(b['avg_buy_price']),float(pyupbit.get_orderbook(ticker=current_ticker)["orderbook_units"][0]["bid_price"])
            if  btc > 0 :
                ret=True
                print_(current_ticker, f'Enough price TEST btc={btc}, avg_buy_price = {avg_buy_price}, current_price= {current_price}')
                if  current_price > avg_buy_price * 1.015 :
                    sell_limit_order(current_ticker, current_price, btc )
    return ret

def get_avg_buy_price(ticker):
    """매수평균가"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['avg_buy_price'] is not None:
                return float(b['avg_buy_price'])
            else:
                return 0
    return 0

def  sell_limit_order(ticker,price,amount) :
    ret = upbit.sell_limit_order(ticker, price, amount)
    print(ticker,f'sell_limit_order {price:.2f}, {amount:.2f}')
    print(ticker,f'sell_limit_order ret = {ret}')

def  buy_limit_order(ticker,price,amount) :
    ret = upbit.buy_limit_order(ticker, price, amount )
    print_(ticker,f'buy_limit_order {price:.2f}, {amount:.2f}')
    print_(ticker,f'buy_limit_order ret = {ret}')

if __name__ == "__main__":
    pass