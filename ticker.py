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
        self.k = 0.4
        self.base = 9
        self.bestValue()  # 최적의 k, base 를 세팅한다.
        self.make_df()    # k,base 를 이용하여 df 와 target_price 를 결정한다.
        self.get_start_time()  # base를 이용하여 하루거래의 시간대를 설정한다

    def __repr__(self):
        return f"<Ticker {self.name}>"

    def __str__(self):
        return f"<Ticker {self.name}>"

    def get_ohlcv_custom(self,_base) :
        df = pyupbit.get_ohlcv(self.name, count=600, interval='minute60')
        df.index = df.index - dt.timedelta(hours=_base)
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

    def __get_ror_k(self,k) :
        df = self.get_ohlcv_custom(self.base)  
        df['range'] = (df['high'] - df['low']) * k
        df['target'] = df['open'] + df['range'].shift(-1)
        df=df.dropna()

        df['ror'] = df.apply(   \
            lambda row : (row.close / row.target) - self.fee if row.high > row.target else 1, axis=1)
        df['cumsum'] = (df['ror']-1).cumsum()
        cumsum = df['cumsum'][-1]
        return cumsum

    def __get_ror_base(self,k,base):
        df = self.get_ohlcv_custom(base)
        df['range'] = (df['high'] - df['low']) * k
        df['target'] = df['open'] + df['range'].shift(-1)
        df=df.dropna()

        df['ror'] = df.apply(   \
            lambda row : (row.close / row.target) - self.fee if row.high > row.target else 1, axis=1)

        df['cumsum'] = (df['ror']-1).cumsum()
        cumsum = df['cumsum'][-1]
        return cumsum

    def bestValue(self) :
        # 최적의 K 값 찾기 
        kdict = {}
        for k in range(1,10,1) :
            cumsum = self.__get_ror_k(k/10)
            kdict[str(round(cumsum,4))] = str(k/10)
            time.sleep(0.5)

        maxkey = max(kdict.keys(), key=(lambda k : float(k)))
        maxK = float(kdict[maxkey])

        # 최적의 BASE
        basedict = {}
        for b in range(1,24,1) :
            cumsum = self.__get_ror_base(maxK,b)
            basedict[str(round(cumsum,4))] = str(b)
            time.sleep(0.5)

        maxkey = max(basedict.keys(), key=(lambda k : float(k)))
        maxBase = int(basedict[maxkey])
        print_(self.name,f'bestValue TEST maxK = {maxK}, maxBase = {maxBase}')
        
        self.k =  maxK
        self.base = maxBase

    def make_df(self) :
        df = self.get_ohlcv_custom(self.base)  
        df['range'] = (df['high'] - df['low']) * self.k
        df['target'] = df['open'] + df['range'].shift(-1)
        df=df.dropna()

        df['ror'] = df.apply(   \
            lambda row : (row.close / row.target) - self.fee if row.high > row.target else 1, axis=1)
        df['cumsum'] = (df['ror']-1).cumsum()
        self.df = df
        self.target_price = self.df.iloc[0]['target'] 
        # 일봉상 15이평선이 우상향
        self.isgood = True if self.df.iloc[0]['ma15_acd'] > 0 else False
        # 이미 목표가에 도달했었던 적있는 경우는 제외
        self.isgood = self.isgood and ( False if self.df.iloc[0]['high'] > self.target_price else True )

    def get_start_time(self) :
        basetime = dt.datetime.now()

        start_time = basetime.replace(hour=self.base,minute=0,second=0)
        if start_time > basetime :
            nextday = start_time
            end_time = start_time - dt.timedelta(minutes=10)
            start_time = start_time - dt.timedelta(days=1)
            
        else :
            nextday = start_time + dt.timedelta(days=1)
            end_time = start_time + dt.timedelta(days=1) - dt.timedelta(seconds=10)

        self.start_time = start_time
        self.end_time = end_time
        self.nextday = nextday

if __name__ == "__main__":
    t  = Ticker('KRW-MANA')
    t.bestValue()
    t.make_df()
    print(t.df)
    print(t.isgood)