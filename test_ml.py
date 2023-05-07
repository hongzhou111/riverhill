import yfinance as yf, pandas as pd, shutil, os, time, glob
import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from get_all_tickers import get_tickers as gt
from ta import add_all_ta_features
from ta.utils import dropna


# List of the stocks we are interested in analyzing. At the time of writing this, it narrows the list of stocks down to 44.
# If you have a list of your own you would like to use just create a new list instead of using this, for example: tickers = ["FB", "AMZN", ...]
tickers = gt.get_tickers_filtered(mktcap_min=150000, mktcap_max=10000000)

# Check that the amount of tickers isn't more than 2000
print("The amount of stocks chosen to observe: " + str(len(tickers)))

# These two lines remove the Stocks folder and then recreate it in order to remove old stocks. Make sure you have created a Stocks Folder the first time you run this.
shutil.rmtree("<Your Path>\\Bayesian_Logistic_Regression\\Stocks\\")
os.mkdir("<Your Path>\\Bayesian_Logistic_Regression\\Stocks\\")
#view rawATLR_GetTickers.py hosted with ❤ by GitHub


# These two lines remove the Stocks folder and then recreate it in order to remove old stocks. Make sure you have created a Stocks Folder the first time you run this.
shutil.rmtree("<Your Path>\\Bayesian_Logistic_Regression\\Stocks_Sub\\")
os.mkdir("<Your Path>\\Bayesian_Logistic_Regression\\Stocks_Sub\\")

# Get the Y values
list_files = (glob.glob("<Your Path>\\Bayesian_Logistic_Regression\\Stocks\\*.csv")) # Creates a list of all csv filenames in the stocks folder
for interval in list_files:
    Stock_Name = ((os.path.basename(interval)).split(".csv")[0])
    data = pd.read_csv(interval)
    dropna(data)
    data = add_all_ta_features(data, open="Open", high="High", low="Low", close="Close", volume="Volume")
    data = data.iloc[100:]
    close_prices = data['Close'].tolist()
    Five_Day_Obs = []
    thirty_Day_Obs = []
    sixty_Day_Obs = []
    x = 0
    while x < (len(data)):
        if x < (len(data)-5):
            if ((close_prices[x+1] + close_prices[x+2] + close_prices[x+3] + close_prices[x+4] + close_prices[x+5])/5) > close_prices[x]:
                Five_Day_Obs.append(1)
            else:
                Five_Day_Obs.append(0)
        else:
            Five_Day_Obs.append(0)
        x+=1
    y = 0
    while y < (len(data)):
        if y < (len(data)-30):
            ThirtyDayCalc = 0
            y2 = 0
            while y2 < 30:
                ThirtyDayCalc = ThirtyDayCalc + close_prices[y+y2]
                y2 += 1
            if (ThirtyDayCalc/30) > close_prices[y]:
                thirty_Day_Obs.append(1)
            else:
                thirty_Day_Obs.append(0)
        else:
            thirty_Day_Obs.append(0)
        y+=1
    z = 0
    while z < (len(data)):
        if z < (len(data)-60):
            SixtyDayCalc = 0
            z2 = 0
            while z2 < 60:
                SixtyDayCalc = SixtyDayCalc + close_prices[z+z2]
                z2 += 1
            if (SixtyDayCalc/60) > close_prices[z]:
                sixty_Day_Obs.append(1)
            else:
                sixty_Day_Obs.append(0)
        else:
            sixty_Day_Obs.append(0)
        z+=1
    data['Five_Day_Observation_Outcome'] = Five_Day_Obs
    data['Thirty_Day_Observation_Outcome'] = thirty_Day_Obs
    data['Sixty_Day_Observation_Outcome'] = sixty_Day_Obs
    data.to_csv("<Your Path>\\Bayesian_Logistic_Regression\\Stocks_Sub\\"+Stock_Name+".csv")
    print("Data for " + Stock_Name + " has been substantiated with technical features.")
#view rawATLR_TI.py hosted with ❤ by GitHub


Hold_Results = []
list_files2 = (glob.glob("<Your Path>\\Bayesian_Logistic_Regression\\Stocks_Sub\\*.csv")) # Creates a list of all csv filenames in the stocks folder
for interval2 in list_files2:
    Stock_Name = ((os.path.basename(interval2)).split(".csv")[0])
    data = pd.read_csv(interval2,index_col=0)
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.fillna(0)
    dependents = [data["Five_Day_Observation_Outcome"].to_list(), data["Thirty_Day_Observation_Outcome"].to_list(), data["Sixty_Day_Observation_Outcome"].to_list()]
    data = data.drop(['Five_Day_Observation_Outcome', 'Thirty_Day_Observation_Outcome', 'Sixty_Day_Observation_Outcome', 'Date', 'Open', 'High', 'Low', 'Close'], axis = 1)
    scaler = StandardScaler()
    data = scaler.fit_transform(data)  # Standardize our data set
    Hold_Results_Section = []
    p = 0
    for dep in dependents:
        x_train, x_test, y_train, y_test =\
        train_test_split(data, dep, test_size=0.2, random_state=0)
        model = LogisticRegression(solver='liblinear', C=0.05, multi_class='ovr',random_state=0)
        model.fit(x_train, y_train)
        y_pred = model.predict(x_test)  # To get the predicted values
        conf = confusion_matrix(y_test, y_pred)
        if p == 0:
            Hold_Results.append([Stock_Name, "Five_Day_Observation_Outcome", model.score(x_train, y_train),model.score(x_test, y_test),conf[0,0],conf[0,1],conf[1,0],conf[1,1]])
        if p == 1:
            Hold_Results.append([Stock_Name, "Thirty_Day_Observation_Outcome", model.score(x_train, y_train),model.score(x_test, y_test),conf[0,0],conf[0,1],conf[1,0],conf[1,1]])
        if p == 2:
            Hold_Results.append([Stock_Name, "Sixty_Day_Observation_Outcome", model.score(x_train, y_train),model.score(x_test, y_test),conf[0,0],conf[0,1],conf[1,0],conf[1,1]])
        p+=1
    print("Model complete for " + Stock_Name)
df = pd.DataFrame(Hold_Results, columns=['Stock', 'Observation Period', 'Model Accuracy on Training Data', 'Model Accuracy on Test Data', 'True Positives','False Positives',
'False Negative','True Negative'])
df.to_csv("<Your Path>\\Bayesian_Logistic_Regression\\Model_Outcome.csv", index = False)
#view rawATLR_Model.py hosted with ❤ by GitHub
