'''
Test Run GA Algorithm with RL and CWH

Change History:
2023/02/17      created
'''
#import math
from datetime import datetime
#from test_mongo import MongoExplorer
from test_ga_v3 import RuleGA

if __name__ == '__main__':
    startTime = datetime.now()

    init_date = '2010-10-01'  # '05-31'
    end_date = '2023-04-26'
    #init_list = [{'symbol': 'TSLA', 'shares': 250000}]
    save_p_flag = 1
    #save_p_flag = 0

    rg = RuleGA(save_p_flag)
    ga_name = 'test_GA_V3_2'  # test ga with investment_cap
    rg.init(ga_name, init_date, end_date)
    rg.generation()

    endTime = datetime.now()
    runTime = endTime - startTime
    print('run time', runTime)

