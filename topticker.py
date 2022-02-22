import time
import pyupbit
import pandas as pd
from ticker import Ticker
import datetime as dt

def get_ohlcv_custom(ticker,base) :
    df = pyupbit.get_ohlcv(ticker, count=600, interval='minute60')
    df.index = df.index - dt.timedelta(hours=base)
    df_daily = pd.DataFrame()
    df_daily['open'] =  df.open.resample('1D').first()
    df_daily['close'] =  df.close.resample('1D').last()
    df_daily['low'] =  df.low.resample('1D').min()
    df_daily['high'] =  df.high.resample('1D').max()
    df_daily['volume'] =  df.volume.resample('1D').sum()
    df_daily['value'] =  df.value.resample('1D').sum()
    df_daily['ma15'] = df_daily['close'].rolling(15).mean()
    df_daily['ma15_acd'] = df_daily['ma15'] - df_daily['ma15'].shift(1)
    df_daily=df_daily.dropna()
    df_daily = df_daily[::-1]
    return df_daily

# 거래대금 상위 10위...
def best_volume_tickers() : 
    krw = 100000
    all_tickers = pyupbit.get_tickers(fiat="KRW")
    tickers_prices = pyupbit.get_current_price(all_tickers)
    tickers = {}
    for k, v in tickers_prices.items() :
        if  v < krw :
            df = get_ohlcv_custom(k,9)
            if len(df.index) > 0 :
                tickers[k] = df.iloc[0]['value']

    sort_list = sorted(tickers.items(), key=lambda x : x[1], reverse=True)[:10]
    return [e[0] for e in sort_list]

def make_ticker_class(names) :
    result_ticker_object = []
    for  t in  names :
        ticker = Ticker(t)
        ticker.bestValue()
        ticker.make_df()
        if ticker.isgood  and  \
           (ticker.df.iloc[0]['open'] < pyupbit.get_current_price(ticker.name))  :
            result_ticker_object.append(ticker)
    
    return result_ticker_object

if __name__ == "__main__":
    # target_tickers = best_volume_tickers()
    # ticker_objects = make_ticker_class(target_tickers)
    # for t in ticker_objects :
    #     print(t.name, t.target)
    target_tickers = get_ohlcv_custom('KRW-STRK',18)
    print(target_tickers)