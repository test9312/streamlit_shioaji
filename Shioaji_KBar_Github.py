# -*- coding: utf-8 -*-
"""
Created on Sun Dec 31 01:23:34 2023

@author: user
"""
import numpy as np
import indicator_f_Lo2_short,datetime, indicator_forKBar_short
import pandas as pd
import streamlit as st 
import streamlit.components.v1 as stc 

html_temp = """
		<div style="background-color:#3872fb;padding:10px;border-radius:10px">
		<h1 style="color:white;text-align:center;">金融資料視覺化呈現 (金融看板) </h1>
		<h2 style="color:white;text-align:center;">Financial Dashboard </h2>
		</div>
		"""
stc.html(html_temp)
df_original = pd.read_excel("kbars_2330_2022-01-01-2022-11-18.xlsx")
df_original = df_original.drop('Unnamed: 0',axis=1)



st.subheader("選擇開始與結束的日期, 區間:2022-01-03 至 2022-11-18")
start_date = st.text_input('選擇開始日期 (日期格式: 2022-01-03)', '2022-01-03')
end_date = st.text_input('選擇結束日期 (日期格式: 2022-11-18)', '2022-11-18')
start_date = datetime.datetime.strptime(start_date,'%Y-%m-%d')
end_date = datetime.datetime.strptime(end_date,'%Y-%m-%d')
# 使用条件筛选选择时间区间的数据
df = df_original[(df_original['time'] >= start_date) & (df_original['time'] <= end_date)]


### 轉化為字典:
KBar_dic = df.to_dict()

KBar_open_list = list(KBar_dic['open'].values())
KBar_dic['open']=np.array(KBar_open_list)

KBar_dic['product'] = np.repeat('tsmc', KBar_dic['open'].size)

KBar_time_list = list(KBar_dic['time'].values())
KBar_time_list = [i.to_pydatetime() for i in KBar_time_list] ## Timestamp to datetime
KBar_dic['time']=np.array(KBar_time_list)

KBar_low_list = list(KBar_dic['low'].values())
KBar_dic['low']=np.array(KBar_low_list)

KBar_high_list = list(KBar_dic['high'].values())
KBar_dic['high']=np.array(KBar_high_list)

KBar_close_list = list(KBar_dic['close'].values())
KBar_dic['close']=np.array(KBar_close_list)

KBar_volume_list = list(KBar_dic['volume'].values())
KBar_dic['volume']=np.array(KBar_volume_list)

KBar_amount_list = list(KBar_dic['amount'].values())
KBar_dic['amount']=np.array(KBar_amount_list)


######  改變 KBar 時間長度 (以下)  ########

Date = start_date.strftime("%Y-%m-%d")

st.subheader("設定一根 K 棒的時間長度(分鐘)")
cycle_duration = st.number_input('輸入一根 K 棒的時間長度(單位:分鐘, 一日=1440分鐘)', key="KBar_duration")
cycle_duration = int(cycle_duration)
KBar = indicator_forKBar_short.KBar(Date,cycle_duration)    ## 設定cycle_duration可以改成你想要的 KBar 週期

for i in range(KBar_dic['time'].size):
    

    time = KBar_dic['time'][i]
    open_price= KBar_dic['open'][i]
    close_price= KBar_dic['close'][i]
    low_price= KBar_dic['low'][i]
    high_price= KBar_dic['high'][i]
    qty =  KBar_dic['volume'][i]
    amount = KBar_dic['amount'][i]
    tag=KBar.AddPrice(time, open_price, close_price, low_price, high_price, qty)
    
KBar_dic = {}

## 形成 KBar 字典:
KBar_dic['time'] =  KBar.TAKBar['time']   
KBar_dic['product'] = np.repeat('tsmc', KBar_dic['time'].size)
KBar_dic['open'] = KBar.TAKBar['open']
KBar_dic['high'] =  KBar.TAKBar['high']
KBar_dic['low'] =  KBar.TAKBar['low']
KBar_dic['close'] =  KBar.TAKBar['close']
KBar_dic['volume'] =  KBar.TAKBar['volume']


######  (一) 移動平均線策略   #########

st.subheader("設定計算長移動平均線(MA)的 K 棒數目(整數, 例如 10)")

LongMAPeriod=st.slider('選擇一個整數', 0, 100, 10)

st.subheader("設定計算短移動平均線(MA)的 K 棒數目(整數, 例如 2)")

ShortMAPeriod=st.slider('選擇一個整數', 0, 100, 2)

                
st.subheader("設定計算長RSI指標線(整數, 例如 15)")
LongRSIPeriod=st.slider('選擇一個整數', 0, 1000, 15)


st.subheader("設定計算短RSI指標線(整數, 例如 8)")
ShortRSIPeriod=st.slider('選擇一個整數', 0, 1000, 8)


# 將K線 Dictionary 轉換成 Dataframe
KBar_df = pd.DataFrame(KBar_dic)

KBar_df['MA_long'] = KBar_df['close'].rolling(window=LongMAPeriod).mean()
KBar_df['MA_short'] = KBar_df['close'].rolling(window=ShortMAPeriod).mean()



def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi
# # 計算 RSI指標長短線
KBar_df['RSI_long'] = calculate_rsi(KBar_dic,timeperiod=LongRSIPeriod)
KBar_df['RSI_short'] = calculate_rsi(KBar_dic,timeperiod=ShortRSIPeriod)


## 尋找最後 NAN值的位置
last_nan_index_MA = KBar_df['MA_long'][::-1].index[KBar_df['MA_long'][::-1].apply(pd.isna)][0]
last_nan_index_RSI = KBar_df['RSI_long'][::-1].index[KBar_df['RSI_long'][::-1].apply(pd.isna)][0]



# 將 Dataframe 欄位名稱轉換
KBar_df.columns = [ i[0].upper()+i[1:] for i in KBar_df.columns ]


st.subheader("畫圖")
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import plotly.offline as pyoff

with st.expander("K線圖與移動平均線"):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # include candlestick with rangeselector
    fig.add_trace(go.Candlestick(x=KBar_df['Time'],
                    open=KBar_df['Open'], high=KBar_df['High'],
                    low=KBar_df['Low'], close=KBar_df['Close'], name='K線'),
                   secondary_y=True)   ## secondary_y=True 表示此圖形的y軸scale是在右邊而不是在左邊
    
    #include a go.Bar trace for volumes
    fig.add_trace(go.Bar(x=KBar_df['Time'], y=KBar_df['Volume'], name='成交量', marker=dict(color='black')),secondary_y=False)  ## secondary_y=False 表示此圖形的y軸scale是在左邊而不是在右邊
    fig.add_trace(go.Scatter(x=KBar_df['Time'][last_nan_index_MA+1:], y=KBar_df['MA_long'][last_nan_index_MA+1:], mode='lines',line=dict(color='orange', width=2), name=f'{LongMAPeriod}-根 K棒 移動平均線'), 
                  secondary_y=True)
    fig.add_trace(go.Scatter(x=KBar_df['Time'][last_nan_index_MA+1:], y=KBar_df['MA_short'][last_nan_index_MA+1:], mode='lines',line=dict(color='pink', width=2), name=f'{ShortMAPeriod}-根 K棒 移動平均線'), 
                  secondary_y=True)
    fig.layout.yaxis2.showgrid=True

    st.plotly_chart(fig, use_container_width=True)

with st.expander("長短RSI"):

    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig2.add_trace(go.Scatter(x=KBar_df['Time'][last_nan_index_RSI+1:], y=KBar_df['RSI_long'][last_nan_index_RSI+1:], mode='lines',line=dict(color='blue', width=2), name=f'{LongRSIPeriod}-根 K棒 移動RSI'), 
                  secondary_y=True)
    fig2.add_trace(go.Scatter(x=KBar_df['Time'][last_nan_index_RSI+1:], y=KBar_df['RSI_short'][last_nan_index_RSI+1:], mode='lines',line=dict(color='green', width=2), name=f'{ShortRSIPeriod}-根 K棒 移動RSI'), 
                  secondary_y=True)
    
    fig2.layout.yaxis2.showgrid=True    

    st.plotly_chart(fig2, use_container_width=True)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    