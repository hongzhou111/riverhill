import logging
import pymongo
import pandas as pd

class MongoExplorer:
    def __init__(self):
        #mongo_client = pymongo.MongoClient('mongodb://192.168.1.160:27017/')
        mongo_client = pymongo.MongoClient('mongodb://192.168.1.181:27017/')
        self.mongoDB = mongo_client['riverhill']

if __name__ == '__main__':
    mongo = MongoExplorer()

    # ss = ['MA', 'MSFT', 'PAYC', 'EVBG', 'SHOP', 'GOOGL', 'ANTM', 'AMZN', 'TSLA', 'AYX', 'TTD', 'SQ', 'LSXMB', 'FBIO']

    # # mongo_query = {"Yahoo_Symbol": 'ANTM'}
    # # mongo_query = {"Yahoo_Symbol": ss[len(ss) - 1]}
    # #mongo_query = {}
    # mongo_query = {"Yahoo_Symbol": ss[1]}

    # coms = mongo.mongoDB['etrade_companies'].find(mongo_query)
    # i = 1
    # restartIndex = 1  # 2990
    # stopIndex = 10000

    # for x in coms:
    #     if i > stopIndex:
    #         break

    #     if i >= restartIndex:
    #         print(i, x['Symbol'])
    #     i = i + 1

    ticker = 'TSLA'
    collection = ticker + '_10sec_ts'      #mongodb colection name, TALA_10sec
    df = pd.read_csv("tradestation_data/tsla_2023_05_31_10sec.csv")     # row data in csv file, full path
    data_dict = df.to_dict("records")
    result = mongo.mongoDB[collection].insert_many(data_dict)

    df = pd.DataFrame(mongo.mongoDB[collection].find({"Symbol": "TSLA"}))
    print(df.head())
