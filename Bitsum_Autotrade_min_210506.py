# Editing Date : 2021.05.06
import pybithumb
import requests
import pandas as pd
import datetime  # 거래 이력 데이터프레임에서 timestamp(시간)을 계산하기 위한 모듈 추가
import numpy as np
from slacker import Slacker  # slack 메신저 사용시
import time, calendar
import json

######## 계 좌 정 보 #############################
bithumb = pybithumb.Bithumb(api_key, secret_key)
##################################################

######## 변 수 모 음 ##############################
coin_list = ['BTC', 'XRP', 'ETH', 'BCH', 'EOS', 'TRX', 'LTC', 'ADA', 'LINK', 'XLM', 'BSV', 'MLK', 'ONT', 'STEEM']
# 4/30 선정(빗썸 선정 메이저 11+3개) : BTC(비트코인), XRP(리플), ETH(이더리움), BCH(비트코인 캐시), EOS(이오스), TRX(트론), LTC(라이트코인), ADA(에이다), LINK(체인링크), XLM(스텔라루멘), BSV(비트코인에스브이), MLK(밀크), ONT(온톨로지), STEEM(스팀)

# 기존의 dictionary에서 불러와서 coin_bought_price에 넣는 것.
# List 및 가격은 Bitsum_Autotrade_min_list.py에서 자동적으로 만들어 줌.
tf = open("Coin_buying_price_Bitsum.json", "r")
coin_bought_price = json.load(tf)
print(coin_bought_price)

# slack 사용용 정보
slack = Slacker('xoxb-1623925257904-1623926509472-inMKOT7HyyhQBqklvwCQyIjO')

# 주요 변수 (필요시 값 변경)
min_trade_money = 5000        # 최소 매도, 매수금액, 초기값 5000 (5000원)
profit_ratio = 0.15            # 매도 수익률 기준(이익률), 초기값 0.1 (10%)
loss_ratio = 0.05             # 매도 수익률 기준(손실률), 초기값 0.05 (-5%)
k = 0.3                       # 변동성 돌파 구간 설정값, 초기값 0.3 (일반적으로 0.3 ~ 0.7)
buying_balance_ratio = 0.15   # 매수시 잔고의 몇% 구매값, 초기값 0.15 (15%)
working_period_time = 60     # 주기적인 실행 시간, 초기값 300 (300초)

# Bitsum_analysis_class.py에서 불러올때 필요한 변수들, 아직 연동하지 않았음.
candle_period = '1h'  # 기본값 : 24h {1m, 3m, 5m, 10m, 30m, 1h, 6h, 12h, 24h 사용 가능}
date_range = 90  # call_data의 자료 기간을 선정함. 기본 30일이하며, 최대 2600일정도 받아옴.

###################################################

######## 함 수 정 의 ################################
def dbgout(message):
    """인자로 받은 문자열을 파이썬 셸과 슬랙으로 동시에 출력한다."""
    print(datetime.datetime.now().strftime('[%m/%d %H:%M:%S]'), message)
    send_message = datetime.datetime.now().strftime('[%m/%d %H:%M:%S] ') + message
    slack.chat.post_message('#stock', send_message)

def get_current_price(coin_name):
    """현재가 조회"""
    current_price = int(pybithumb.get_current_price(coin_name))
    return current_price

def get_balance(coin_name):
    """잔고 조회"""
    balance = bithumb.get_balance(coin_name)[2]  # 받은 값 = (보유코인량, 매도 주문 코인량, 원화보유량, 매수거래 원화량)
    return balance

def get_target_price(coin_name, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pybithumb.get_ohlcv(coin_name)
    df = df.tail(2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price


################## 메 인 프 로 그 램 ########################

dbgout('AutoTrade is Log in Now')

while True:
    try:
        for coin_name in coin_list :
            balance = bithumb.get_balance(coin_name)  # 받은 값 = (보유코인량, 매도 주문 코인량, 원화보유량, 매수거래 원화량)
            print(coin_name, ':', balance)
            current_price = int(pybithumb.get_current_price(coin_name))
            time.sleep(0.1)
            value = balance[0] * current_price
            if value > min_trade_money :  # 최소 거래 가능 금액 선정 (초기값 : 5000원)
                if (current_price/coin_bought_price[coin_name]) > (1 + profit_ratio) or (current_price/coin_bought_price[coin_name]) < (1 - loss_ratio) :
                    # 수익률 일정값 이상이거나, 이하이면 매도 실시 (초기 이익수익률 10%, 손해률 -5%)
                    print("%s : 매도" % coin_name)
                    sell_coins=balance[0]-balance[1]
                    split_point = str(round(sell_coins, 12)).split(".")
                    for i in range(len(split_point)):
                        if i == 0:  # 1보다 큰 정수 부분
                            sell_coins = float(split_point[i])
                        else:  # 1보다 작은 실수 부분
                            sell_coins = sell_coins + float("0" + "." + split_point[i][:4])
                    order_result = bithumb.sell_market_order(coin_name, sell_coins)
                    print("%s current_sell_price : %s" % (coin_name, current_price))
                    print("%s current_bought_price : %s" % (coin_name, coin_bought_price[coin_name]))
                    ratio = (current_price/coin_bought_price[coin_name]-1) * 100 #수익률
                    ratio = int(ratio)
                    sell_price = current_price * sell_coins
                    sell_price = int(sell_price)
                    print("%s : 수익율 %s %% 내고 팔았음." % (coin_name, ratio))
                    dbgout("Sell coin : " + coin_name + " profit ratio is " + str(ratio) + " %")
                    dbgout("Sell coin : " + coin_name + " Sell total price is " + str(sell_price) + " won")

                    coin_bought_price[coin_name] = current_price
                    # dictionary를 저장할때
                    tf = open("Coin_buying_price_Bitsum.json", "w")
                    json.dump(coin_bought_price, tf)
                    tf.close()

                else :
                    print("%s current_price : %s" % (coin_name, current_price))
                    print("%s current_bought_price : %s" % (coin_name, coin_bought_price[coin_name]))
                    print("%s : 팔지 않고 보유" % coin_name)
            else :
                target_price = get_target_price(coin_name, k)
                current_price = get_current_price(coin_name)
                print("%s current_price : %s" % (coin_name, current_price))
                print("%s balance : %s" % (coin_name, get_balance(coin_name)))
                if current_price > target_price :
                # and ma15 < current_price : 상승장일때는 이것 추가도 좋음.
                    balance = get_balance(coin_name)
                    buy_money = balance * buying_balance_ratio  # 보유 금액의 일정 금액을 구매
                    if balance > min_trade_money :  # 최소 거래 가능 금액 선정 (초기값 : 5000원)
                        buy_coins = buy_money / current_price
                        split_point = str(round(buy_coins, 12)).split(".")
                        for i in range(len(split_point)):
                            if i == 0:  # 1보다 큰 정수 부분
                                buy_coins = float(split_point[i])
                        else:  # 1보다 작은 실수 부분
                            buy_coins = buy_coins + float("0" + "." + split_point[i][:4])
                        order_result = bithumb.buy_market_order(coin_name, buy_coins)  # 시장가 매수
                        coin_bought_price[coin_name] = current_price

                        # dictionary를 저장할때
                        tf = open("Coin_buying_price_Bitsum.json", "w")
                        json.dump(coin_bought_price, tf)
                        tf.close()

                        # dbgout("BTC buy price : " + current_price)
                        # dbgout("BTC buy coin unit : " + buy_coins)
                        print(" %s buy price : %s" % (coin_name, + current_price))
                        print(" %s buy coin unit : %s " % (coin_name, buy_coins))
                        current_price = int(current_price)
                        buying_price = buy_coins * current_price
                        buying_price = int(buying_price)
                        dbgout("Buy coin : " + coin_name + " buying unit price is " + str(current_price) + " won")
                        dbgout("Buy coin : " + coin_name + " buying total price is " + str(buying_price) + " won")

        t_now = datetime.datetime.now()
        print(t_now)
        time.sleep(working_period_time)  # 일정시간마다 구매여부 판단.
    except Exception as e:
        print(e)
        time.sleep(10)
