import requests
import json
from test_mongo import MongoExplorer
import logging
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import utc

class TS_Authenticator:
    def __init__(self, account_id, auth_code, public_key, private_key, refresh_token):
        self.mongo = MongoExplorer()
        self.collection = self.mongo.mongoDB["TS_auth"]

        self.account_id = account_id
        self.auth_code = auth_code
        self.public_key = public_key
        self.private_key = private_key
        self.refresh_token = refresh_token
        self.access_token = None
        self.query = {"account_id": account_id}
        self.dict = {"auth_code": auth_code, 
                    "public_key": public_key,
                    "private_key": private_key,
                    "refresh_token": refresh_token}

        self.auth_url = f"https://signin.tradestation.com/authorize?response_type=code&client_id={public_key}&redirect_uri=http%3A%2F%2Flocalhost&audience=https%3A%2F%2Fapi.tradestation.com&state=STATE&scope=openid+offline_access+profile+MarketData+ReadAccount+Trade+Crypto+Matrix+OptionSpreads"
        self.token_url = "https://signin.tradestation.com/oauth/token"

        self.collection.update_one(self.query, {"$set": self.dict}, upsert=True)

    def get_tokens(self):
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "authorization_code", "client_id": self.public_key, "client_secret": self.private_key, "code": self.auth_code, "redirect_uri": "http://localhost"}
        response = requests.post(self.token_url, headers=headers, data=data).json()

        self.access_token = response["access_token"]
        self.refresh_token = response["refresh_token"]
        return response["access_token"], response["refresh_token"], response["id_token"]

    def refresh(self):
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "refresh_token", "client_id": self.public_key, "client_secret": self.private_key, "refresh_token": self.refresh_token}
        response = requests.post(self.token_url, headers=headers, data=data)
        if response.status_code != 200:
                logging.warning(f"{response.text}")
        response = response.json()

        self.access_token = response["access_token"]
        newdict = {"access_token": self.access_token}
        self.dict.update(newdict)
        self.collection.update_one(self.query,
                {"$set": newdict}, upsert=True)
        return response["access_token"]

    def start_scheduler(self):
        executors = {
            'default': ThreadPoolExecutor(100),
            'processpool': ProcessPoolExecutor(8)
        }
        scheduler = BlockingScheduler(executors=executors, timezone=utc)
        scheduler.add_job(self.refresh, 'cron', 
                    day_of_week='mon-fri', minute="14-59/15", second="55")
        scheduler.start()


account_id = "11655345"
auth_code = "e37HZhkr8HBokHSw"
public_key = "r4bJ08Nbz9f8b6djDhoyCmazNnrrLFL4"
private_key = "hFBk8xgV_UGJEUFnxVW-AFz6YToqZwdvM-48x5wLUQhzKiR99r2w780hL0giBfvd"
refresh_token = "lzijZJe0VUnjFEzq6dqWK-Q3rqhzyoq7kkrDkqVoJvoYn"
ts_authenticator = TS_Authenticator(account_id, auth_code, public_key, private_key, refresh_token)

if __name__ == '__main__':
    logging.basicConfig(filename="tradestation_data/exceptions.log", format='%(asctime)s %(message)s')
    ts_authenticator.refresh()
    ts_authenticator.start_scheduler()