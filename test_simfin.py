'''
# api_key = 'xYrW6xuY7L4uDQSqVDKoHoXjYho6D2WV'

# Import the simfin package and the Python shortcuts for the columns
import simfin as sf
from simfin.names import *

# Import matplotlib and seaborn for plotting charts
import matplotlib.pyplot as plt
import seaborn as sns
# Seaborn set plotting style.
sns.set_style("whitegrid")

# Set your API-key for downloading data.
sf.set_api_key('free')
# sf.set_api_key('xYrW6xuY7L4uDQSqVDKoHoXjYho6D2WV')

# Set the local directory where data-files are stored.
# The dir will be created if it does not already exist.
# sf.set_data_dir('~/simfin_data/')
# sf.set_data_dir('~/OneDrive/Stock/simfin_data')
sf.set_data_dir('C:/Users/3203142/OneDrive/Stock/simfin_data')

# Load the full list of companies in the selected market (United States).
# df_companies = sf.load_companies(market='us')

# Load all the industries that are available.
# df_industries = sf.load_industries()

# Load the quarterly Income Statements for all companies in the selected market.
#df_income = sf.load_income(variant='quarterly', market='us')
#df_income = sf.load_income(variant='annual', market='us')
df_income = sf.load_income(variant='ttm', market='us')

# Load the quarterly Balance Sheet data for all companies in the selected market.
# df_balance = sf.load_balance(variant='quarterly', market='us')

# Load the quarterly Balance Sheet data for all companies in the selected market.
# df_cashflow = sf.load_cashflow(variant='quarterly', market='us')

# Plot revenue and net income for Microsoft.
#df_income.loc['MSFT', [REVENUE, NET_INCOME]].plot(grid=True)
#plt.show()

#df_income.info()
#print(df_income.loc['MSFT'])
print(df_income.loc['MSFT'].loc['2010-06-30']['Shares (Diluted)'])


# Calculate net profit margin for entire dataset.
# df_net_profit_margin = df_income[NET_INCOME] / df_income[REVENUE]
# Rename the series to be able to plot it.
# df_net_profit_margin.rename("Net Profit Margin", inplace=True)
# plot net profit margin for Apple, Amazon and Microsoft
# tickers = ['AAPL', 'AMZN', 'MSFT']
# sns.lineplot(x="Report Date", y="Net Profit Margin", hue=TICKER, data=df_net_profit_margin.loc[tickers].reset_index())
# plt.show()

# Calculate EBITDA for entire dataset.
# df_ebitda = df_income[OPERATING_INCOME].fillna(0) + df_cashflow[DEPR_AMOR].fillna(0)
# df_ebitda.loc['MSFT'].plot(grid=True)
# plt.show()

# PRICE/SALES RATIO
# Load the daily share price data for all companies in the selected market.
# df_prices = sf.load_shareprices(variant='daily', market='us')

# Calculate all sales per share figures.
# df_sales_per_share = df_income[REVENUE] / df_income[SHARES_BASIC]

# Reindex to map fundamentals to the days contained in the share prices dataset.
# df_sales_per_share_daily = sf.reindex(df_src=df_sales_per_share, df_target=df_prices, method='ffill')

# Calculate prices sales ratio.
# df_price_sales = df_prices[CLOSE] / df_sales_per_share_daily

# plot for Microsoft.
# df_price_sales.loc['MSFT'].plot(grid=True)
# plt.show()
'''
import simfin as sf

# Set your API-key for downloading data. This key gets the free data.
sf.set_api_key('free')

# Set the local directory where data-files are stored.
# The directory will be created if it does not already exist.
#sf.set_data_dir('~/simfin_data/')
sf.set_data_dir('C:/Users/3203142/OneDrive/Stock/simfin_data')

# Download the data from the SimFin server and load into a Pandas DataFrame.
df = sf.load_derived(variant='annual', market='us')

# Print the first rows of the data.
print(df.head())