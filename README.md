# Robinhood-Crypto-Bot

A Python-based crypto trading bot designed to analyze market data, identify trading opportunities, and execute trades based on technical indicators. This bot utilizes **Heikin Ashi candles** and the **Relative Strength Index (RSI)** to determine optimal buy and sell signals.

---

## **Features**

- **Historical Data Collection**: 
  - Gathers historical price data for the selected cryptocurrency using third-party API.
  - Prepares data for technical analysis.

- **Heikin Ashi Candlestick Analysis**: 
  - Smooths out market noise and highlights trends.
  - Detects trend reversals and continuation patterns.

- **RSI (Relative Strength Index)**:
  - Measures the speed and change of price movements to identify overbought or oversold conditions.
  - Customizable parameters.

- **Trade Execution**:
  - Monitors for two conditions to enter a trade:
    1. **Condition 1**: The candle's low crosses below the lower oversold RSI channel.
    2. **Condition 2**: A reversal is confirmed with the formation of a green Heikin Ashi candle.
  - Automatically places buy or sell orders upon meeting both conditions.

---

## **Technical Indicators Used**

1. **Heikin Ashi Candles**:
   - A modified candlestick charting method to reduce noise in price action.
   - Helps to easily spot trends and reversals.

2. **RSI (Relative Strength Index)**:
   - Threshold levels (e.g., 30 for oversold and 70 for overbought) to gauge market conditions.
   - Works in tandem with Heikin Ashi for confirmation of trade setups.

---

## **Trade Conditions**

### **Condition 1: RSI Oversold Crossover**
- When the Heikin Ashi candle's low crosses below the lower RSI oversold channel, the bot identifies a potential trade setup.
- This serves as the initial signal of a trend reversal.

### **Condition 2: Reversal Confirmation**
- The bot waits for the formation of a **green Heikin Ashi candle** to confirm a trend reversal.
- Ensures that the signal is valid before executing a trade.

---

## **How It Works**

1. **Setup and Initialization**:
   - Configure the bot with your robinhood credentials.
   - Specify the cryptocurrency to monitor and trade (e.g., BTC).

2. **Data Collection and Analysis**:
   - The bot fetches historical price data and calculates Heikin Ashi candles and RSI values.

3. **Trade Monitoring**:
   - Continuously monitors live market data to detect the predefined trade conditions.

4. **Trade Execution**:
   - Executes a buy or sell order once both trade conditions are satisfied.

---
