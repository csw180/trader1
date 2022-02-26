import time
import pyupbit
import datetime as dt
from ticker import Ticker
import upbit_trade

total_seed = 90000

# 거래량 상위 10개 종목 선별
def best_volume_tickers() : 
    all_tickers = pyupbit.get_tickers(fiat="KRW")
    all_tickers_prices = pyupbit.get_current_price(all_tickers)
    all_tickers_value = {}

    # 각 종목의 거래대금을 조사한다.
    for k, v in all_tickers_prices.items() :
        if  v < total_seed :
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

print(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] Autotrader init.. ", flush=True)
tickers = best_volume_tickers()
print(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] best_volume_tickers finished.. count= {len(tickers)}", flush=True)

standby_time_best_volume_tickers = dt.datetime.now()
standby_time_best_volume_tickers = standby_time_best_volume_tickers.replace(hour=18,minute=20,second=0)
if dt.datetime.now() > standby_time_best_volume_tickers :
    standby_time_best_volume_tickers = standby_time_best_volume_tickers + dt.timedelta(days=1)

loop_cnt = 0
# 자동매매 시작
while  True :
    loop_cnt +=1
    try : 
        for t in  tickers :
            t.do()
            if loop_cnt >= 300 :   # 운영모드로 가면 충분히 크게 바꿀것..
                print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}]#{t.name} {t.start_time:%Y-%m-%d %H:%M:%S}~{t.end_time:%Y-%m-%d %H:%M:%S}, target:{t.target_price:,.2f}, current:{pyupbit.get_current_price(t.name):,}', flush=True)
        if  loop_cnt >= 300 :  # 운영모드로 가면 충분히 크게 바꿀것..
            loop_cnt = 0
        
        current_time = dt.datetime.now()
        if  current_time > standby_time_best_volume_tickers :
            tickers = best_volume_tickers()
            print(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] best_volume_tickers finished.. count= {len(tickers)}", flush=True)
            standby_time_best_volume_tickers = standby_time_best_volume_tickers + dt.timedelta(days=1)
        else :
            time.sleep(1)

    except Exception as e:
        print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {e}', flush=True)
        time.sleep(1)