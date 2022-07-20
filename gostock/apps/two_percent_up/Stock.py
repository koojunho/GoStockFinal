import time

from gostock.utils import *


class Stock:
    MAX_SEC = 10
    SIZE_OF_PRICE_HISTORY = MAX_SEC

    def __init__(self, code, name, market):
        self.code = code
        self.name = name
        self.market = market

        self.time_delay = 0

        self.last_time = None

        self.order_per_sec = 0
        self.order_per_sec_last = 0

        self.soar = False
        self.soar_rate = 0

        self.price_history = []

    def set_current_price(self, kiwoom_time, price, data, created_at=None):
        curr_dt = KiwoomUtil.kiwoom_time_2_datetime(kiwoom_time)
        curr_time = KiwoomUtil.datetime_2_timestamp(curr_dt)
        curr_price = price
        curr_rate = float(data.get('등락율'))

        self.time_delay = time.time() - curr_time

        self.order_per_sec += 1

        self.soar = False
        self.soar_rate = 0

        if self.last_time == kiwoom_time:
            return
        self.last_time = kiwoom_time

        self.order_per_sec_last = self.order_per_sec
        self.order_per_sec = 0

        for ph in reversed(self.price_history):
            # 주문이 적은데 급등이면 피한다
            if self.order_per_sec_last < 20:
                break

            # MAX_SEC 초 이내의 급등을 찾아야 하므로 MAX_SEC 초를 넘어가면 종료
            if curr_time - ph.time > self.MAX_SEC:
                break

            # # 급등을 찾아야 하므로 급등률이 1%보다 작으면 종료
            # if curr_rate - ph.rate < 1:
            #     break

            # 급등을 찾아야 하므로 호가 갭이 4보다 작으면 종료
            if StockUtil.get_hoga_gap(ph.price, curr_price, self.market) < 4:
                break

            self.soar = True
            self.soar_rate = curr_rate - ph.rate
            self.price_history = []
            break

        self.price_history.append(DotDict({'time': curr_time, 'price': curr_price, 'rate': curr_rate}))
        self.price_history = self.price_history[-self.SIZE_OF_PRICE_HISTORY:]
