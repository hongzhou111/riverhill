'''
Daily run of ga_macd_rl_daily_01
'''
from bson import json_util
from datetime import datetime
from datetime import timedelta
from test_ga_macd_rl import RuleGA_MACD_RL
from test_macd import MACD

if __name__ == '__main__':
    startTime = datetime.now()

    m = MACD()
    m.update_all()

    init_date = startTime.strftime('%Y-%m-%d')
    end_date = (startTime + timedelta(days=1)).strftime('%Y-%m-%d')
    #init_date = '2021-09-22'
    #end_date = '2021-09-23'
    init_cash = 200000
    #init_list = []
    init_list = [{'symbol': 'BKNG', 'shares': 50}]
    save_p_flag = 1

    ga = RuleGA_MACD_RL(save_p_flag)
    ga_name = 'test_GA_MACD_RL_Daily_01'
    p = ga.reload(ga_name, end_date)
    if p is None:
        ga.init(ga_name, init_date, end_date, init_cash, init_list)

    #print(json_util.dumps(ga.p, indent=4))

    ga.generation()
    #print(json_util.dumps(ga.p, indent=4))
    #print(ga.getTotalPerf())

    #print(ga.getCAPList('2013-06-14'))

    init_cash2 = 319108
    init_list2 = [{'symbol': 'COUP', 'shares': 300},
                 {'symbol': 'TWLO', 'shares': 250},
                 {'symbol': 'ROKU', 'shares': 200},
                 {'symbol': 'OKTA', 'shares': 200},
                 {'symbol': 'AYX', 'shares': 550},
                 {'symbol': 'ATVI', 'shares': 700},
                 {'symbol': 'BABA', 'shares': 400},
                 {'symbol': 'TCEHY', 'shares': 1600},
                 {'symbol': 'PAYC', 'shares': 300},
                 {'symbol': 'GS', 'shares': 37},
                 {'symbol': 'GE', 'shares': 15}
                 ]
    ga2 = RuleGA_MACD_RL(save_p_flag)
    ga_name2 = 'test_GA_MACD_RL_Daily_02'
    p2 = ga2.reload(ga_name2, end_date)
    if p2 is None:
        ga2.init(ga_name2, init_date, end_date, init_cash2, init_list2)

    #print(json_util.dumps(ga2.p, indent=4))

    ga2.generation()
    endTime = datetime.now()
    runTime = endTime - startTime
    print('run time', runTime)
