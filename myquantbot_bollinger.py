import pyupbit
import numpy as np
import datetime
import time

import os
from dotenv import load_dotenv

load_dotenv()

# API 키 설정
upbit = pyupbit.Upbit(os.getenv("UPBIT_ACCESS_KEY"), os.getenv("UPBIT_SECRET_KEY"))

# 파라미터 설정
check_interval = 60  # 1분 간격
profit_target = 0.002  # 0.2% 수익률 목표
ticker = "KRW-BTC"  # 비트코인


def get_bollinger_bands(ticker, interval="minute1", k=2, count=200):
    """볼린저 밴드 계산"""
    df = pyupbit.get_ohlcv(ticker, interval=interval, count=count)
    df["MA20"] = df["close"].rolling(window=20).mean()
    df["stddev"] = df["close"].rolling(window=20).std()
    df["upper"] = df["MA20"] + (k * df["stddev"])
    df["lower"] = df["MA20"] - (k * df["stddev"])

    return df.iloc[-1]


def buy_crypto_currency(ticker):
    print(f"매수: {ticker}" f"현재가: {pyupbit.get_current_price(ticker)}")
    """매수 실행 함수"""
    krw_balance = upbit.get_balance("KRW")
    if krw_balance > 5000:
        order = upbit.buy_market_order(ticker, krw_balance * 0.9995)
        order_uuid = upbit.get_order(order["uuid"])
        print(f"주문 UUID: {order_uuid}")
    return None


def sell_crypto_currency(ticker):
    print(f"매도: {ticker}" f"현재가: {pyupbit.get_current_price(ticker)}")
    """매도 실행 함수"""
    btc_balance = upbit.get_balance(ticker)
    if btc_balance > 0.00008:
        upbit.sell_market_order(ticker, btc_balance)


def check_sell_conditions(ticker, bought_price):
    """매도 조건 확인"""
    print(f"현재가: {pyupbit.get_current_price(ticker)}, 매수가: {bought_price}")
    current_price = pyupbit.get_current_price(ticker)
    return current_price >= bought_price * (1 + profit_target)


def run_bot():
    bought = False
    bought_price = 0
    done_for_the_day = False
    last_checked_sell = datetime.datetime.now()
    order_uuid = None

    while True:
        now = datetime.datetime.now()
        if now.hour == 0:
            done_for_the_day = False
            if not bought:  # 매수 상태가 아니면 리셋
                bought_price = 0
            last_checked_sell = now

        if not done_for_the_day:
            if not bought:
                band = get_bollinger_bands(ticker)
                current_price = pyupbit.get_current_price(ticker)
                print(f"Current time: {now}")
                print(
                    f"Current price: {current_price}, Lower band: {band['lower']}, Upper band: {band['upper']}"
                )
                if current_price < band["lower"]:
                    buy_crypto_currency(ticker)
                    bought = True
                    last_checked_sell = now
                    bought_price = pyupbit.get_current_price(ticker)

            # 매도 체크: 10분 간격
            if bought and (now - last_checked_sell).seconds >= 600:
                last_checked_sell = now

                # 체결 정보를 가져오기 위해 주문 ID 사용
                if order_uuid is not None:
                    # 주문 상태 확인
                    order_details = upbit.get_order(order_uuid)
                    if (
                        order_details and order_details["state"] == "done"
                    ):  # 주문이 완료되었는지 확인
                        # 평균 체결 가격
                        bought_price = float(order_details["price"])
                        print(f"Avg Bought price: {bought_price}")

                if check_sell_conditions(ticker, bought_price):
                    sell_crypto_currency(ticker)
                    bought = False  # 매도 성공시 매수 상태 리셋
                    done_for_the_day = True  # 거래 완료

        time.sleep(60)  # 조건을 확인하는 주기는 필요에 따라 조절


# 실행
run_bot()
