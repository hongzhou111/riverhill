'''
History
2022/11/29 - add macd_crossing_by_threshold_min_len,  add cross_type for (normal, threhold);  normal is detected one day after, threhold is detected on the crossing day
2023/03/26 - use minute data from yfinance
'''
import pandas as pd
from stockstats import StockDataFrame as Sdf
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from datetime import timedelta
import traceback

class StockStats:
    def __init__(self, ticker, aaod=(datetime.now()+timedelta(days=1)).strftime("%Y-%m-%d"), interval='1m'):
        try:
            y = yf.Ticker(ticker)
            # get historical market data
            #df = y.history(period="max")
            if interval == '1d':
                end_date = (datetime(*(int(s) for s in aaod.split('-')))+timedelta(days=1)).strftime("%Y-%m-%d")
                #df = y.history(threads=False, start="1970-01-01", end=end_date)
                df = y.history(start="1970-01-01", end=end_date)
                df = df.reset_index()
            elif interval == '1m':
                df = y.history(period="7d", interval="1m")
                df = df.reset_index()
                df = df.rename(columns={"Datetime": "Date"})
            elif interval == 'no':
                df = pd.DataFrame()

            #df = yf.download(ticker, threads= False, start="1970-01-01", end=end_date)
            #df = y.history(end=aaod)
            #start_date = datetime.strptime('1970-01-01', '%Y-%m-%d')
            #end_date = datetime.strptime(aaod, '%Y-%m-%d')
            #df = pdr.get_data_yahoo(ticker, start=datetime(start_date.year, start_date.month, start_date.day), end=datetime(end_date.year, end_date.month, end_date.day))

            #current_hour = datetime.now().hour
            #if current_hour < 16:
                #last_day_df = yf.download(tickers=ticker, period='1d', interval='1m')
                #df.iloc[-1,:] = last_day_df.iloc[-1,:]
            #data   = pd.read_csv('data.csv')
            #self.stock = Sdf.retype(df, index_column='datetime')
            self.stock = Sdf.retype(df)
            #self.stock['date'] = self.stock.index
        except Exception as error:
            df = pd.DataFrame()
            #data   = pd.read_csv('data.csv')
            self.stock = Sdf.retype(df)
            # print(error)
            print(traceback.format_exc())
            pass

    def macd(self, short=None, long=None, signal=None):
        if not self.stock.empty:
            if short is not None:
                Sdf.MACD_EMA_SHORT = short
            if long is not None:
                Sdf.MACD_EMA_LONG = long
            if signal is not None:
                Sdf.MACD_EMA_SIGNAL = signal

            signal = self.stock['macds']        # signal line
            macd = self.stock['macd']         # The MACD that need to cross the signal line to give you a Buy/Sell signal
            macdh = self.stock['macdh']         # The MACD that need to cross the signal line to give you a Buy/Sell signal
            close = self.stock['close']

            s = self.stock
            s = s.reset_index()      #.reset_index()
            #dd = s['date']
            dd = s['date']
            #listLongShort = ["No data"]    # Since you need at least two days in the for loop
            macd_cross = [0]
            macd_sign = [0]
            start_close = [close[0]]
            start = [dd[0]]
            end = [dd[0]]
            max = [0]
            min = [0]
            r = [0]
            len = [0]
            accum = [0]
            peak = [dd[0]]
            flag = [0]

            macd_corr = pd.DataFrame()      #columns=['macds', 'start_close', 'start', 'end', 'max', 'min', 'macd_sign', 'len', 'accum', 'peak', 'pre_macds', 'pre_start_close','pre_start', 'pre_end', 'pre_max', 'pre_min', 'pre_macd_sign', 'pre_len', 'pre_accum', 'pre_peak']

            for i in range(1, s.shape[0]):
                # If the MACD crosses the signal line upward
                if macd[i] > signal[i] and macd[i - 1] <= signal[i - 1]:
                    #listLongShort.append("BUY")
                    sign = 1
                # The other way around
                elif macd[i] < signal[i] and macd[i - 1] >= signal[i - 1]:
                    #listLongShort.append("SELL")
                    sign = -1
                else:
                    sign = 0
                if sign == 1 or sign == -1:
                    macd_cross.append(sign)
                    macd_sign.append(sign)
                    start_close.append(close[i])
                    start.append(s.iloc[i]['date'])
                    end.append(s.iloc[i]['date'])
                    max.append(macdh[i])
                    min.append(macdh[i])
                    r.append(1)
                    len.append(1)
                    accum.append(macdh[i])
                    peak.append(s.iloc[i]['date'])

                    # search pre_macd
                    j = i - 1
                    while j > 1 and macd_cross[j] == 0:
                        j = j - 1

                    if j > 1:
                        #print(i, j-1, self.stock.iloc[j-1], macd_cross[j-1], macd_sign[j-1], start[j-1], end[j-1], max[j-1], min[j-1], len[j-1], accum[j-1], peak[j-1])
                        # flag the cross if pre_macd_max or pre_macd_min > 5% macdh
                        if macd_sign[j-1] == 1:
                            f = abs(max[j-1]) / abs(signal[j-1])
                        elif macd_sign[j-1] == -1:
                            f = abs(min[j-1]) / abs(signal[j-1])
                        else:
                            f = 0

                        if f > 0.1 and len[j-1] > 15:
                            flag = 1
                        else:
                            flag = 0

                        macd_corr_new_row = pd.DataFrame.from_records([{
                            'flag': flag,
                            'macds': signal[i-1],
                            'macd_sign': macd_sign[i-1],
                            'end_close': close[i-1],
                            'start': start[i-1],
                            'end': end[i-1],
                            'max': max[i-1],
                            'min': min[i-1],
                            'len': len[i-1],
                            'accum': accum[i-1],
                            'peak': peak[i-1],
                            'pre_macds': signal[j-1],
                            'pre_macd_sign': macd_sign[j-1],
                            'pre_end_close': close[j-1],
                            'pre_start': start[j-1],
                            'pre_end': end[j-1],
                            'pre_max': max[j-1],
                            'pre_min': min[j-1],
                            'pre_len': len[j-1],
                            'pre_accum': accum[j-1],
                            'pre_peak': peak[j-1]
                        }])
                        #}, ignore_index=True)
                        macd_corr = pd.concat([macd_corr, macd_corr_new_row])

                # copy from i-1 if not crossed
                else:
                    #listLongShort.append("HOLD")
                    macd_cross.append(0)
                    macd_sign.append(macd_sign[i-1])
                    start_close.append(start_close[i-1])
                    start.append(start[i-1])
                    end.append(s.iloc[i]['date'])
                    if macdh[i] > max[i-1]:
                        max.append(macdh[i])
                    else:
                        max.append(max[i-1])
                    if macdh[i] < min[i-1]:
                        min.append(macdh[i])
                    else:
                        min.append(min[i-1])
                    if macd_sign[i] == 1:
                        rr = macdh[i] / max[i]
                    elif macd_sign[i] == -1:
                        rr = macdh[i] / min[i]
                    else:
                        rr = 0
                    r.append(rr)
                    len.append(len[i-1] + 1)
                    accum.append(accum[i-1] + macdh[i])
                    if macd_sign[i] == 1 and macdh[i] > max[i-1]:
                        peak.append(s.iloc[i]['date'])
                    elif macd_sign[i] == -1 and macdh[i] < min[i-1]:
                        peak.append(s.iloc[i]['date'])
                    else:
                        peak.append(peak[i - 1])

            self.stock['macd_cross'] = macd_cross
            self.stock['macd_sign'] = macd_sign
            self.stock['start'] = start
            self.stock['end'] = end
            self.stock['max'] = max
            self.stock['min'] = min
            self.stock['r'] = r
            self.stock['len'] = len
            self.stock['accum'] = accum
            self.stock['peak'] = peak
            self.stock['h_s'] = macdh       #/close
            s['h_s'] = s['macdh']           #/s['close']

            # The advice column means "Buy/Sell/Hold" at the end of this day or
            #  at the beginning of the next day, since the market will be closed

            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', None)
            #print(self.stock)
            #print(macd_corr)

        '''
        #s = stock.reset_index()
        base = np.zeros(s.shape[0])
        macdh1 = s.loc[s['macdh'] >= 0]
        macdh2 = s.loc[s['macdh'] < 0]
        #print(macdh1)

        macd_corr1 = macd_corr.loc[macd_corr['pre_macd_sign'] == -1]
        macd_corr2 = macd_corr.loc[macd_corr['pre_macd_sign'] == 1]

        macd_corr11 = macd_corr.loc[(macd_corr['pre_macd_sign'] == -1) & (macd_corr['flag'] == 1)]
        macd_corr21 = macd_corr.loc[(macd_corr['pre_macd_sign'] == 1) & (macd_corr['flag'] == -1)]

        #print(macd_corr11)
        #print(macd_corr)
        #macd_ratio1 = pd.DataFrame()
        #macd_ratio1['r'] = macd_corr1['max']/macd_corr1['pre_min']
        #macd_ratio1 = macd_ratio1[macd_ratio1['r'] > -20]
        #macd_ratio2 = pd.DataFrame()
        #macd_ratio2['r'] = -1*macd_corr2['min']/macd_corr2['pre_max']
        #macd_ratio2 = macd_ratio2[macd_ratio2['r'] < 20]

        #print(macd_ratio1)

        #fig, axs = plt.subplots(3)
        fig, axs = plt.subplots(2)
        axs[0].plot(s['date'], s['close']/5, color='black', label='Price')
        axs[0].bar(macdh1['date'],10*macdh1['macdh'], color = 'g', width=4.0)
        axs[0].bar(macdh2['date'],10*macdh2['macdh'], color = 'r', width=4.0)
        axs[0].plot(s['date'], base, color='grey')

        axs[1].plot(s['date'], s['close'] / 5, color='black', label='Price')
        axs[1].bar(macdh1['date'],1000*macdh1['h_s'], color = 'g', width=4.0)
        axs[1].bar(macdh2['date'],1000*macdh2['h_s'], color = 'r', width=4.0)
        #axs[0].plot(s['date'],s['macd'], color = 'b', label = 'MACD')
        #axs[0].plot(s['date'],s['macds'], color = 'purple', label = 'MACDS')
        axs[1].plot(s['date'],base, color = 'grey')
        #axs[0].plot(macd_corr11['pre_end'], macd_corr11['pre_end_close']/5, 'o', color='g')
        #axs[0].plot(macd_corr21['pre_end'], macd_corr21['pre_end_close']/5, 'o', color='r')
        #plt.plot(s['date'],s['close']/10, color = 'black', label = 'Price')
        #plt.bar(macdh1['date'],500*macdh1['macdh']/macdh1['close'], color = 'g', width=4.0)
        #plt.bar(macdh2['date'],500*macdh2['macdh']/macdh2['close'], color = 'r', width=4.0)
        #plt.plot(s['date'],s['macd'], color = 'b', label = 'MACD')
        #plt.plot(s['date'],s['macds'], color = 'purple', label = 'MACDS')
        #plt.plot(s['date'],base, color = 'grey')

        #axs[1].plot(macd_corr1['pre_accum'], macd_corr1['max'], 'o', color='r')
        #axs[1].plot(macd_corr2['pre_accum'], macd_corr2['min'], 'o', color='g')
        #axs[1].plot(macd_corr1['pre_min'], macd_corr1['max'], 'o', color='r')
        #axs[1].plot(macd_corr2['pre_max'], macd_corr2['min'], 'o', color='g')

        #axs[1].plot(macd_corr11['pre_accum'], macd_corr11['max'], 'o', color='g')
        #axs[1].plot(macd_corr21['pre_accum'], macd_corr21['min'], 'o', color='r')
        #axs[1].plot(macd_corr11['pre_min'], macd_corr1['max'], 'o', color='r')
        #axs[1].plot(macd_corr21['pre_max'], macd_corr2['min'], 'o', color='g')

        #axs[2].hist(macd_ratio1['r'], bins=200, color='r')
        #axs[2].hist(macd_ratio2['r'], bins=200, color='g')

        #plt.plot(macd_corr['pre_accum'], macd_corr['accum'], 'o', color='b')
        #plt.plot(macd_corr1['pre_accum'], macd_corr1['max'], 'o', color='r')
        #plt.plot(macd_corr2['pre_accum'], macd_corr2['min'], 'o', color='g')
        #plt.plot(macd_corr1['pre_min'], macd_corr1['max'], 'o', color='b')
        #plt.plot(macd_corr2['pre_max'], macd_corr2['min'], 'o', color='black')
        #plt.plot(macd_corr1['pre_min']/macd_corr1['pre_start_close'], macd_corr1['max']/macd_corr1['start_close'], 'o', color='b')
        #plt.plot(macd_corr2['pre_max']/macd_corr2['pre_start_close'], macd_corr2['min']/macd_corr2['start_close'], 'o', color='black')
        #plt.legend()
        #plt.show(block=False)
        '''
    def macd_by_date(self, AAOD, short=None, long=None, signal=None):
        if short is not None:
            Sdf.MACD_EMA_SHORT = short
        if long is not None:
            Sdf.MACD_EMA_LONG = long
        if signal is not None:
            Sdf.MACD_EMA_SIGNAL = signal

        signal = self.stock['macds']        # signal line
        macd   = self.stock['macd']         # The MACD that need to cross the signal line to give you a Buy/Sell signal
        macdh   = self.stock['macdh']         # The MACD that need to cross the signal line to give you a Buy/Sell signal
        #macdh_c = 100 * self.stock['macdh']     #/ self.stock['close']
        macdh_c = self.stock['macdh']  # / self.stock['close']

        s = self.stock
        s = s.reset_index()      #.reset_index()
        d = s['date']
        #print(d)
        #pd.set_option('display.max_rows', None)
        #pd.set_option('display.max_columns', None)
        #pd.set_option('display.width', None)
        #pd.set_option('display.max_colwidth', None)
        #print(s)

        i = s.loc[s['date'] == AAOD].index[0]
        cross_num = 0
        current = i
        sign = 0
        macd_sign = 0
        max = macdh_c[i]
        max_date = d[i].strftime("%Y-%m-%d")
        min = macdh_c[i]
        min_date = d[i].strftime("%Y-%m-%d")
        peak = macdh_c[i]
        peak_date = d[i].strftime("%Y-%m-%d")
        accum = 0
        len = 0
        pre_macd_sign = 0
        pre_max = -1000000
        pre_max_date = ''
        pre_min = 1000000
        pre_min_date = ''
        pre_peak = 0
        pre_peak_date = ''
        pre_accum = 0
        pre_len = 0
        while i > 1 and cross_num < 2:
            #print(s.iloc[i], i)
            if cross_num == 0:
                if macdh_c[i] > max:
                    max = macdh_c[i]
                    max_date = d[i].strftime("%Y-%m-%d")
                if macdh_c[i] < min:
                    min = macdh_c[i]
                    min_date = d[i].strftime("%Y-%m-%d")
                s = signal[i]
                accum = accum + macdh_c[i]
                len = len + 1
            elif cross_num == 1:
                macd_sign = sign
                if macdh_c[i] > pre_max:
                    pre_max = macdh_c[i]
                    pre_max_date = d[i].strftime("%Y-%m-%d")
                if macdh_c[i] < pre_min:
                    pre_min = macdh_c[i]
                    pre_min_date = d[i].strftime("%Y-%m-%d")
                pre_signal = signal[i]
                pre_accum = pre_accum + macdh_c[i]
                pre_len = pre_len + 1

            # If the MACD crosses the signal line upward
            if macd[i] > signal[i] and macd[i - 1] <= signal[i - 1]:
                #listLongShort.append("BUY")
                cross_num = cross_num + 1
                sign = 1
            # The other way around
            elif macd[i] < signal[i] and macd[i - 1] >= signal[i - 1]:
                #listLongShort.append("SELL")
                cross_num = cross_num + 1
                sign = -1
            if cross_num == 2:
                pre_macd_sign = sign
                if pre_macd_sign == 1:
                    #pre_macd_strength = abs(pre_max) / abs(pre_signal)
                    pre_peak = pre_max
                    pre_peak_date = pre_max_date
                elif pre_macd_sign == -1:
                    #pre_macd_strength = abs(pre_min) / abs(pre_signal)
                    pre_peak = pre_min
                    pre_peak_date = pre_min_date
                else:
                    #pre_macd_strength = 0
                    pre_peak = 0
                    pre_peak_date = ''
            i = i - 1

        if macd_sign == 1:
            r = macdh_c[current] / max
            #print(macdh_c[current], max, r)
            #macd_strength = abs(max) / abs(s)
            peak = max
            peak_date = max_date
        elif macd_sign == -1:
            r = macdh_c[current] / min
            #macd_strength = abs(min) / abs(s)
            peak = min
            peak_date = min_date
        else:
            r = 0
            #macd_strength = 0
            peak = 0
            peak_date = ''

        result = {
            'macd_sign': macd_sign,
            'peak': peak,
            'peak_date': peak_date,
            'r': r,
            #'macd_strength': macd_strength,
            #'signal': s,
            'accum': accum,
            'len': len,
            'pre_macd_sign': pre_macd_sign,
            'pre_peak': pre_peak,
            'pre_peak_date': pre_peak_date,
            #'pre_macd_strength': pre_macd_strength,
            #'pre_signal': pre_signal,
            'pre_accum': pre_accum,
            'pre_len': pre_len
        }
        #print(result)
        return result

    def macd_crossing(self, short=None, long=None, signal=None):
        if 'macd_cross' not in self.stock.columns:
            self.macd(short, long, signal)

        s = self.stock
        s = s.reset_index()
        s['next_open'] = s['open'].shift(-1)
        s['next_high'] = s['high'].shift(-1)
        s['next_low'] = s['low'].shift(-1)
        s['next_close'] = s['close'].shift(-1)
        crossing = pd.DataFrame()      #columns=['macds', 'start_close', 'start', 'end', 'max', 'min', 'macd_sign', 'len', 'accum', 'peak', 'pre_macds', 'pre_start_close','pre_start', 'pre_end', 'pre_max', 'pre_min', 'pre_macd_sign', 'pre_len', 'pre_accum', 'pre_peak']

        for i in range(2, s.shape[0]):
            if s.iloc[i]['macd_cross'] == -1 or s.iloc[i]['macd_cross'] == 1:
                #crossing = crossing.append(s.iloc[[i-1]], ignore_index=True)
                crossing = pd.concat([crossing, s.iloc[[i - 1]]])
        #crossing.reset_index(drop=True, inplace=True)
        crossing.reset_index(inplace=True)
        return crossing

    def macd_crossing_by_threshold(self, short=None, long=None, signal=None, threshold=0.2):
        if 'macd_cross' not in self.stock.columns:
            self.macd(short, long, signal)

        s = self.stock
        s = s.reset_index()
        s['next_open'] = s['open'].shift(-1)
        s['next_high'] = s['high'].shift(-1)
        s['next_low'] = s['low'].shift(-1)
        s['next_close'] = s['close'].shift(-1)
        crossing = pd.DataFrame()      #columns=['macds', 'start_close', 'start', 'end', 'max', 'min', 'macd_sign', 'len', 'accum', 'peak', 'pre_macds', 'pre_start_close','pre_start', 'pre_end', 'pre_max', 'pre_min', 'pre_macd_sign', 'pre_len', 'pre_accum', 'pre_peak']

        status = 0      # corssing ending status, 0-normal crossing; 1-crossing if below threshold;
        crossing_index = 0
        for i in range(2, s.shape[0]):
            if s.iloc[i]['r'] < threshold and s.iloc[i]['len'] >= 5:
                if status == 0:
                #if (status == 0) | (status == 1 and i > crossing_index + 5):
                    #crossing = crossing.append(s.iloc[[i]], ignore_index=True)
                    crossing = pd.concat([crossing, s.iloc[[i]]])
                    status = 1
                    #crossing_index = i
            if (s.iloc[i]['macd_cross'] == -1 or s.iloc[i]['macd_cross'] == 1):
                if status == 0:
                    #crossing = crossing.append(s.iloc[[i-1]], ignore_index=True)
                    crossing = pd.concat([crossing, s.iloc[[i - 1]]])
                    #crossing_index = i
                else:
                    status = 0
        #crossing.reset_index(drop=True, inplace=True)
        crossing.reset_index(inplace=True)
        return crossing

    def macd_crossing_by_threshold_min_len(self, short=None, long=None, signal=None, threshold=0.0, min_len=0):
        if 'macd_cross' not in self.stock.columns:
            self.macd(short, long, signal)

        s = self.stock
        s = s.reset_index()
        s['next_open'] = s['open'].shift(-1)
        s['next_high'] = s['high'].shift(-1)
        s['next_low'] = s['low'].shift(-1)
        s['cross_type'] = 'normal'
        crossing = pd.DataFrame()      # columns=['macds', 'start_close', 'start', 'end', 'max', 'min', 'macd_sign', 'len', 'accum', 'peak', 'pre_macds', 'pre_start_close','pre_start', 'pre_end', 'pre_max', 'pre_min', 'pre_macd_sign', 'pre_len', 'pre_accum', 'pre_peak']

        status = 0      # corssing ending status, 0-normal crossing; 1-crossing if below threshold;
        for i in range(2, s.shape[0]):
            if s.iloc[i]['r'] < threshold and s.iloc[i]['len'] >= min_len:
                if status == 0:
                # if (status == 0) | (status == 1 and i > crossing_index + 5):
                    # crossing = crossing.append(s.iloc[[i]], ignore_index=True)
                    s.at[i, 'cross_type'] = 'threshold'
                    crossing = pd.concat([crossing, s.iloc[[i]]])
                    status = 1
                    #crossing_index = i
            if (s.iloc[i]['macd_cross'] == -1 or s.iloc[i]['macd_cross'] == 1) and s.iloc[i-1]['len'] >= min_len:
                if status == 0:
                    #crossing = crossing.append(s.iloc[[i-1]], ignore_index=True)
                    s.at[i-1, 'cross_type'] = 'normal'
                    crossing = pd.concat([crossing, s.iloc[[i-1]]])
                    #crossing_index = i
                else:
                    status = 0
        #crossing.reset_index(drop=True, inplace=True)
        crossing.reset_index(inplace=True)
        return crossing

    def macd_by_date_with_threshold(self, AAOD, short=None, long=None, signal=None, threshold=0.2):
        if short is not None:
            Sdf.MACD_EMA_SHORT = short
        if long is not None:
            Sdf.MACD_EMA_LONG = long
        if signal is not None:
            Sdf.MACD_EMA_SIGNAL = signal

        signal = self.stock['macds']        # signal line
        macd = self.stock['macd']         # The MACD that need to cross the signal line to give you a Buy/Sell signal
        macdh   = self.stock['macdh']         # The MACD that need to cross the signal line to give you a Buy/Sell signal
        #macdh_c = 100 * self.stock['macdh']     #/ self.stock['close']
        macdh_c = self.stock['macdh']  # / self.stock['close']

        s = self.stock
        s = s.reset_index()      #.reset_index()
        d = s['date']
        #print(d)
        #pd.set_option('display.max_rows', None)
        #pd.set_option('display.max_columns', None)
        #pd.set_option('display.width', None)
        #pd.set_option('display.max_colwidth', None)
        #print(s)

        i = s.loc[s['date'] == AAOD].index[0]
        cross_num = 0
        current = i
        sign = 0
        macd_sign = 0
        max = macdh_c[i]
        max_date = d[i].strftime("%Y-%m-%d")
        min = macdh_c[i]
        min_date = d[i].strftime("%Y-%m-%d")
        peak = macdh_c[i]
        peak_date = d[i].strftime("%Y-%m-%d")
        accum = 0
        len = 0
        pre_macd_sign = 0
        pre_max = -1000000
        pre_max_date = ''
        pre_min = 1000000
        pre_min_date = ''
        pre_peak = 0
        pre_peak_date = ''
        pre_accum = 0
        pre_len = 0
        while i > 1 and cross_num < 2:
            #print(s.iloc[i], i)
            if cross_num == 0:
                if macdh_c[i] > max:
                    max = macdh_c[i]
                    max_date = d[i].strftime("%Y-%m-%d")
                if macdh_c[i] < min:
                    min = macdh_c[i]
                    min_date = d[i].strftime("%Y-%m-%d")
                s = signal[i]
                accum = accum + macdh_c[i]
                len = len + 1
            elif cross_num == 1:
                macd_sign = sign
                if macdh_c[i] > pre_max:
                    pre_max = macdh_c[i]
                    pre_max_date = d[i].strftime("%Y-%m-%d")
                if macdh_c[i] < pre_min:
                    pre_min = macdh_c[i]
                    pre_min_date = d[i].strftime("%Y-%m-%d")
                pre_signal = signal[i]
                pre_accum = pre_accum + macdh_c[i]
                pre_len = pre_len + 1

            # If the MACD crosses the signal line upward
            if macd[i] > signal[i] and macd[i - 1] <= signal[i - 1]:
                #listLongShort.append("BUY")
                cross_num = cross_num + 1
                sign = 1
            # The other way around
            elif macd[i] < signal[i] and macd[i - 1] >= signal[i - 1]:
                #listLongShort.append("SELL")
                cross_num = cross_num + 1
                sign = -1
            if cross_num == 2:
                pre_macd_sign = sign
                if pre_macd_sign == 1:
                    #pre_macd_strength = abs(pre_max) / abs(pre_signal)
                    pre_peak = pre_max
                    pre_peak_date = pre_max_date
                elif pre_macd_sign == -1:
                    #pre_macd_strength = abs(pre_min) / abs(pre_signal)
                    pre_peak = pre_min
                    pre_peak_date = pre_min_date
                else:
                    #pre_macd_strength = 0
                    pre_peak = 0
                    pre_peak_date = ''
            i = i - 1

        if macd_sign == 1:
            r = macdh_c[current] / max
            #print(macdh_c[current], max, r)
            #macd_strength = abs(max) / abs(s)
            peak = max
            peak_date = max_date
        elif macd_sign == -1:
            r = macdh_c[current] / min
            #macd_strength = abs(min) / abs(s)
            peak = min
            peak_date = min_date
        else:
            r = 0
            #macd_strength = 0
            peak = 0
            peak_date = ''

        j = current - len + 1
        cross_num = 0
        jmax = 0
        post_threshold_flag = 0
        while j < current:
            if jmax < abs(macdh_c[j]):
                jmax = abs(macdh_c[j])
            r1 = abs(macdh_c[j]) / jmax

            #print(len, j, macdh_c[j], r1)
            if r1 < threshold:
                post_threshold_flag = 1
                break
            j = j + 1

        result = {
            'macd_sign': macd_sign,
            'peak': peak,
            'peak_date': peak_date,
            'r': r,
            #'macd_strength': macd_strength,
            #'signal': s,
            'accum': accum,
            'len': len,
            'post_threshold_flag': post_threshold_flag,
            'pre_macd_sign': pre_macd_sign,
            'pre_peak': pre_peak,
            'pre_peak_date': pre_peak_date,
            #'pre_macd_strength': pre_macd_strength,
            #'pre_signal': pre_signal,
            'pre_accum': pre_accum,
            'pre_len': pre_len
        }
        #print(result)
        return result

    def bollinger(self):
        boll = self.stock['boll']           # close_20_sma
        boll_ub = self.stock['boll_ub']     # upper band
        boll_lb = self.stock['boll_lb']     # lower band
        std = self.stock['close_{}_mstd'.format(Sdf.BOLL_PERIOD)]

        self.stock['bb_value'] = (self.stock['close'] - boll)/(2*std)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        print(self.stock[:100])

        s = self.stock
        s = s.reset_index()      #.reset_index()
        base = np.zeros(s.shape[0])
        #fig, axs = plt.subplots(3)
        fig, axs = plt.subplots(2)
        axs[0].plot(s['date'], s['close'], color='black', label='Price')
        axs[0].plot(s['date'], boll_ub, color='g')
        axs[0].plot(s['date'], boll_lb, color='g')
        axs[0].plot(s['date'], 100*s['bb_value'], color='r')

    def rsi(self, n=14):
        rsi = self.stock['rsi_{}'.format(n)]
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        #print(self.stock)

        s = self.stock
        s = s.reset_index()      #.reset_index()
        base = np.zeros(s.shape[0])
        #fig, axs = plt.subplots(3)
        fig, axs = plt.subplots(2)
        axs[0].plot(s['date'], s['close'], color='black', label='Price')
        axs[0].plot(s['date'], rsi, color='g')

if __name__ == '__main__':
    #ss = StockStats('TSLA')
    #ss = StockStats('AMZN')
    #ss = StockStats('FB')
    #ss = StockStats('AAPL')
    #ss = StockStats('ANTM')
    #ss = StockStats('SHOP')
    #ss = StockStats('RNG')
    #ss = StockStats('EYE')
    #ss = StockStats('CDLX')
    #ss = StockStats('APPN')
    #ss = StockStats('BAND')
    #ss.macd(6, 13, 9)
    #c = ss.macd_crossing()
    #c = ss.macd_crossing_by_threshold()
    #c.to_excel('macd_crossing.xlsx')
    #print(ss.stock)
    #print(c)

    #print(ss.macd_by_date('2020-09-18'))
    #ss.bollinger()
    #ss.rsi()
    #ss2 = StockStats('FB')
    #ss2.macd(13, 26)
    #ss3 = StockStats('FB')
    #ss3.macd(60, 200)
    #plt.show()
    #m = ss.macd_by_date(AAOD='2021-05-26', short=6, long=13, signal=9)
    #print(m)

    #aaod='2019-11-13'
    #ss = StockStats('WYNN', aaod)
    #ss = StockStats('ODFL')
    #ss = StockStats('BKNG')
    #ss = StockStats('DG')
    #ss = StockStats('AEIS')
    #ss = StockStats('NTES')
    ss = StockStats('TSLA')
    #ss = StockStats('TSLA', aaod)
    #ss.macd(6, 13, 9)
    #ss.macd(12, 26, 9)
    ss.macd(3, 7, 19)
    print(ss.stock)
    #print(ss.macd_by_date_with_threshold('2014-02-21'))
    #c = ss.macd_crossing()
    #c = ss.macd_crossing_by_threshold()
    # c.to_excel('macd_crossing.xlsx')
    #print(c)

    #c2 = ss.macd_crossing_by_threshold_min_len(threshold=0.5,min_len=6)
    c2 = ss.macd_crossing_by_threshold_min_len(threshold=0,min_len=0)
    print(c2)
    print(len(c2.loc[:, 'open'].values))

    current_step = 0
    print(c2.loc[current_step, "next_open"],c2.loc[current_step, "next_high"])
    next_date_index = c2.loc[current_step, "index"] + 1
    print(ss.stock.iloc[next_date_index]["open"], ss.stock.iloc[next_date_index]["high"])

