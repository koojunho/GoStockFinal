import time

from gostock.utils import *


class Stock:
    MAX_SEC = 50
    SIZE_OF_PRICE_HISTORY = MAX_SEC

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

        if self.last_time == kiwoom_time:
            return
        self.last_time = kiwoom_time

        soar = False
        soar_rate = 0
        for ph in reversed(self.price_history):
            # MAX_SEC 초 이내의 급등을 찾아야 하므로 MAX_SEC 초를 넘어가면 종료
            if curr_time - ph.time > self.MAX_SEC:
                break
            # 급등을 찾아야 하므로 급등률이 2%보다 작으면 종료
            # if curr_rate - ph.rate < 2:
            if curr_rate - ph.rate < 0.5:
                break
            soar = True
            soar_rate = curr_rate - ph.rate
            break

        self.price_history.append(DotDict({'time': curr_time, 'price': curr_price, 'rate': curr_rate}))
        self.price_history = self.price_history[-self.SIZE_OF_PRICE_HISTORY:]

        if soar:
            print(f'{self.code} {self.name} -> {curr_rate}% ({soar_rate:.2f}% 상승)')
            return True

        return False
