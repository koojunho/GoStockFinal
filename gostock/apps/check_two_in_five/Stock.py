import time

from gostock.utils import *


class Stock:
    SIZE_OF_PRICE_HISTORY = 5

    def __init__(self, code, name, market):
        self.code = code
        self.name = name

        self.market = market
        if market == '0':
            self.s_market = '피'
        elif market == '10':
            self.s_market = '닥'

        self.time_delay = 0

        self.last_time = None

        self.price_history = []

    def set_current_price(self, kiwoom_time, price, data, created_at=None):
        curr_dt = KiwoomUtil.kiwoom_time_2_datetime(kiwoom_time)
        curr_time = KiwoomUtil.datetime_2_timestamp(curr_dt)
        curr_price = price
        curr_rate = float(data.get('등락율'))

        self.time_delay = time.time() - curr_time
        if self.time_delay > 1:
            print('delay:', self.time_delay)
            # return

        if self.last_time == kiwoom_time:
            return
        self.last_time = kiwoom_time

        soar = False
        for ph in reversed(self.price_history):
            # 5초 이내의 급등을 찾아야 하므로 5초를 넘어가면 종료
            if curr_time - ph.time > 5:
                break
            # 급등을 찾아야 하므로 급등률이 2보다 작으면 종료
            if curr_rate - ph.rate < 2:
                break
            soar = True
            break

        if soar:
            print('급등:', self.code, self.name, curr_price)

        self.price_history.append(DotDict({'time': curr_time, 'price': curr_price, 'rate': curr_rate}))
        self.price_history = self.price_history[-self.SIZE_OF_PRICE_HISTORY:]
