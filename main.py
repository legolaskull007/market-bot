
import yfinance as yf
import ta
import smtplib
from email.mime.text import MIMEText
import time
import os

# Email notification setup (Railway will provide env variables)
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

def send_email_notification(subject, message):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print('Notification sent!')
    except Exception as e:
        print('Failed to send notification:', e)

def get_indicators(df):
    df['SMA_5'] = df['Close'].rolling(window=5).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    macd_indicator = ta.trend.MACD(df['Close'])
    df['MACD'] = macd_indicator.macd()
    df['MACD_signal'] = macd_indicator.macd_signal()
    return df

def check_signals(df):
    last = df.index[-1]
    prev = df.index[-2]

    if (
        df['SMA_5'][last] > df['SMA_20'][last] and 
        df['SMA_5'][prev] <= df['SMA_20'][prev] and 
        df['RSI'][last] < 35 and
        df['MACD'][last] > df['MACD_signal'][last] and
        df['MACD'][prev] <= df['MACD_signal'][prev]
    ):
        return 'BUY'

    elif (
        df['SMA_5'][last] < df['SMA_20'][last] and
        df['SMA_5'][prev] >= df['SMA_20'][prev] and
        df['RSI'][last] > 65 and
        df['MACD'][last] < df['MACD_signal'][last] and
        df['MACD'][prev] >= df['MACD_signal'][prev]
    ):
        return 'SELL'

    return None

TICKER = 'RELIANCE.NS'
last_signal = ''

while True:
    data = yf.download(TICKER, period='2d', interval='5m')
    data = get_indicators(data.dropna())
    signal = check_signals(data)
    price = data['Close'][-1]

    if signal and signal != last_signal:
        subject = f'Reliance Trade Alert: {signal}'
        message = f'Trade Signal: {signal}\nCurrent Price: {price}\nTime: {data.index[-1]}'
        send_email_notification(subject, message)
        last_signal = signal
    else:
        print(f'No signal at {data.index[-1]} | Price: {price:.2f}')

    time.sleep(300)
