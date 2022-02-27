import time
import pyupbit
import datetime as dt
from ticker import Ticker
import upbit_trade

def print_(ticker,msg)  :
    if  ticker :
        ret = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'#'+ticker+'# '+msg
    else :
        ret = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' '+msg
    print(ret, flush=True)

# 거래량 상위 10개 종목 선별
def best_volume_tickers() : 
    all_tickers = pyupbit.get_tickers(fiat="KRW")
    all_tickers_prices = pyupbit.get_current_price(all_tickers)
    all_tickers_value = {}

    # 각 종목의 거래대금을 조사한다.
    for k, v in all_tickers_prices.items() :
        if  v < 90000 :   # 단가가 9만원 미만인 것만...
            df = pyupbit.get_ohlcv(k, count=3, interval='minute60')  #60분봉 3개의 거래대금 합을 가져오기 위함
            time.sleep(0.5)
            if len(df.index) > 0 :
                all_tickers_value[k] = df['value'].sum()

    # 거래대금 top 10 에 해당하는 종목만 걸러낸다
    sorted_list = sorted(all_tickers_value.items(), key=lambda x : x[1], reverse=True)[:10]
    top_tickers = [e[0] for e in sorted_list]
    tickers = []
    for  t in  top_tickers :
        ticker = Ticker(t)
        ticker.bestValue()
        ticker.make_df()
        if  ticker.isgood :
            tickers.append(ticker)
    return tickers

print_('',f"Autotrader init.. ")
tickers = best_volume_tickers()
print_('',f"best_volume_tickers finished.. count={len(tickers)} tickers={tickers}")

# standby_time_best_volume_tickers = dt.datetime.now()
# standby_time_best_volume_tickers = standby_time_best_volume_tickers.replace(hour=18,minute=20,second=0)
# if dt.datetime.now() > standby_time_best_volume_tickers :
#     standby_time_best_volume_tickers = standby_time_best_volume_tickers + dt.timedelta(days=1)
# print_('',f"best_volume_tickers finished.. count={len(tickers)} tickers={tickers}")

loop_cnt = 0
print_loop = 20
# 자동매매 시작
while  True :
    loop_cnt +=1
    try : 
        if upbit_trade.sell_enough_price() :
            time.sleep(2)
            continue

        if  not tickers :
            print_('',f"None tickers selected. bestVolume search again after 30 minute sleep")
            time.sleep(60*30)
            tickers = best_volume_tickers()
            print_('',f"best_volume search finished.. count={len(tickers)} tickers={tickers}")
            continue

        current_time = dt.datetime.now()
        for t in  tickers :
            if  current_time > t.nextday :                
                t.bestValue()
                t.make_df()
                t.get_start_time()
                print_(t.name,f'k = {t.k}, base = {t.base}, target_price = {t.target_price}')
                print_(t.name,f'New Day START!..{t.start_time:%Y-%m-%d %H:%M:%S} ~ {t.end_time::%Y-%m-%d %H:%M:%S}, nextday : {t.nextday:%Y-%m-%d %H:%M:%S}')

            elif  t.start_time < current_time < t.end_time :    
                if loop_cnt >= print_loop :   # 운영모드로 가면 충분히 크게 바꿀것..
                    print_(t.name,f'{t.start_time:%Y-%m-%d %H:%M:%S} ~ {t.end_time:%Y-%m-%d %H:%M:%S}, target:{t.target_price:,.2f}, current:{pyupbit.get_current_price(t.name):,}')
                    loop_cnt = 0

                current_price = float(pyupbit.get_orderbook(ticker=t.name)["orderbook_units"][0]["ask_price"]) 
                if t.target_price < current_price:
                    krw = upbit_trade.get_balance("KRW")
                    print_(t.name,f'get_balance(KRW): {krw}')
                    if krw > 5000:
                        upbit_trade.buy_limit_order(t.name, current_price, (krw*0.999)//current_price )
            else : 
                if  btc:=upbit_trade.get_balance(t.currency) > 0 :
                    current_price = t.get_current_bid_price()
                    print_(t.name,f'force to sell unconditionally get_balance({t.currency}): {btc}, current_price= {current_price}')
                    upbit_trade.sell_limit_order(t.name, current_price, btc )
                    print_(t.name,'excluded from ticker list')
                    tickers.remove(t)
                    break
                        
        # if  current_time > standby_time_best_volume_tickers:
        #     tickers = best_volume_tickers()
        #     print_('',f"best_volume search finished.. count={len(tickers)} tickers={tickers}")
        #     standby_time_best_volume_tickers = standby_time_best_volume_tickers + dt.timedelta(days=1)
        # else :
        #     time.sleep(1)

        time.sleep(1)
    except Exception as e:
        print_('',f'{e}')
        time.sleep(1)