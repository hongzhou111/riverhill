'''
https://towardsdatascience.com/algorithmic-trading-with-macd-and-python-fef3d013e9f3

https://towardsdatascience.com/algorithmic-trading-with-rsi-using-python-f9823e550fe0
by Victor Sim
'''
import yfinance
import talib
from matplotlib import pyplot as plt

data = yfinance.download('FB','2016-1-1','2020-1-1')
data["macd"], data["macd_signal"], data["macd_hist"] = talib.MACD(data['Close'])
print(data)
fig = plt.figure()
plt.plot(data.index, data['macd'], color='b', label='MACD')
plt.plot(data.index, data['macd_signal'], color='purple', label='MACDS')
plt.bar(data.index, data['macd_hist'], color='r', width=4.0)

'''
def intersection(lst_1,lst_2):
    intersections = []
    insights = []
    if len(lst_1) > len(lst_2):
        settle = len(lst_2)
    else:
        settle = len(lst_1)
    for i in range(settle-1):
        if (lst_1[i+1] < lst_2[i+1]) != (lst_1[i] < lst_2[i]):
            if ((lst_1[i+1] < lst_2[i+1]),(lst_1[i] < lst_2[i])) == (True,False):
                insights.append('buy')
            else:
                insights.append('sell')
            intersections.append(i)
    return intersections,insights
intersections,insights = intersection(data["macd_signal"],data["macd"])

def intersection(lst_1,lst_2):
    intersections = []
    insights = []
    if len(lst_1) > len(lst_2):
        settle = len(lst_2)
    else:
        settle = len(lst_1)
    for i in range(settle-1):
        if (lst_1[i+1] < lst_2[i+1]) != (lst_1[i] < lst_2[i]):
            if ((lst_1[i+1] < lst_2[i+1]),(lst_1[i] < lst_2[i])) == (True,False):
                insights.append('buy')
            else:
                insights.append('sell')
            intersections.append(i)
    return intersections,insights
intersections,insights = intersection(data["macd_signal"],data["macd"])

profit = 0
pat = 1
for i in range(len(intersections)-pat):
    index = intersections[i]
    true_trade= None
    if data['Close'][index] < data['Close'][index+pat]:
        true_trade = 'buy'
    elif data['Close'][index] > data['Close'][index+pat]:
        true_trade = 'sell'
    if true_trade != None:
        if insights[i] == true_trade:
            profit += abs(data['Close'][index]-data['Close'][index+1])
        if insights[i] != true_trade:
            profit += -abs(data['Close'][index]-data['Close'][index+1])
'''
rsi = talib.RSI(data["Close"])
fig = plt.figure()
#fig.set_size_inches((25, 18))
ax_rsi = fig.add_axes((0, 0.24, 1, 0.2))
ax_rsi.plot(data.index, [70] * len(data.index), label="overbought")
ax_rsi.plot(data.index, [30] * len(data.index), label="oversold")
ax_rsi.plot(data.index, rsi, label="rsi")
ax_rsi.plot(data["Close"])
ax_rsi.legend()

section = None
sections = []
for i in range(len(rsi)):
    if rsi[i] < 30:
        section = 'oversold'
    elif rsi[i] > 70:
        section = 'overbought'
    else:
        section = None
    sections.append(section)

section = None
sections = []
for i in range(len(rsi)):
    if rsi[i] < 30:
        section = 'oversold'
    elif rsi[i] > 70:
        section = 'overbought'
    else:
        section = None
    sections.append(section)

trades = []
for i in range(1,len(sections)):
    trade = None
    if sections[i-1] == 'oversold' and sections[i] == None:
        trade = True
    if sections[i-1] == 'overbought' and sections[i] == None:
        trade = False
    trades.append(trade)

acp = data['Close'][len(data['Close'])-len(trades):].values
profit = 0
qty = 10
for i in range(len(acp)-1):
    true_trade = None
    if acp[i] < acp[i+1]:
        true_trade = True
    elif acp[i] > acp[i+1]:
        true_trade = False
    if trades[i] == true_trade:
        profit += abs(acp[i+1] - acp[i]) * qty
    elif trades[i] != true_trade:
        profit += -abs(acp[i+1] - acp[i]) * qty

print(profit)
plt.show()
