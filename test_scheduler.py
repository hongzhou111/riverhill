import time
from schedule import repeat, every, run_pending
from test_rocketfinancial import RocketFin

#@repeat(every(10).seconds)
#@repeat(every(5).seconds)
@repeat(every().day.at("22:00"))
def run_task():
    #print("Sending email...")
    r = RocketFin()
    r.run()

while True:
    run_pending()
    time.sleep(1)