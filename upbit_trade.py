import pyupbit
import datetime as dt

access = "Oug97pOTCd6xN12mREWTo9GTQcmkzhMtnoW2Wqyo"          # 본인 값으로 변경
secret = "6IUBTLNU02rSGQux5cIMW11W05WnoW5rRKxxSE6Z"          # 본인 값으로 변경
upbit = pyupbit.Upbit(access, secret)

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

def get_avg_buy_price(ticker):
    """잔고 조회"""
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
    print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] sell_limit_order {ticker}, {price:.2f}, {amount:.2f}', flush=True)
    print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] sell_limit_order ret = {ret}' , flush=True)

def  buy_limit_order(ticker,price,amount) :
    ret = upbit.buy_limit_order(ticker, price, amount )
    print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] buy_limit_order {ticker}, {price:.2f}, {amount:.2f}', flush=True)
    print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] buy_limit_order ret = {ret}' , flush=True)

if __name__ == "__main__":
    btc = get_balance('STRK')
    current_price = pyupbit.get_orderbook(ticker='KRW-STRK')["orderbook_units"][0]["bid_price"]
    sell_p = (btc*0.9995)//current_price
    print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] btc= {btc}, current_price = {current_price}, sell_p = {sell_p}')
    # sell_limit_order('KRW-STRK', ,1.0)