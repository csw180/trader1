"""
최적의 K 값 찾기
최적의 BASE 값 찾기

변동성 돌파 전략을 적용하기 위해서 
하루의 시작을 몇시로 보는것이 가장 최적인가를 검정하는 프로그램
적절한 하루시작시간과 K 값을 시뮬레이션 시켜본다.
"""

import time
import pyupbit
import datetime
import pandas as pd
from pandasql import sqldf
import numpy as np

current_ticker = 'KRW-ETC'

# 최적 K, BASE 추정 관련 상수
# DAYS : 몇일간의 데이터를 가지고 K 와 BASE 를 구할것인가
# K : 변동성돌파전략 K
# BASE : 하루의 시작을 몇시로 볼것인가
DAYS = 7  #최대 2<= DAYS <=7, 8이상 넣으면 마지막에 NAN에 들어올수 있음, 2이상은 넣어야 shift(-1)로인한 에러 안남,
          #거래당일은 제외한 숫자임
K = 0.3
BASE = 8

#거래소 매매거래 수수료
fee = 0.0005

def get_ohlcv_custom(ticker,count,base) :
    df_1 = pyupbit.get_ohlcv(ticker, interval="minute60")
    df_1['newdate'] = df_1.index
    df_1['stickdate'] = df_1.apply(   \
        lambda row : str( row.newdate + datetime.timedelta(days=-1))[:10] if 0 <= row.newdate.hour < base else str(row.newdate)[:10], axis=1)
    sql =   f"""

        with a as ( 
                select stickdate, newdate, cast(strftime('%H',newdate) as int) as hour, open, high, low, close, volume,
                       row_number() over(partition by stickdate order by newdate desc) as idx
                from df_1
        )
        select  a.stickdate as _date
            ,max(case when a.hour={base} then a.open else null end) as open
            ,max(case when idx = 1 then a.close else null end) as close
            ,min(a.low) as low
            ,max(a.high) as high
            ,sum(a.volume) as volume
        from  a
        group by a.stickdate
        order by 1 desc

        """
    df = sqldf(sql, locals())
    df=df.loc[0:count]
    df.set_index('_date',inplace =True)
    return df

def get_ror_k(k=0.5):
    df = get_ohlcv_custom(current_ticker,DAYS,BASE)  
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(-1)
    df=df.dropna()

    df['ror'] = df.apply(   \
        lambda row : (row.close / row.target) - fee if row.high > row.target else 1, axis=1)
    df['cumsum'] = (df['ror']-1).cumsum()
    cumsum = df['cumsum'][-1]
    return cumsum

def get_ror_base(k,base):
    df = get_ohlcv_custom(current_ticker,DAYS,base)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(-1)
    df=df.dropna()

    df['ror'] = df.apply(   \
        lambda row : (row.close / row.target) - fee if row.high > row.target else 1, axis=1)

    # 종가매도가 아닌 목표수익율 2%~3% 도달하면 판다고 가정하고 수익율 계산 : 수익이 더 줄어듬..
    # lambda row : (get_sellprice_enough(row.target , 1.03, row.high, row.close) / row.target) - fee if row.high > row.target else 1, axis=1) 
    df['cumsum'] = (df['ror']-1).cumsum()
    cumsum = df['cumsum'][-1]
    return cumsum

# 종가매도가 아닌 목표수익율 2%~3% 도달하면 판다고 가정할때 매도가격을 가져온다.
# def get_sellprice_enough(baseP, enough, limit, ovlimit) :
#     if baseP * enough < limit :
#         return baseP * enough
#     else :
#         return ovlimit

def bestValue() :
    # 최적의 K 값 찾기 
    kdict = {}
    for k in range(1,10,1) :
        cumsum = get_ror_k(k/10)
        kdict[str(round(cumsum,4))] = str(k/10)
        time.sleep(1)

    maxkey = max(kdict.keys(), key=(lambda k : float(k)))
    maxK = float(kdict[maxkey])

    # 최적의 BASE
    basedict = {}
    for b in range(1,24,1) :
        cumsum = get_ror_base(maxK,b)
        basedict[str(round(cumsum,4))] = str(b)
        time.sleep(1)

    maxkey = max(basedict.keys(), key=(lambda k : float(k)))
    maxBase = int(basedict[maxkey])
    print('==============================================================', flush=True)
    print(f'maxK = {maxK}, maxBase = {maxBase}, maxProfit_1day = {maxkey}', flush=True)
    print('===============================================================', flush=True)

    return maxK,maxBase
