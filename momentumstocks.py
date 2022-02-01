#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug  1 08:57:35 2021
momentum strategy
@author: vishwanath
"""

import yfinance as yf
import numpy as np
import datetime as dt

import pandas as pd

import datetime
import os
from scipy import stats
import traceback
import matplotlib.pyplot as plt
import json
import logging 

# os.chdir('/root/cronjobs/momentumtrading/')

# Reading config file
f = open ('config_momentum.json', "r")
config_data = json.loads(f.read())
print(config_data)

#Create and configure logger 
logging.basicConfig(filename="moment_log.log", 
					format='%(asctime)s %(message)s', 
					filemode='a') 

#Creating an object 
logger=logging.getLogger() 

#Setting the threshold of logger to DEBUG 
logger.setLevel(logging.INFO) 

#Test messages 

logger.info("Just an information Script Started")

x = datetime.datetime.now()
print("Script execution started at",str(x))





def cal_percent(openprice , closeprice):
    x = closeprice -openprice
    return (x/openprice) *100


def computeRSI (data, time_window):
    diff = data.diff(1).dropna()        # diff in one field(one day)

    #this preservers dimensions off diff values
    up_chg = 0 * diff
    down_chg = 0 * diff
    
    # up change is equal to the positive difference, otherwise equal to zero
    up_chg[diff > 0] = diff[ diff>0 ]
    
    # down change is equal to negative deifference, otherwise equal to zero
    down_chg[diff < 0] = diff[ diff < 0 ]
    

    up_chg_avg   = up_chg.ewm(com=time_window-1 , min_periods=time_window).mean()
    down_chg_avg = down_chg.ewm(com=time_window-1 , min_periods=time_window).mean()
    
    rs = abs(up_chg_avg/down_chg_avg)
    rsi = 100 - 100/(1+rs)
    return rsi


def computeCloud (data):
    if data.Close > data.MovingAVG:
        return 1
    
    return 0


def computeCloud (data):
    if data.Close > data.MovingAVG:
        return 1
    
    return 0


def savetoImg(data ,name):
    # plt.axis('off')
    plt.plot(data.index, data['Close'],linewidth =1)
        
        #SAVE as png
    path ="images/"
    if config_data['debug'] == 0 :
        path = '/var/www/html/images/'
    
    fig1 = plt.gcf()
    fig1.suptitle(name, fontsize=20)
    fig1.savefig(path + name+ '.png')
    plt.clf()
    plt.cla()
    plt.close()



liststocks = pd.read_csv('nifty500.csv')
liststocks = liststocks['name'].tolist()

# liststocks = ['TATACONSUM' , 'INFY','TCS','DMART','GLAND','YESBANK','SWSOLAR','CAMLINFINE','INFY']
# liststocks = ["DMART" , 'ALKEM', 'DIXON','YESBANK','ZEEL'] 
tickers={}

TODAY = "2021-11-22"
datetime_object = dt.datetime.strptime(TODAY, '%Y-%m-%d')


for name in liststocks: 
    try:
        result = []
        
        # periods = ['1mo','3mo','6mo','1y']
        periods = [30,90,180,365]
        percentile = [1,3,6,12]
        i=0
        rsi = 0
        abovecloudscore = 0
        percentilerank = 0
        for per in periods:
            # ohlcv = yf.download(name +'.NS',period=per,interval= '1mo')
            ohlcv = yf.download(name +'.NS',datetime_object -dt.timedelta(per),datetime_object)
            if per ==365:
                savetoImg(ohlcv , name)
            calcloud=ohlcv
            openprice = ohlcv.iloc[0]['Open']
            closeprice = ohlcv.iloc[len(ohlcv) -1 ]['Close']
            percentchange= cal_percent(openprice, closeprice)
            result.append(percentchange)
            
            # Calculate RSI
            if per  == 180 :
                ohlcv['RSI'] = computeRSI(ohlcv['Adj Close'], 14)
                rsi =   ohlcv.iloc[len(ohlcv) -1 ]['RSI']
             
            # Calculate ABOVE CLOUD
            calcloud['MovingAVG'] = calcloud['Close'].rolling(window=52).mean()
            calcloud['AbvCloud'] = calcloud.apply(lambda x: computeCloud(x), axis=1)
            if per== 365:
                abovecloudscore = sum(calcloud['AbvCloud'])
                total = len(ohlcv) - 52 
                abovecloudscore =abovecloudscore / total
                abovecloudscore = abovecloudscore*100
                
            # Calculate the Percentile RSI 
            if per  == 180:
               percentilerank = stats.percentileofscore(ohlcv['RSI'].dropna(), ohlcv.iloc[len(ohlcv) -1 ]['RSI'], 'rank')
               tmp = ohlcv
            

            
            i = i+1


        i=0
        sumofper= 0
        for x in percentile:
            sumofper =sumofper + (result[i]/x )
            i = i + 1
        
        #TODO
        result.append(sumofper/len(result))
        result.append(rsi)
        result.append(abovecloudscore)
        result.append(percentilerank)

        tickers[name] = result
        

        
    except Exception as ex:
        print(ex)#raised if `y` is empty.
        print("ERROR: ", name)
        logger.info("ERROR: "+ name)
        logger.info(ex)
        liststocks.remove(name)
        traceback.print_exc()


df=pd.DataFrame.from_dict(tickers,orient='index')
df = df.reset_index()

#TODO
df.columns =['name','1month', '3months', '6months', '1year', 'Mommentum Score','RSI','AboveCloud','PecentileRSI']
# df = df.sort_values('Mommentum Score',ascending=False)

df = df.dropna()

savepath = ""
if config_data['debug'] == 0:
    savepath = "/root/myproject/"

df.to_csv( savepath+ "momentumresults.csv",index=False)

logger.info("Script Started Ended")


