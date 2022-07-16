import time

from gostock.utils import *


class StockA:
    SIZE_OF_PRICE_HISTORY = 5

    def __init__(self, code, name, market):
        self.code = code
        self.name = name

        self.market = market
        if market == '0':
            self.s_market = '피'
        elif market == '10':
            self.s_market = '닥'

        self.last_time = None

        self.time_delay = 0

        self.price_history = []

    def set_current_price(self, kiwoom_time, price, data, created_at=None):
        curr_dt = KiwoomUtil.kiwoom_time_2_datetime(kiwoom_time)
        curr_time = KiwoomUtil.datetime_2_timestamp(curr_dt)
        curr_price = price
        curr_rate = data.get('등락율')

        new_time = False
        if self.last_time != kiwoom_time:
            self.last_time = kiwoom_time
            new_time = True

        self.time_delay = time.time() - curr_time
