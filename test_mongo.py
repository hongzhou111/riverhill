import logging
import pymongo


class MongoExplorer:
    def __init__(self):
        mongo_client = pymongo.MongoClient('mongodb://192.168.1.160:27017/')
        self.mongoDB = mongo_client['riverhill']

if __name__ == '__main__':
    mongo = MongoExplorer()

    ss = ['MA', 'MSFT', 'PAYC', 'EVBG', 'SHOP', 'GOOGL', 'ANTM', 'AMZN', 'TSLA', 'AYX', 'TTD', 'SQ', 'LSXMB', 'FBIO']

    # mongo_query = {"Yahoo_Symbol": 'ANTM'}
    # mongo_query = {"Yahoo_Symbol": ss[len(ss) - 1]}
    #mongo_query = {}
    mongo_query = {"Yahoo_Symbol": ss[1]}

    coms = mongo.mongoDB['etrade_companies'].find(mongo_query)
    i = 1
    restartIndex = 1  # 2990
    stopIndex = 10000

    for x in coms:
        if i > stopIndex:
            break

        if i >= restartIndex:
            print(i, x['Symbol'])
        i = i + 1

