import requests
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

# Binance API credentials
api_key = '69x3Jp04I1k9hbddyDocyjQVm5FKU86TrRMjhLH7opWvGvXF314oGfmodxSsHtWV'
api_secret = 'n8KBEJVD6btZZLxSeru8PsLJ3M57POaOH9jzgxPALXWKTL5aApWj833ZLSqct0Gk'

# Telegram bot token
bot_token = '6372215166:AAGD6B8i_kuKkV996zX7ifAYwdO8e25yvlA'

# Initialize Binance client
client = Client(api_key, api_secret)

# Function to calculate Exponential Moving Average
def calculate_ema(data, period=50):
    if len(data) < period:
        return None
    multiplier = 2 / (period + 1)
    ema_data = [float(data[0][4])]
    for i in range(1, len(data)):
        ema_data.append((float(data[i][4]) - ema_data[i-1]) * multiplier + ema_data[i-1])
    return ema_data[-1]

# Function to calculate RSI
def calculate_rsi(data, period=14):
    gains = []
    losses = []
    for i in range(1, len(data)):
        diff = float(data[i][4]) - float(data[i - 1][4])
        if diff > 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period if sum(losses) != 0 else 1

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Function to calculate volume moving average
def calculate_volume_ma(data, period=20):
    volumes = [float(candle[5]) for candle in data]
    if len(volumes) < period:
        return None
    volume_ma = sum(volumes[-period:]) / period
    return volume_ma

# Define the entry rules
def is_bullish_trade(symbol):
    try:
        # Fetch 50 and 200 SMA
        kline_data = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, "200 days ago UTC")
        
        if len(kline_data) < 200:
            return False  # Not enough data

        ma_50 = calculate_ema(kline_data, 50)
        ma_200 = calculate_ema(kline_data, 200)

        # Check for Golden Cross
        if ma_50 > ma_200:
            # Fetch RSI data
            rsi_data = kline_data[-15:]
            current_rsi = calculate_rsi(rsi_data, 14)
            previous_rsi = calculate_rsi(rsi_data[:-1], 14)
            if not (30 <= current_rsi <= 70 and current_rsi > previous_rsi):
                return False

            # Calculate volume and volume moving average
            volume_ma = calculate_volume_ma(kline_data, 50)
            current_volume = float(kline_data[-1][5])
            if current_volume > volume_ma:
                return True

    except BinanceAPIException as e:
        print(f"Binance API Exception: {e}")
    except BinanceRequestException as e:
        print(f"Binance Request Exception: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return False

def is_bearish_trade(symbol):
    try:
        # Fetch 50 and 200 SMA
        kline_data = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, "200 days ago UTC")
        
        if len(kline_data) < 200:
            return False  # Not enough data

        ma_50 = calculate_ema(kline_data, 50)
        ma_200 = calculate_ema(kline_data, 200)

        # Check for Death Cross
        if ma_50 < ma_200:
            # Fetch RSI data
            rsi_data = kline_data[-15:]
            current_rsi = calculate_rsi(rsi_data, 14)
            previous_rsi = calculate_rsi(rsi_data[:-1], 14)
            if not (30 <= current_rsi <= 70 and current_rsi < previous_rsi):
                return False

            # Calculate volume and volume moving average
            volume_ma = calculate_volume_ma(kline_data, 50)
            current_volume = float(kline_data[-1][5])
            if current_volume > volume_ma:
                return True

    except BinanceAPIException as e:
        print(f"Binance API Exception: {e}")
    except BinanceRequestException as e:
        print(f"Binance Request Exception: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return False

# Send Telegram alert
def send_telegram_alert(message):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    params = {'chat_id': '1122627805', 'text': message}  # Replace 'your_chat_id' with your chat ID
    requests.post(url, data=params)

# Main function
def main():
    while True:  # Infinite loop
        try:
            exchange_info = client.get_exchange_info()
            symbols = [symbol_info['symbol'] for symbol_info in exchange_info['symbols']]

            for symbol in symbols:
                if symbol.endswith('USDT'):  # Filter only USDT pairs
                    if is_bullish_trade(symbol):
                        ma_50 = calculate_ema(client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, "50 days ago UTC"), 50)
                        ma_200 = calculate_ema(client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, "200 days ago UTC"), 200)
                        current_rsi = calculate_rsi(client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, "14 days ago UTC"), 14)
                        message = f"Bullish trade signal detected for {symbol}\n"
                        message += f"Price in MA 50: {ma_50}\n"
                        message += f"Price in MA 200: {ma_200}\n"
                        message += f"RSI: {current_rsi}\n"
                        send_telegram_alert(message)

                    elif is_bearish_trade(symbol):
                        ma_50 = calculate_ema(client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, "50 days ago UTC"), 50)
                        ma_200 = calculate_ema(client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, "200 days ago UTC"), 200)
                        current_rsi = calculate_rsi(client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, "14 days ago UTC"), 14)
                        message = f"Bearish trade signal detected for {symbol}\n"
                        message += f"Price in MA 50: {ma_50}\n"
                        message += f"Price in MA 200: {ma_200}\n"
                        message += f"RSI: {current_rsi}\n"
                        send_telegram_alert(message)

        except BinanceAPIException as e:
            print(f"Binance API Exception: {e}")
        except BinanceRequestException as e:
            print(f"Binance Request Exception: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            
        time.sleep(14400)  # Pause for 4 hours

if __name__ == "__main__":
    main()
