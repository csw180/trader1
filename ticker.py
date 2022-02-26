import time
import pyupbit
import pandas as pd
import numpy as np
import datetime as dt
import pyupbit
import upbit_trade

class Ticker :
    def __init__(self, name) -> None:
        self.name =  name
        self.currency = name[name.find('-')+1:]
        self.fee = 0.0005   #업비트 거래소 매매거래 수수료
        self.k = 0.4
        self.base = 9
        self.bestValue()  # 최적의 k, base 를 세팅한다.
        self.make_df()    # k,base 를 이용하여 df 와 target_price 를 결정한다.
        self.start_time, self.end_time, self.nextday =  self.get_start_time()  # base를 이용하여 하루거래의 시간대를 설정한다

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
            time.sleep(0.2)

        maxkey = max(kdict.keys(), key=(lambda k : float(k)))
        maxK = float(kdict[maxkey])

        # 최적의 BASE
        basedict = {}
        for b in range(1,24,1) :
            cumsum = self.__get_ror_base(maxK,b)
            basedict[str(round(cumsum,4))] = str(b)
            time.sleep(0.2)

        maxkey = max(basedict.keys(), key=(lambda k : float(k)))
        maxBase = int(basedict[maxkey])
        # maxBase = 9
        print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] ==============================================================', flush=True)
        print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}]  ticker = {self.name}, maxK = {maxK}, maxBase = {maxBase}, maxProfit_1day = {maxkey}', flush=True)
        print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] ===============================================================', flush=True)

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
        # 현재가가 일봉상 고점밑일때 이미 고점찍고 내려오는 국면일수 있다
        self.isgood = False if pyupbit.get_current_price(self.name)*1.01 < self.df.iloc[0]['high'] else True  

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

        return start_time, end_time, nextday

    def do(self) :
        # 보유코인이 있으면 목표수익율(5%)를 넘어서면 즉시 판다.
        btc = upbit_trade.get_balance(self.currency)
        avg_buy_price = upbit_trade.get_avg_buy_price(self.currency)
        current_price = self.get_current_bid_price()
        if  btc > 0 :
            self.isgood = False
            if  current_price > avg_buy_price * 1.03 :
                print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] get_balance({self.name}): {btc}, avg_buy_price = {avg_buy_price}, current_price= {current_price}', flush=True)
                if btc > ( 5000 / current_price) :
                    upbit_trade.sell_limit_order(self.name, current_price, btc )
            return

        if not self.isgood :
            print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {self.name} not good position. may be not ascending ...',flush=True)
            return

        current_time = dt.datetime.now()
        if  self.start_time < current_time < self.end_time :    
            current_price = self.get_current_ask_price()     
            if self.target_price < current_price:
                krw = upbit_trade.get_balance("KRW")
                print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] get_balance(KRW): {krw}', flush=True)
                if krw > 5000:
                    upbit_trade.buy_limit_order(self.name, current_price, (krw*0.999)//current_price )
        else : 
            if  btc:=upbit_trade.get_balance(self.currency) > 0 :
                current_price = self.get_current_bid_price()
                print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] get_balance({self.name}): {btc}, current_price= {current_price}', flush=True)
                if btc > ( 5000 / current_price) :
                    upbit_trade.sell_limit_order(self.name, current_price, btc )
            
            print(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] best K, base simmulation.....", flush=True)
            self.bestValue()
            self.make_df()
            print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] ticker= {self.name}, k = {self.k}, base = {self.base}, target_price = {self.target_price}', flush=True)
            self.get_start_time()
            print(f'[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] Day START!..{self.start_time:%Y-%m-%d %H:%M:%S} ~ {self.end_time::%Y-%m-%d %H:%M:%S},  nextday : {self.nextday:%Y-%m-%d %H:%M:%S}', flush=True)
            

    def get_current_ask_price(self):  # 현재 매수가.
        """현재가 조회"""
        return pyupbit.get_orderbook(ticker=self.name)["orderbook_units"][0]["ask_price"]

    def get_current_bid_price(self):  #현재 매도가
        """현재가 조회"""
        return pyupbit.get_orderbook(ticker=self.name)["orderbook_units"][0]["bid_price"]

    #60분봉 3개의 거래대금 합
    def get_current_value(self) :
        result = 0
        df = pyupbit.get_ohlcv(self.name, count=3, interval='minute60')  
        if len(df.index) > 0 :
            result = df['value'].sum()
        return result