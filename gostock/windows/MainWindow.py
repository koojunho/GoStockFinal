import pathlib
from datetime import datetime

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from gostock.kiwoom.Kiwoom import MyKiwoom
from gostock.utils import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.kiwoom = MyKiwoom()
        self.will_login()

        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._on_timer)
        self.timer.start()

        self.soar_timer = QTimer()
        self.soar_timer.setInterval(4000)
        self.soar_timer.timeout.connect(self._on_soar_timer)

    def will_login(self):
        self.kiwoom.add_login_callback(self.did_login)
        self.kiwoom.login()

    def did_login(self, err_code):
        self.kiwoom.remove_login_callback(self.did_login)
        if err_code == 0:
            self.refresh_all_stocks_code_name()
            self.soar_timer.start()

    def _on_timer(self):
        self.kiwoom.interval()

    def _on_soar_timer(self):
        self.load_전일대비등락률상위()

    def refresh_all_stocks_code_name(self):
        for market_code in [StockUtil.MARKET_KOSPI, StockUtil.MARKET_KOSDAQ]:
            code_list = list(filter(len, self.kiwoom.GetCodeListByMarket(market_code).split(';')))
            for code in code_list:
                name = self.kiwoom.GetMasterCodeName(code)
                StockUtil.add_stock(market_code, code, name)

    def load_전일대비등락률상위(self):
        def result(rows):
            now = datetime.today()
            s_date = now.strftime('%Y-%m-%d')
            s_h = now.strftime('%H')
            s_m = now.strftime('%M')
            s_s = now.strftime('%S')
            s_to_h = f'{s_date} {s_h}시'
            s_to_m = f'{s_to_h} {s_m}분'
            s_to_s = f'{s_to_m} {s_s}초'
            pathlib.Path(f'_data/{s_to_h}/{s_to_m}').mkdir(parents=True, exist_ok=True)
            FileUtil.write_json(f'_data/{s_to_h}/{s_to_m}/{s_to_s}.json', rows)

        self.kiwoom.opt10027_전일대비등락률상위요청(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용, result)
