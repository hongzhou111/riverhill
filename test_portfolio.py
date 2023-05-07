from test_ga import RuleGA
from datetime import datetime
from bson import json_util

if __name__ == '__main__':
    save_p_flag = 0
    new_end_date = '2020-01-31'
    ga = RuleGA(save_p_flag)
    ga.reload('testP_02', new_end_date)
    #print(ga.getTotal('2020-01-10'))
    print(json_util.dumps(ga.p, indent=4))

    ga.generation()
    print(json_util.dumps(ga.p, indent=4))

    '''
    init_date = '2019-05-16'
    end_date = '2020-01-10'
    save_p_flag = 1
    init_cash = 0
    init_list = [
        {'symbol': 'LYFT',
         'shares': 909},
        {'symbol': 'TTD',
         'shares': 250},
        {'symbol': 'AYX',
         'shares': 550},
        {'symbol': 'ISRG',
         'shares': 180},
        {'symbol': 'CRM',
         'shares': 600},
        {'symbol': 'ATVI',
         'shares': 700},
        {'symbol': 'MDB',
         'shares': 664},
        {'symbol': 'SQ',
         'shares': 1350},
        {'symbol': 'BABA',
         'shares': 400},
        {'symbol': 'AAPL',
         'shares': 200},
        {'symbol': 'TCEHY',
         'shares': 1600},
        {'symbol': 'FB',
         'shares': 333},
        {'symbol': 'AMZN',
         'shares': 40},
        {'symbol': 'TSLA',
         'shares': 300},
        {'symbol': 'ANTM',
         'shares': 5430},
        {'symbol': 'COST',
         'shares': 49},
        {'symbol': 'GS',
         'shares': 37},
        {'symbol': 'GE',
         'shares': 126}
    ]

    csList = [-80]
    cpsList = [1000]
    cbList = [1000]
    # msList = [-10, -20, -40]
    msList = [-10]
    #mpsList = [-50]
    mpsList = [-10]   #-10
    #mbList = [1]
    mbList = [5]
    mbgList = [20]

    i = 2
    restart = 1
    stop = 150000
    ga = RuleGA(save_p_flag)

    for cs in csList:
        for cps in cpsList:
            for cb in cbList:
                for ms in msList:
                    for mps in mpsList:
                        for mb in mbList:
                            for mbg in mbgList:
                                if i >= restart and i <= stop:
                                    startTime = datetime.now()

                                    ga_name = 'testP_' + format(i, '02d')
                                    print(i, ga_name)
                                    ga.init(ga_name, init_date, end_date, init_cash, init_list)
                                    ga.p['crossover_sr_sell_threshold'] = cs
                                    ga.p['crossover_profit_sell_threshold'] = cps
                                    ga.p['crossover_g_buy_threshold'] = cb
                                    ga.p['mutate_sell_sr_threshold'] = ms
                                    ga.p['mutate_perf_sell_g_threshold'] = mps
                                    ga.p['mutate_buy_sr_threshold'] = mb
                                    ga.p['mutate_buy_g_threshold'] = mbg

                                    # print(ga.p)
                                    ga.generation()
                                    print(json_util.dumps(ga.p, indent=4))

                                    endTime = datetime.now()
                                    runTime = endTime - startTime
                                    print('run time', runTime)
                                i = i + 1
    '''
