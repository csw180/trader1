import time
import pyupbit
import pandas as pd
import numpy as np
import datetime as dt
import pyupbit
import upbit_trade

def print_(ticker,msg)  :
    if  ticker :
        ret = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'#'+ticker+'# '+msg
    else :
        ret = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' '+msg
    print(ret, flush=True)

class Ticker :
    def __init__(self, name) -> None:
        self.name =  name
        self.currency = name[name.find('-')+1:]
        self.fee = 0.0005   #업비트 거래소 매매거래 수수료
        self.get_target_price()
        self.make_df()    # k,base 를 이용하여 df 와 target_price 를 결정한다.

    def __repr__(self):
        return f"<Ticker {self.name}>"

    def __str__(self):
        return f"<Ticker {self.name}>"

    def get_target_price(self) :
        df =  pyupbit.get_ohlcv(self.name, count=100, interval="day")
        df['ma20'] = df['close'].rolling(20).mean()
        df['ma20_asc'] = df['ma20'] - df['ma20'].shift(1)
        df['max20'] = df['high'].rolling(20).max()
        df['max20_asc_d1'] = df['max20'] - df['max20'].shift(1)
        df['max20_asc_d2'] = df['max20'] - df['max20'].shift(2)

        df=df.dropna()
        df=df[::-1]
        self.target_price = df.iloc[0]['max20'] 
        # 일봉상 20이평선이 우상향
        self.isgood = True if df.iloc[0]['ma20_asc'] > 0 else False
        # 이미 목표가에 도달했었던 적있는 경우는 제외
        self.isgood = self.isgood and ( False if df.iloc[0]['high'] > self.target_price else True )
        # 연속고가를 갱신하는 모양은 제외
        self.isgood = self.isgood and ( True if df.iloc[0]['max20_asc_d1'] == 0 and \
                                                df.iloc[0]['max20_asc_d2'] == 0 else False )

    def make_df(self) :
        df = pyupbit.get_ohlcv(self.name, count=600, interval='minute5')
        df['vma20'] = df['volume'].rolling(15).mean()
        df['vma20_asc'] = df['vma20'] - df['vma20'].shift(1)
        df=df.dropna()
        df=df[::-1]
        df['target'] = self.target_price
        self.df = df

if __name__ == "__main__":
    t  = Ticker('KRW-MANA')
    t.get_target_price()
    t.make_df()
    print(t.df.head(30))
    print(t.target_price)
    print(t.isgood)