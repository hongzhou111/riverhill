import yfinance as yf
from test_mongo import MongoExplorer
from datetime import datetime
from datetime import timedelta

class StockCleaner:
    def __init__(self):
        mongo = MongoExplorer()
        self.mongoDB = mongo.mongoDB
        self.companies = self.mongoDB['etrade_companies']
        #mongo_query = {"Yahoo_Symbol": "BRK-A"}
        #mongo_query = {"Yahoo_Symbol": "TSLA"}
        mongo_query = {}
        self.tickers = self.companies.find(mongo_query)

    def cleanup(self):
        #mongo_query1 = {"Close": {"$type": "string"}}
        #mongo_query1 = {"Close": "null"}
        mongo_query1 = {}

        companyIndex = 1
        restartIndex = 1
        stopIndex = 10000

        for t in self.tickers:
            if companyIndex > stopIndex:
                break

            if companyIndex >= restartIndex:
                company = t["Yahoo_Symbol"]
                print(str(companyIndex) + ": " + company)
                mongo_col = self.mongoDB.get_collection(company)

                #if self.mongoDB[company].count_documents(mongo_query1) > 0:
                if mongo_col.count_documents(mongo_query1) > 0:
                    #print(self.mongoDB[company].find_one(mongo_query1))
                    #self.mongoDB[company].delete_many(mongo_query1)
                    print(mongo_col.find_one(mongo_query1))
                    #mongo_col.delete_many(mongo_query1)

            companyIndex = companyIndex + 1


    def cleanup_etrade_companies(self):
        day3 = datetime.now() + timedelta(days=-3)

        companyIndex = 1
        restartIndex = 1
        stopIndex = 10000000

        for t in self.tickers:
            if companyIndex > stopIndex:
                break

            if companyIndex >= restartIndex:
                company = t["Yahoo_Symbol"]
                print(str(companyIndex) + ": " + company)
                y = yf.Ticker(t['Yahoo_Symbol'])
                query = {'Yahoo_Symbol': t['Yahoo_Symbol']}
                try:
                    df = y.history(period="max")
                    df = df.reset_index()
                    print(df['Date'].iloc[-1])
                    #print(df, df.empty, df.shape, len(df))
                    if df.empty is not True and df['Date'].iloc[-1].timestamp() >= day3.timestamp():
                        newValue = {'$set': {'status': 'active'}}
                    else:
                        newValue = {'$set': {'status': 'inactive'}}
                        #drop ticker collection
                        qc = self.mongoDB[company]
                        qc.drop()
                    print(query, newValue)
                    self.companies.update_one(query, newValue)

                except Exception as error:
                #    print(error)
                    newValue = {'$set': {'status': 'inactive'}}
                    print('error', query, newValue)
                    self.companies.update_one(query, newValue)
                    #drop ticker collection
                    qc = self.mongoDB[company]
                    qc.drop()

            companyIndex = companyIndex + 1


if __name__ == '__main__':
    c = StockCleaner()
    #c.cleanup()
    c.cleanup_etrade_companies()
