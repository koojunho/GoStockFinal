import pathlib
from datetime import datetime

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from gostock.apps.two_percent_up.Stock import Stock
from gostock.kiwoom.Kiwoom import MyKiwoom
from gostock.utils import *


class Dialog(QDialog):
    def __init__(self, kiwoom):
        super().__init__()
        self.setWindowTitle("2% 상승 시 매수")

        self.stocks = {}

        self.kiwoom = kiwoom
        self.kiwoom.add_real_data_callback(self.update_real_data)

        self.soar_timer = QTimer()
        self.soar_timer.setInterval(10000)
        self.soar_timer.timeout.connect(self._on_soar_timer)
        self.soar_timer.start()

    def closeEvent(self, event):
        self.soar_timer.stop()
        self.kiwoom.unreg_screen_real(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용)
        self.kiwoom.remove_real_data_callback(self.update_real_data)

    def _on_soar_timer(self):
        self.load_전일대비등락률상위()

    def load_전일대비등락률상위(self):
        def result(rows):
            self.prepare_stock_objs(rows)
            now = datetime.today()
            s_date = now.strftime('%Y-%m-%d')
            s_h = now.strftime('%H')
            s_m = now.strftime('%M')
            s_s = now.strftime('%S')
            s_to_h = f'{s_date} {s_h}시'
            s_to_m = f'{s_to_h} {s_m}분'
            s_to_s = f'{s_to_m} {s_s}초'
            pathlib.Path(f'_data/전일대비등락률상위/{s_date}/{s_to_h}/{s_to_m}').mkdir(parents=True, exist_ok=True)
            FileUtil.write_json(f'_data/전일대비등락률상위/{s_date}/{s_to_h}/{s_to_m}/{s_to_s}.json', rows)

        self.kiwoom.unreg_screen_real(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용)
        self.kiwoom.opt10027_전일대비등락률상위요청(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용, result)

    def prepare_stock_objs(self, rows):
        stocks = {}
        for idx, rank_data in enumerate(rows):
            rank = idx + 1
            code = rank_data.get('종목코드')
            name = rank_data.get('종목명')
            market = StockUtil.get_market(code)
            if not market:
                return
            existing_stock = self.stocks.get(code)
            if existing_stock:  # 원래 구독 중인 종목은 기존 객체를 사용.
                stocks[code] = existing_stock
            else:
                stock = Stock(code, name, market)
                stocks[code] = stock
        self.stocks = stocks

    def update_real_data(self, code, real_type, data):
        stock = self.stocks.get(code)

        # 시세정보 TR을 호출하면 이어서 실시간 데이터가 지속적으로 들어온다.
        # self.kiwoom.unreg_all_real(MyKiwoom.SCREEN_거래량급증요청_실시간열람용) 호출로 막기는 하지만
        # 몇 건은 여기까지 들어오게 된다. 따라서 명시적으로 구독 중인 종목이 아니면 무시한다.
        if not stock:
            # print('비구독 코드:', code, real_type)
            return

        if real_type == "주식체결":
            kiwoom_time, price = data.get('시간'), abs(int(data.get('체결가')))
            r = stock.set_current_price(kiwoom_time, price, data)
            if r:
                KiwoomUtil.ding()

    def buy(self, code):
        self.kiwoom.SendOrder(
            rqname="시장가매수", screen="9101", accno="6064198810", order_type=1,
            code=code, quantity=1, price=0, hoga="03", order_no=""
        )
