import numpy as np
import time
from datetime import datetime
from binance.client import Client
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Initialize Client with your API keys
api_key = "<your_api_key>"
api_secret = "<your_private_api_key>"
client = Client(api_key, api_secret)

# Traded symbol
symbol = "ETHUSDT"

# List to keep all closing prices
prices = []

# Lists to keep all stats needed
moving_average_values = []
bollinger_band_high_values = []
bollinger_band_low_values = []

# Flags to track the exchanges to avoid duplicated entries
in_short = False
in_long = False

# Period of Bollinger Bands
period = 3

# Last time check (to avoid duplicated entries)
last_time = ""

# Helper functions for trade operations:
def short_open(symbol, quantity):
    client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=quantity)
    logging.info(f"Short position opened for {symbol}, quantity: {quantity}")

def short_close(symbol, quantity):
    client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=quantity)
    logging.info(f"Short position closed for {symbol}, quantity: {quantity}")

def long_open(symbol, quantity):
    client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=quantity)
    logging.info(f"Long position opened for {symbol}, quantity: {quantity}")

def long_close(symbol, quantity):
    client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=quantity)
    logging.info(f"Long position closed for {symbol}, quantity: {quantity}")

# Main loop
while True:
    current_time = datetime.now()

    # Check if it's time for a new candlestick (5-minute interval)
    if current_time.minute % 5 == 0 and current_time.strftime('%Y-%m-%d %H:%M') != last_time:
        last_time = current_time.strftime('%Y-%m-%d %H:%M')
        
        try:
            # Get the latest price for the symbol
            latest_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
            prices.append(latest_price)
            
            # Print latest price with current time
            logging.info(f"Latest price at {current_time}: {latest_price}")

            # Calculate moving average and standard deviation
            ma = np.mean(prices[-period:])
            moving_average_values.append(ma)

            std = np.std(prices[-period:], ddof=1)

            # Calculate Bollinger Bands
            bb_high = ma + 2 * std
            bb_low = ma - 2 * std

            bollinger_band_high_values.append(bb_high)
            bollinger_band_low_values.append(bb_low)

            # Decision-making for strategy
            # Short trades
            if len(prices) >= 2:
                if prices[-2] < bollinger_band_high_values[-2] and prices[-1] > bollinger_band_high_values[-1]:
                    if not in_short:
                        short_open(symbol=symbol, quantity=1)
                        in_short = True

                if prices[-2] > moving_average_values[-2] and prices[-1] < moving_average_values[-1]:
                    if in_short:
                        short_close(symbol=symbol, quantity=1)
                        in_short = False

                # Long trades
                if prices[-1] < bollinger_band_low_values[-1] and prices[-2] > bollinger_band_low_values[-2]:
                    if not in_long:
                        long_open(symbol=symbol, quantity=1)
                        in_long = True

                if prices[-2] < moving_average_values[-2] and prices[-1] > moving_average_values[-1]:
                    if in_long:
                        long_close(symbol=symbol, quantity=1)
                        in_long = False
        except Exception as e:
            logging.error(f"Error while processing: {e}")

    # Adjust sleep time to avoid unnecessary CPU usage
    time.sleep(60)  # Sleep for a minute (adjust this as needed)
