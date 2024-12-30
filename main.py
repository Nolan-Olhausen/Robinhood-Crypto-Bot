# ==============================================================================
# Project: Crypto Trading Bot
# Author: Nolan Olhausen
# ==============================================================================

import robin_stocks as rh
import pyotp
import argparse
import time
import pandas as pd
import pandas_ta
from ta.momentum import RSIIndicator
import math

# Candle config
candleLength = 14
smoothing = 1

# RSI plot config
rsiLength = 14

# Channel overbought/oversold config
upperOB = 70
lowerOS = 30
extraCheck = 45

# Get Data at current
def getData(symbol):

    # Create data from historicals filtering for each necessary
    data = {
        'open': getHistoricals(symbol, interval="5minute", span="day", bounds="24_7", info="open_price"),
        'high': getHistoricals(symbol, interval="5minute", span="day", bounds="24_7", info="high_price"),
        'low': getHistoricals(symbol, interval="5minute", span="day", bounds="24_7", info="low_price"),
        'close': getHistoricals(symbol, interval="5minute", span="day", bounds="24_7", info="close_price")
    }
    dataframe = pd.DataFrame(data)
    return dataframe

# Calculate RSI
def calculateRSI(dataFrame, column):

    # Calculate price differences
    delta = dataFrame[column].diff(1)

    # Calculate gains and losses
    gain = delta.clip(lower=0).round(2)
    loss = delta.clip(upper=0).abs().round(2)
    
    # Calculate exponential weighted moving averages of gains and losses
    avgGain = gain.rolling(window=rsiLength, min_periods=rsiLength).mean()
    avgLoss = loss.rolling(window=rsiLength, min_periods=rsiLength).mean()

    # Calculate Average Gains
    for i, row in enumerate(avgGain.iloc[rsiLength+1:]):
        avgGain.iloc[i + rsiLength + 1] =\
            (avgGain.iloc[i + rsiLength] *
             (rsiLength - 1) +
             gain.iloc[i + rsiLength + 1])\
            / rsiLength

    # Calculate Average Losses
    for i, row in enumerate(avgLoss.iloc[rsiLength+1:]):
        avgLoss.iloc[i + rsiLength + 1] =\
            (avgLoss.iloc[i + rsiLength] *
             (rsiLength - 1) +
             loss.iloc[i + rsiLength + 1])\
            / rsiLength
    
    # Calculate the RS (Relative Strength)
    rs = avgGain / avgLoss

    # Calculate the RSI (Relative Strength Index)
    rsi = 100 - (100 / (1 + rs))

    return rsi

# Heikin Ashi Candle Function with smoothing
def heikinAshi(dataFrame):

    # Get rsi series of OHLC
    openRSIRaw = calculateRSI(dataFrame, 'open')
    highRSIRaw = calculateRSI(dataFrame, 'high')
    lowRSIRaw = calculateRSI(dataFrame, 'low')
    closeRSIRaw = calculateRSI(dataFrame, 'close')

    # OpenRSI can be set to prev close
    openRSI = closeRSIRaw.iloc[-2]

    # Set closeRSI to avoid repeat calculations
    closeRSI = closeRSIRaw.iloc[-1]

    # Unlike normal high/low, the RSI versions can overlap
    highRSI = max(highRSIRaw.iloc[-1], lowRSIRaw.iloc[-1])
    lowRSI = min(highRSIRaw.iloc[-1], lowRSIRaw.iloc[-1])

    # Calculate Heikin Ashi values (formula at https://www.investopedia.com/trading/heikin-ashi-better-candlestick/)
    close = (openRSI + highRSI + lowRSI + closeRSI) / 4

    # Open calculation
    # Smoothing can smooth/lag candles open, helps trend (smoothing must be at least 1)
    if(math.isnan(openRSIRaw.iloc[smoothing])):
        open = (openRSIRaw.iloc[-2] + closeRSIRaw.iloc[-2]) / 2
    else:
        open = ((openRSIRaw.iloc[-2] * smoothing) + closeRSIRaw.iloc[-2]) / (smoothing + 1)

    high = max(highRSI, max(open, close))
    low = min(lowRSI, min(open, close))

    # Create candle
    ohlc4 = {
        'open': open,
        'high': high,
        'low': low,
        'close': close
    }

    return ohlc4


# Get the mark price, ask price, and bid price of the crypto
def getPrice(symbol):
    try:

        # Get current price stats
        markPrice = rh.robinhood.crypto.get_crypto_quote(symbol, info="mark_price")
        askPrice = rh.robinhood.crypto.get_crypto_quote(symbol, info="ask_price")
        bidPrice = rh.robinhood.crypto.get_crypto_quote(symbol, info="bid_price")
        return float(markPrice), float(askPrice), float(bidPrice)
    except Exception as e:
        print(f"Error fetching prices for {symbol}: {e}")
        return None, None, None

# Execute a market buy of the crypto for the dollar amount
def cryptoMarketBuy(symbol, dollarAmount):
    try:
        # Send order
        order = rh.robinhood.orders.order_buy_crypto_by_price(symbol, float(dollarAmount))
        return order
    except Exception as e:
        print(f"Error executing market buy for {symbol}: {e}")
        return None
    
# Execute a market sell of the crypto for the dollar amount
def cryptoMarketSell(symbol, quantity):
    try:
        # Send order
        order = rh.robinhood.orders.order_sell_crypto_by_quantity(symbol, float(quantity))
        return order
    except Exception as e:
        print(f"Error executing market sell for {symbol}: {e}")
        return None
    
# Get historicals of crypto
def getHistoricals(symbol, interval='5minute', span='day', bounds='24_7', info=None):
    try:
        # Get historicals of crypto
        historicals = rh.robinhood.crypto.get_crypto_historicals(
            symbol, interval=interval, span=span, bounds=bounds, info=info
        )
        floatHistoricals = [float(item) for item in historicals]
        return floatHistoricals
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {e}")
        return None

# Strategy Method, Condition 1: candle low crosses below lowerOS, Condition 2: reversal to green candle
def scalpingStrategy(symbol, cash):
        
    # Create updated data
    data = getData(symbol)

    # Create most recent candle
    candle = heikinAshi(data)

    # Check 1st condition
    if candle['low'] < lowerOS:
        print("Passed Condition 1: Candle low crosses below 30 RSI")
        condition2 = False
        lowest = data['low'][-1] # for last swing low

        # Loop until condition 2 is met and rsi still below extraCheck
        while not condition2:
            print("Waiting on condition 2")
            time.sleep(300)

            # Get new info
            newData = getData(symbol)
            newCandle = heikinAshi(newData)

            # Check conditions
            if(newCandle['close'] > newCandle['open']):
                if(newCandle['close'] < extraCheck):
                    condition2 = True
                else:
                    print("Candle was green, but RSI > 45, resetting")
                    break
            else:
                print("Not green candle, monitoring")

                # Update swing low if necessary
                if(newData['low'][-1] < lowest):
                    lowest = newData['low'][0] 

        # Condition 2
        if(condition2):

            # Get/calculate necessaries
            markPrice, askPrice, bidPrice = getPrice(symbol)
            buySpread = 1 - askPrice/((bidPrice + askPrice) / 2)
            profitPercent = 0.25
            triggerPercent = max((1 - lowest/markPrice), ((profitPercent + (buySpread * 2)) / 100))
            
            # Send order
            try:
                buyOrder = cryptoMarketBuy(symbol, cash)
                time.sleep(15)
                buyOrder = cryptoMarketBuy(symbol, cash) # Attempt again in case fail, robinhood often rejects order
                # This only works since I am using all my account balance on each trade, if first succeeds, second
                # will fail due to insufficient funds, if using smaller amounts than balance, could send 2 orders
            except Exception as e:
                print(f"Buy order failed: {e}")
                exit(1)

            # Calculate stop-loss and take-profit
            takeProfit = markPrice * (1 + triggerPercent)
            stopLoss = markPrice * (1 - triggerPercent)

            if buyOrder:
                print(f"Buy order executed at {markPrice} for {symbol}")
                print(f"    Stop-Loss: {stopLoss}")
                print(f"    Take-Profit: {takeProfit}")

                # Loop to check for sell signal
                while True:

                    # Check price every 30 sec
                    time.sleep(30)
                    newPrice = getPrice(symbol)[0]
                    if(newPrice >= takeProfit): # Hit take-profit

                        # Get quantity of crypto
                        quantity = rh.robinhood.crypto.get_crypto_positions(info='quantity')[0]
                        
                        # Sell Profit
                        try:
                            sellOrder = cryptoMarketSell(symbol, quantity)
                            time.sleep(15)
                            sellOrder = cryptoMarketSell(symbol, quantity)
                            # This only works since I am using all crypto balance on each trade, if first succeeds, second
                            # will fail due to insufficient coin, if using smaller amounts than balance, could send 2 orders
                        except Exception as e:
                            print(f"Sell order failed: {e}")
                            exit(1)
                        if sellOrder:
                            print(f"Sell order executed at {newPrice} for {symbol}")
                            print(f"    Profit: {newPrice - markPrice}")
                            break
                    elif(newPrice <= stopLoss): # Hit stop-loss

                        # Get quantity of crypto
                        quantity = rh.robinhood.crypto.get_crypto_positions(info='quantity')[0]
                        
                        # Sell Loss
                        try:
                            sellOrder = cryptoMarketSell(symbol, quantity)
                        except Exception as e:
                            print(f"Sell order failed: {e}")
                            exit(1)
                        if sellOrder:
                            print(f"Sell order executed at {newPrice} for {symbol} due to stop loss")
                            print(f"    Loss: {markPrice - newPrice}")
                            break
                    else:
                        print(f"    Current Price: {newPrice}")
        else:
            print("Failed Condition 2 with reset") 
    else:
        print("Failed Condition 1: RSI not below 30, was " + str(candle['low']))




# Main
if __name__ == "__main__":
    # Parse text document with login info
    lines = open(r"C:\Users\beefm\OneDrive\Documents\cred-robin.txt").read().splitlines()
    KEY = lines[0]
    EMAIL = lines[1]
    PASS = lines[2]
    totp = pyotp.TOTP(KEY).now()

    # Login to robinhood
    try:
        login = rh.robinhood.authentication.login(EMAIL, PASS, mfa_code=totp)
    except Exception as e:
        print(f"Login failed: {e}")
        exit(1)

    # Parse argument for crypto symbol
    parser = argparse.ArgumentParser(description="Get price information for a stock ticker or cryptocurrency symbol.")
    parser.add_argument("-s", "--symbol", help="Cryptocurrency symbol")
    args = parser.parse_args()
    symbol = args.symbol

    data = getData(symbol)
    candle = heikinAshi(data)

    # Run bot
    while True:

        # Get available cash in account, but subtract a dollar
        cash = str(float(rh.robinhood.account.build_user_profile()['cash']) - 1)

        # YOLO cash, could set specified amount, or divide total cash like cash/10 for 10%
        scalpingStrategy(symbol, cash)
        
        # Repeat every 5 minutes for each candle
        time.sleep(300)

    