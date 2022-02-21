import time
import pyupbit
import datetime
import pandas as pd
# from pandasql import sqldf
import numpy as np
import datetime as dt

class Ticker :
    def __init__(self, name) -> None:
        self.name =  name
        self.currency = name[-3:]
        self.__days = 7 
        #업비트 거래소 매매거래 수수료
        self.fee = 0.0005
        self.k = 0.4
        self.base = 9
        self.bestValue()  # 최적의 k, base 를 세팅한다.
        self.make_df()    # k,base 를 이용하여 df 와 target_price 를 결정한다.
        self.start_time, self.end_time, self.nextday =  self.get_start_time()  # base를 이용하여 하루거래의 시간대를 설정한다

    # def get_ohlcv_custom(self,base) :
    #     df_1 = pyupbit.get_ohlcv(self.name, interval="minute60")
    #     df_1['newdate'] = df_1.index
    #     df_1['stickdate'] = df_1.apply(   \
    #         lambda row : str( row.newdate + datetime.timedelta(days=-1))[:10] if 0 <= row.newdate.hour < base else str(row.newdate)[:10], axis=1)
    #     sql =   f"""

    #         with a as ( 
    #                 select stickdate, newdate, cast(strftime('%H',newdate) as int) as hour, open, high, low, close, volume,
    #                     row_number() over(partition by stickdate order by newdate desc) as idx
    #                 from df_1
    #         )
    #         select  a.stickdate as _date
    #             ,max(case when a.hour={base} then a.open else null end) as open
    #             ,max(case when idx = 1 then a.close else null end) as close
    #             ,min(a.low) as low
    #             ,max(a.high) as high
    #             ,sum(a.volume) as volume
    #         from  a
    #         group by a.stickdate
    #         order by 1 desc

    #         """
    #     df = sqldf(sql, locals())
    #     df=df.loc[0:self.__days]
    #     df.set_index('_date',inplace =True)
    #     return df

   
    def get_ohlcv_custom(self,_base) :
        df = pyupbit.get_daily_ohlcv_from_base(ticker=self.name, base=_base)
        df = df[::-1]
        return df
     
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
            time.sleep(1)

        maxkey = max(kdict.keys(), key=(lambda k : float(k)))
        maxK = float(kdict[maxkey])

        # 최적의 BASE
        basedict = {}
        for b in range(1,24,1) :
            cumsum = self.__get_ror_base(maxK,b)
            basedict[str(round(cumsum,4))] = str(b)
            time.sleep(1)

        maxkey = max(basedict.keys(), key=(lambda k : float(k)))
        maxBase = int(basedict[maxkey])
        # print('==============================================================', flush=True)
        # print(f'ticker = {self.name}, maxK = {maxK}, maxBase = {maxBase}, maxProfit_1day = {maxkey}', flush=True)
        # print('===============================================================', flush=True)

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

    def get_start_time(self) :
        basetime = dt.datetime.now()

        start_time = basetime.replace(hour=self.base,minute=0,second=0)
        if start_time > basetime :
            nextday = start_time
            end_time = start_time - dt.timedelta(seconds=10)
            start_time = start_time - dt.timedelta(days=1)
            
        else :
            nextday = start_time + dt.timedelta(days=1)
            end_time = start_time + dt.timedelta(days=1) - dt.timedelta(seconds=10)

        return start_time, end_time, nextday
            