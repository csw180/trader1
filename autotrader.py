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
            time.sleep(0.2)
            if len(df.index) > 0 :
                if  k == 'KRW-T' :  #상장된지 얼마안된건 제외.에러남.
                    continue
                all_tickers_value[k] = df['value'].sum()

    # 거래대금 top 10 에 해당하는 종목만 걸러낸다
    sorted_list = sorted(all_tickers_value.items(), key=lambda x : x[1], reverse=True)[:10]
    top_tickers = [e[0] for e in sorted_list]
    tickers = []
    print_('',f'top_ticker= {top_tickers}')
    for  t in  top_tickers :
        ticker = Ticker(t)
        ticker.bestValue()
        ticker.make_df()
        if  ticker.isgood :
            tickers.append(ticker)

    # 이미 잔고가 있는 종목은 거래대금TOP10 리스트에 강제 추가 한다
    balances = upbit_trade.get_balances()
    for b in balances :
        rt = True
        tmp_ticker = b['currency']
        tmp_ticker = 'KRW-' + tmp_ticker
        for t in tickers :
            if (tmp_ticker == t.name) :
                rt=False
                break
        if  rt :
            ticker = Ticker(tmp_ticker)
            ticker.bestValue()
            ticker.make_df()
            tickers.append(ticker)

    return tickers

print_('',f"Autotrader init.. ")
tickers = best_volume_tickers()
print_('',f"best_volume_tickers finished.. count={len(tickers)} tickers={tickers}")
loop_cnt = 0
print_loop = 100

# 자동매매 시작
while  True :
    loop_cnt +=1
    try : 
        if loop_cnt >= print_loop + 1 :   # 운영모드로 가면 충분히 크게 바꿀것..
            loop_cnt = 0

        if  not tickers :
            print_('',f"None tickers selected. bestVolume search again after 30 minute sleep")
            time.sleep(60)
            tickers = best_volume_tickers()
            print_('',f"best_volume search finished.. count={len(tickers)} tickers={tickers}")
            continue

        current_time = dt.datetime.now()
        for t in  tickers :
            if  current_time > t.nextday :       
                try :
                    tickers.remove(t)
                except ValueError :
                    pass         
                break

            elif  t.start_time < current_time < t.end_time :    
                # 이미 잔고가 있는 종목은 목표가에 왔는지 확인하고 즉시 매도 처리 한다.
                btc=upbit_trade.get_balance(t.currency)
                if  btc > 0 :
                    current_price = float(pyupbit.get_orderbook(ticker=t.name)["orderbook_units"][0]["bid_price"])
                    avg_buy_price = upbit_trade.get_avg_buy_price(t.currency)
                    if print_loop-5 <= loop_cnt < print_loop-3 :   # 운영모드로 가면 충분히 크게 바꿀것..
                        print_(t.name,f'Enough price TEST btc=({t.currency}): {btc}, avg_buy_price = {avg_buy_price}, current_price= {current_price}')
                    if  current_price > avg_buy_price * 1.025 :
                        upbit_trade.sell_limit_order(t.name, current_price, btc )
                        print_(t.name,'excluded from ticker list')
                        try :
                            tickers.remove(t)
                        except ValueError :
                            pass
                    break

                if loop_cnt >= print_loop :   # 운영모드로 가면 충분히 크게 바꿀것..
                    print_(t.name,f'{t.start_time:%Y-%m-%d %H:%M:%S} ~ {t.end_time:%Y-%m-%d %H:%M:%S}, target:{t.target_price:,.2f}, current:{pyupbit.get_current_price(t.name):,}')

                current_price = float(pyupbit.get_orderbook(ticker=t.name)["orderbook_units"][0]["ask_price"]) 
                if t.target_price < current_price:
                    krw = upbit_trade.get_balance("KRW")
                    print_(t.name,f'get_balance(KRW): {krw}')
                    if krw > 5000:
                        upbit_trade.buy_limit_order(t.name, current_price, (krw*0.999)//current_price )
            else : 
                btc=upbit_trade.get_balance(t.currency) 
                if  btc > 0 :
                    current_price = float(pyupbit.get_orderbook(ticker=t.name)["orderbook_units"][0]["bid_price"])
                    print_(t.name,f'force to sell unconditionally get_balance({t.currency}): {btc}, current_price= {current_price}')
                    upbit_trade.sell_limit_order(t.name, current_price, btc )
                    print_(t.name,'excluded from ticker list')
                    try :
                        tickers.remove(t)
                    except ValueError :
                        pass
                    break
        time.sleep(1)
    except Exception as e:
        print_('',f'{e}')
        time.sleep(1)