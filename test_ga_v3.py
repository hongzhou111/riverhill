'''
GA Algorithm with RL and CWH

gene:                               buy/sell decision models(RL, CWH )
chromesome:                         stock(s)
Population:                         portfolio(p = stocks)
fitness:                            RL_MACD, CWH, G20
initialization:                     buy # stocks, each for 100k
generation:
    run portfolio                   1. mutate sell
                                    2. cross sell
                                    3. cross buy
    run all                         1. mutate buy

    repeat generation               daily

Change History:
2023/02/17      created
2023/03/02      all params:
                Fundamentals
                1.1 CAP_Threshold (> 0.2 B)
                1.2 G20_Year (>1)
                Performance
                2.1 G20_Threshold (>20)
                2.2 G1_Threshold (>0)
                2.3 Price_Higest_Ratio (>0.1)
                RL/CWH
                4.1 predict_date (<7)
                4.2 RL_Model_Score (>1.05)
                4.3 Buy_and_Hold_Perf (>1)
                4.4 Model_Perf (>1.2)
                4.5 MACD (short, long signal) - (3, 7, 10)
                4.6 macd_threshold (0)
                4.7 macd_min_len (>0)
                4.8 cwh_threadhold (>0.8)
                Portifolio
                5.1 hold_time (> 30 days, perf > 1)
                5.2 hold_min_perf (>1)
                5.3 mutate_sell_threshold (>0.8)
                5.4 investment_cap (10000000)
                5.5 stock_count_max (80)
                5.6 stock_mutate_sell_count (5)
                5.7 invest_time (>30)
                5.8 check_stock_count_days (21)

2023/03/07      1. add g20.Recommention == '' constrain for cwh mutate buy
                2. if g20.cross_sell conflicts cwh.cross_buy,  take g20.cross_sell
2023/03/12      add investment_cap = 10000000
2023/03/15      add stock_count_max = 100,  sort the stocks by perf for invest_time > 30,  mutate_sell the lowerst stocks if count > stock_count_max
2023/03/16      for run_all add sort for the stocks, sorted by G20 desc
2023/04/26      for stock_count mutate sell,  check stock perf every 5 days (check_stock_count_days), mutate_selel the lowerest stocks if count > stock_count_max, otherwise mutate_sell last stock_mutatel_sell_count
'''
import math
from datetime import datetime
from test_mongo import MongoExplorer
from test_ga_macd_rl_v2 import RuleGA_MACD_RL
from test_cup_with_handle import Rule_Cup_with_Handle
import pandas as pd

class RuleGA:
    def __init__(self, save_p_flag=0):
        mongo_client = MongoExplorer()
        self.mongoDB = mongo_client.mongoDB
        self.save_p_flag = save_p_flag
        self.ga = RuleGA_MACD_RL(save_p_flag)

    def get_invest_time(self, action_list, aaod):
        result = 0

        #action_list.reverse()
        i = len(action_list) - 1
        while i >= 0:
            a = action_list[i]
            if a['reason'] == 'mutate_buy':
                result = (datetime(*(int(s) for s in aaod.split('-'))) - datetime(*(int(s) for s in a['date'].split('-')))).days
                break
            i = i -1

        return result

    def check_stock_count(self, aaod):
        stock_df = pd.DataFrame(columns=['symbol', 'perf'])
        for i, s in enumerate(self.ga.p['stocks']):
            #print(s['symbol'], s['actions'], self.get_invest_time(s['actions'], aaod))
            if s['share'] > 0 and self.get_invest_time(s['actions'], aaod) > 30:  #s['cash'] > 0 or
                perf = self.ga.getPerf(s['symbol'], aaod)
                stock_df =stock_df.append({'symbol': s['symbol'], 'perf': perf}, ignore_index=True)
        stock_df = stock_df.sort_values('perf', ascending=False)
        #print(stock_df.head(500))
        l = len(stock_df.index)
        if l >= 80:
            endI = 75
        elif l >= 30:
            endI = -5
        else:
            endI = l
        mutate_sell_stocks = stock_df.iloc[endI:]
        #print(mutate_sell_stocks.tail(500))
        if not mutate_sell_stocks.empty:
            mutate_sell_stock_list = mutate_sell_stocks['symbol'].values.tolist()
        else:
            mutate_sell_stock_list = []
        return mutate_sell_stock_list

    def init(self, ga_name, init_date, end_date):
        if self.ga.reload(ga_name, end_date, mutate_sell_threshold=0.8) is None:
            self.ga.init(ga_name, init_date, end_date)

    def run_portfolio(self, aaod, check_stock_count=False):
        self.ga.plist = []

        execute_cross_sell_flag = 0
        execute_cross_buy_flag = 0
        execute_mutate_sell_flag = 0

        if check_stock_count is True:
            mutate_sell_stock_list = self.check_stock_count(aaod)
        else:
            mutate_sell_stock_list = []

        for i, s in enumerate(self.ga.p['stocks']):
            if s['share'] > 0 or s['init_investment'] > 0:  #s['cash'] > 0 or
                self.ga.plist.append(s['symbol'])

            reason = ''
            fitness = ''
            perf = self.ga.getPerf(s['symbol'], aaod)
            last_buy_days = self.ga.getHoldingDuration(self.ga.p['stocks'][i]['actions'], 'buy', aaod)
            print(s['symbol'], s['share'], s['init_investment'], aaod, perf, last_buy_days)

            if s['symbol'] in mutate_sell_stock_list:
                reason = 'mutate_sell'
                fitness = {"reason": 'check_stock_count'}
            elif perf > 0 and perf < self.ga.p['mutate_sell_threshold'] and s['share'] > 0:      # and perf > 0:  # mutate sell
                reason = 'mutate_sell'
                fitness = {"perf": perf}
            elif s['share'] > 0 and last_buy_days > self.ga.p['hold_time'] and perf < 1 and perf > 0:  # if holding 90 days and no gain mutate sell
                reason = 'mutate_sell'
                fitness = {"perf": perf}

            if reason == '' and (s['share'] > 0 or s['init_investment'] > 0):
                cwh = Rule_Cup_with_Handle(aaod)
                cwh_rr = cwh.trade_with_cwh(ticker=s['symbol'], aaod=aaod, look_back=120, cwh_back=20)
                for ii, rr in cwh_rr.iterrows():
                    if ii > 0: break
                    if rr['cwh_sign'] == 2:     # mutate sell
                        reason = 'mutate_sell'
                        fitness = {"cwh_sign": rr['cwh_sign'], "pearson": rr['pearson'], "sigma": rr['sigma'], "end_date": rr['end_date'], "perf": perf}
                    if rr['cwh_sign'] == 1:  # cross buy
                        reason = 'cross_buy'
                        fitness = {"cwh_sign": rr['cwh_sign'], "pearson": rr['pearson'], "sigma": rr['sigma'], "end_date": rr['end_date']}

            if (reason == '' and (s['share'] > 0 or s['init_investment'] > 0)) or (reason == 'cross_buy' and fitness != '' and fitness.get('cwh_sign') == 1):
                f = self.ga.fitness(s['symbol'], aaod, run_rl=2, g20_threshold=self.ga.p['g20_threshold'])
                if f is not None and f['rl_result']['predict_action'] >= 1 and f['rl_result']['predict_action'] < 2:        #cross sell
                    reason = 'cross_sell'
                    fitness = f
                elif f is not None and f['rl_result']['predict_action'] >= 0 and f['rl_result']['predict_action'] < 1:      # and f['Recommendation'] == '':  # cross buy
                    reason = 'cross_buy'
                    fitness = f

            if reason == 'cross_sell' or reason == 'mutate_sell':
                sell_share = (-1) * s['share']
                sell_price = self.ga.getSellPrice(s['symbol'], aaod)
                if sell_share < 0 and sell_price > 0:
                    sell_position = sell_price * sell_share
                else:
                    sell_position = 0

                if sell_position < 0:
                    # update p
                    self.ga.p['last_update_date'] = aaod
                    self.ga.p['stocks'][i]['share'] = 0
                    #self.ga.p['stocks'][i]['cash'] = self.ga.p['stocks'][i]['cash'] - sell_position
                    self.ga.p['p_cash'] = self.ga.p['p_cash'] - sell_position

                    if reason == 'cross_sell':
                        execute_cross_sell_flag = 1
                    else:  # mutate sell
                        execute_mutate_sell_flag = 1
                        #self.ga.p['p_cash'] = self.ga.p['p_cash'] + self.ga.p['stocks'][i]['cash']
                        #self.ga.p['stocks'][i]['cash'] = 0
                        self.ga.p['stocks'][i]['init_investment'] = 0

                    sell_action = {
                        "date": aaod,
                        "action_type": "sell",
                        "reason": reason,
                        "fitness": fitness,
                        "price": sell_price,
                        "share": sell_share,
                        "value": sell_position
                    }
                    print(sell_action)
                    self.ga.p['stocks'][i]['actions'].append(sell_action)

            elif reason == 'cross_buy' and s['share'] == 0 and s['init_investment'] > 0:
                last_sell_action = self.ga.getLastAction(s['actions'], 'sell')

                #if s['cash'] > 0:
                if last_sell_action != None and last_sell_action['reason'] == 'cross_sell':
                    buy_price = self.ga.getBuyPrice(s['symbol'], aaod)
                    if buy_price > 0:
                        #buy_share = math.floor(s['cash'] / buy_price)
                        buy_share = math.floor(((-1) * last_sell_action['value']) / buy_price)
                        buy_position = buy_price * buy_share
                        if buy_position > 0:
                            buy_action = {
                                "date": aaod,
                                "action_type": "buy",
                                "reason": reason,
                                "fitness": fitness,
                                "price": buy_price,
                                "share": buy_share,
                                "value": buy_position
                            }
                            print(buy_action)

                            new_share = s['share'] + buy_share
                            # update p
                            self.ga.p['last_update_date'] = aaod
                            self.ga.p['stocks'][i]['share'] = new_share
                            self.ga.p['stocks'][i]['actions'].append(buy_action)
                            #self.ga.p['stocks'][i]['cash'] = self.ga.p['stocks'][i]['cash'] - buy_position

                            if self.ga.p['p_cash'] >= buy_position:
                                self.ga.p['p_cash'] = self.ga.p['p_cash'] - buy_position
                            else:
                                self.ga.p['investment'] = self.ga.p['investment'] + buy_position - self.ga.p['p_cash']
                                self.ga.p['p_cash'] = 0
                            execute_cross_buy_flag = 1

        return execute_cross_sell_flag, execute_mutate_sell_flag, execute_cross_buy_flag


    def run_all(self, aaod):
        execute_mutate_buy_flag = 0
        clist = self.mongoDB['stock_g20'].find({'AAOD': aaod, 'Recommendation': ''}, no_cursor_timeout=True).sort('G20', -1)
        clen = self.mongoDB['stock_g20'].count_documents({'AAOD': aaod, 'Recommendation': ''})
        if clen < 100:
            mongo_col = self.mongoDB['etrade_companies']
            mongo_query = {'status': 'active'}
            clist = mongo_col.find(mongo_query, no_cursor_timeout=True)
            source = 'etrade_companies'
        else:
            source = 'stock_g20'
        print('\n', source)

        s = ''
        for i in clist:
            if source == 'etrade_companies':
                s = i['Yahoo_Symbol']
            elif source == 'stock_g20':
                s = i['symbol']

            reason = ''
            fitness = ''
            if s != '' and s not in self.ga.plist:
                if (self.ga.p['investment'] - self.ga.p['p_cash']) > 10000000: break
                print(s, aaod)

                f = self.ga.fitness(s, aaod, run_rl=1, g20_threshold=self.ga.p['g20_threshold'])
                if f is not None and f['rl_result']['predict_action'] < 1 and f['rl_result']['predict_action'] >= 0 and f['Recommendation'] == '' and f['G20'] >= 20:
                    reason = 'mutate_buy'
                    fitness = f

                if reason == '' and f is not None and f['Recommendation'] == '':
                    cwh = Rule_Cup_with_Handle(aaod)
                    cwh_rr = cwh.trade_with_cwh(ticker=s, aaod=aaod, look_back=120, cwh_back=20)
                    for ii, rr in cwh_rr.iterrows():
                        if ii > 0: break
                        if rr['cwh_sign'] == 1:  # cross buy
                            reason = 'mutate_buy'
                            fitness = {"cwh_sign": rr['cwh_sign'], "pearson": rr['pearson'], "sigma": rr['sigma'],
                                       "end_date": rr['end_date']}

                if reason == 'mutate_buy':
                    buy_price = self.ga.getPrice(s, aaod)
                    if buy_price > 0:
                        buy_share = math.floor(100000 / buy_price)
                        buy_position = buy_price * buy_share
                        if buy_position > 0:
                            existing_stock = 0
                            for pi, ps in enumerate(self.ga.p['stocks']):
                                if ps['symbol'] == s:
                                    #if ps['cash'] == 0 and ps['share'] == 0:
                                    if ps['init_investment'] == 0 and ps['share'] == 0:
                                        buy_action = {
                                            "date": aaod,
                                            "action_type": "buy",
                                            "reason": reason,
                                            "fitness": fitness,
                                            "price": buy_price,
                                            "share": buy_share,
                                            "value": buy_position
                                        }
                                        print(buy_action)

                                        new_share = ps['share'] + buy_share
                                        # update p
                                        self.ga.p['last_update_date'] = aaod
                                        self.ga.p['stocks'][pi]['share'] = new_share
                                        self.ga.p['stocks'][pi]['actions'].append(buy_action)
                                        self.ga.p['stocks'][pi]['init_investment'] = self.ga.p['stocks'][pi]['init_investment'] + buy_position
                                        execute_mutate_buy_flag = 1

                                    existing_stock = 1
                                    break
                            if existing_stock == 0:
                                stock = {
                                    "symbol": s,
                                    "share": buy_share,
                                    #"cash": 0,
                                    "init_investment": buy_position,
                                    "actions":
                                        [
                                            {
                                                "date": aaod,
                                                "action_type": "buy",
                                                "reason": reason,
                                                "fitness": fitness,
                                                "price": buy_price,
                                                "share": buy_share,
                                                "value": buy_position
                                            }
                                        ]
                                }
                                print(stock)
                                # update p
                                self.ga.p['last_update_date'] = aaod
                                self.ga.p['stocks'].append(stock)
                                execute_mutate_buy_flag = 1

                            if self.ga.p['p_cash'] >= buy_position:
                                self.ga.p['p_cash'] = self.ga.p['p_cash'] - buy_position
                            else:
                                self.ga.p['investment'] = self.ga.p['investment'] + buy_position - self.ga.p['p_cash']
                                self.ga.p['p_cash'] = 0
        return execute_mutate_buy_flag

    def generation(self):
        mongo_query = {'$and': [{'Date': {'$gt': self.ga.p['last_update_date']}}, {'Date': {'$lte': self.ga.p['end_date']}}]}
        mongo_col_q = self.mongoDB.get_collection('AMZN')
        qDates = list(mongo_col_q.find(mongo_query).sort("Date", 1))

        index = 1
        restartIndex = 1
        stopIndex = 1500000
        for q in qDates:
            startTime = datetime.now()

            if index > stopIndex:
                break
            if index >= restartIndex:
                d = q['Date']
                print(index, d)

                if index % 5 == 0:
                    check_stock_count = True
                else:
                    check_stock_count = False

                crossover_sell_execute, mutate_sell_execute, crossover_buy_execute = self.run_portfolio(d, check_stock_count)
                mutate_buy_execute = self.run_all(d)

                execute_count = crossover_sell_execute + mutate_sell_execute + crossover_buy_execute + mutate_buy_execute
                if execute_count > 0 or index == stopIndex or index == len(qDates):
                    total = self.ga.getTotal(d)
                    self.ga.p['total'] = total
                    action = []
                    if crossover_sell_execute == 1:
                        action.append("Crossover_Sell")
                        self.ga.p['last_cross_sell_date'] = d
                    if mutate_sell_execute == 1:
                        action.append("Mutate_Sell")
                        self.ga.p['last_mutate_sell_date'] = d
                    if crossover_buy_execute == 1:
                        action.append("Crossover_Buy")
                        self.ga.p['last_cross_buy_date'] = d
                    if mutate_buy_execute == 1:
                        action.append("Mutate_Buy")
                        self.ga.p['last_mutate_buy_date'] = d
                    self.ga.p['total_history'].append({"date": d, "total": total, "action": action})

                    if index == stopIndex or index == len(qDates):
                        self.ga.p['last_update_date'] = d

                    if self.save_p_flag > 0:
                        self.ga.save_p()
                    self.ga.render(d)
                    print(self.ga.getTotalPerf())

            endTime = datetime.now()
            runTime = endTime - startTime
            print('run time: ', runTime, 'end time: ', endTime)

            index = index + 1

if __name__ == '__main__':
    startTime = datetime.now()

    init_date = '2010-10-01'  # '05-31'
    end_date = '2023-04-26'
    #init_list = [{'symbol': 'TSLA', 'shares': 250000}]
    save_p_flag = 1
    #save_p_flag = 0

    rg = RuleGA(save_p_flag)
    ga_name = 'test_GA_V3_1'  # test ga with RL and CWH
    rg.init(ga_name, init_date, end_date)
    rg.generation()

    endTime = datetime.now()
    runTime = endTime - startTime
    print('run time', runTime)

