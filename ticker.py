import time
import pyupbit
import pandas as pd
import numpy as np
import datetime as dt
import pyupbit
import account

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
        self.isgood = True

    def __repr__(self):
        return f"<Ticker {self.name}>"

    def __str__(self):
        return f"<Ticker {self.name}>"

    def get_ohlcv_custom(self,_base) :
        df = pyupbit.get_ohlcv(self.name, count=300, interval='minute60')
        df.index = df.index - dt.timedelta(hours=_base)
        df_daily = pd.DataFrame()
        df_daily['open'] =  df.open.resample('1D').first()
        df_daily['close'] =  df.close.resample('1D').last()
        df_daily['low'] =  df.low.resample('1D').min()
        df_daily['high'] =  df.high.resample('1D').max()
        df_daily['volume'] =  df.volume.resample('1D').sum()
        df_daily['value'] =  df.value.resample('1D').sum()
        df_daily['ma5'] = df_daily['close'].rolling(5).mean()
        df_daily['ma5_acd'] = df_daily['ma5'] - df_daily['ma5'].shift(1)
        df_daily=df_daily.dropna()
        df_daily = df_daily[::-1]
        return df_daily

    def get_ror_k(self,k,base) :
        df = self.get_ohlcv_custom(base)  
        df['range'] = (df['high'] - df['low']) * k
        df['target'] = df['open'] + df['range'].shift(-1)
        df=df.head(7)

        df['ror'] = df.apply(   \
            lambda row : (row.close / row.target) - self.fee if row.high > row.target else 1, axis=1)
        df['cumsum'] = (df['ror']-1).cumsum()
        cumsum = df['cumsum'][-1]
        return cumsum

    def get_loss_base(self,base):
        df = self.get_ohlcv_custom(base)
        df['loss'] = df['open'] - df['low']
        df['cumloss'] = df['loss'].cumsum()
        df=df.head(7)
        cumloss = df['cumloss'][-1]
        return cumloss

    def bestValue(self) :
        # 최적의 BASE
        basedict = {}
        for b in range(1,24,1) :
            cumloss = self.get_loss_base(b)
            basedict[str(round(cumloss,4))] = str(b)
            time.sleep(0.3)

        minkey = min(basedict.keys(), key=(lambda k : float(k)))
        minBase = int(basedict[minkey])

        # 최적의 K 값 찾기 
        kdict = {}
        for k in range(1,10,1) :
            cumsum = self.get_ror_k(k/10,minBase)
            kdict[str(round(cumsum,4))] = str(k/10)
            time.sleep(0.3)

        maxkey = max(kdict.keys(), key=(lambda k : float(k)))
        maxK = float(kdict[maxkey])

        print_(self.name,f'bestValue TEST maxK = {maxK}, minBase = {minBase}')
        
        self.k =  maxK
        self.base = minBase


    def make_df(self) :
        try :
            df = self.get_ohlcv_custom(self.base)
            df['range'] = (df['high'] - df['low']) * self.k
            df['target'] = df['open'] + df['range'].shift(-1)
            self.df = df.head(7)
            self.target_price = self.df.iloc[0]['target'] 
            # 일봉상 5이평선이 우상향
            self.isgood = True if self.df.iloc[0]['ma5_acd'] > 0 else False
            # 이미 목표가에 도달했었던 적있는 경우는 제외
            self.isgood = self.isgood and ( False if self.df.iloc[0]['high'] > self.target_price else True )
            self.isgood = self.isgood and ( True if self.df.iloc[1]['close'] > self.df.iloc[1]['open'] else False )
        except Exception :
            pass

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
    # print('KRW-T'['KRW-T'.find('-')+1:])

    t  = Ticker('KRW-OMG')
    t.bestValue()  # 최적의 k, base 를 세팅한다.
    t.make_df()
    print(t.df)
    # t.make_df()    # k,base 를 이용하여 df 와 target_price 를 결정한다.
    # t.get_start_time()  # base를 이용하여 하루거래의 시간대를 설정한다
