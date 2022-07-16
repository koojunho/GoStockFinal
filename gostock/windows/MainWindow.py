import pathlib
from datetime import datetime

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from gostock.kiwoom.Kiwoom import MyKiwoom
from gostock.models.stocks.StockA import StockA
from gostock.utils import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.stocks = {}

        self.kiwoom = MyKiwoom()
        self.kiwoom.add_real_data_callback(self.update_real_data)
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

    def get_stock_codes(self):
        return list(self.stocks.keys())

    def prepare_stock_objs(self, rows):
        old_code_list = self.get_stock_codes()
        stocks = {}
        for idx, rank_data in enumerate(rows):
            rank = idx + 1
            code = rank_data.get('종목코드')
            name = rank_data.get('종목명')
            if not code:
                continue
            existing_stock = self.stocks.get(code)
            if existing_stock:  # 원래 구독 중인 종목은 기존 객체를 사용.
                stocks[code] = existing_stock
            else:
                stock = StockA(code, name, StockUtil.get_market(code))
                stocks[code] = stock
        self.stocks = stocks
        new_code_list = self.get_stock_codes()
        return KiwoomUtil.subscribe(old_code_list, new_code_list)

    def update_real_data(self, code, real_type, data):
        # 거래량급증TR 같은 시세정보 api를 호출하면 결과가 반환된 후 이어서 실시간 데이터가 지속적으로 들어온다.
        # self.kiwoom.unreg_all_real(MyKiwoom.SCREEN_거래량급증요청_실시간열람용) 호출로 막기는 하지만
        # 몇 건은 여기까지 들어오게 된다. 따라서 명시적으로 구독 중인 종목이 아니면 무시한다.
        if not self.stocks.get(code):
            # print('비구독 코드:', code, real_type)
            return

        stock = self.stocks.get(code)
        if real_type == "주식호가잔량":
            hoga = {'호가시간': data['호가시간']}
            for i in reversed(range(1, 11)):
                key = f'매도{i}'
                hoga[key] = abs(int(data[key]))
                key = f'매도{i}수량'
                hoga[key] = abs(int(data[key]))
            for i in range(1, 11):
                key = f'매수{i}'
                hoga[key] = abs(int(data[key]))
                key = f'매수{i}수량'
                hoga[key] = abs(int(data[key]))
            stock.set_hoga(hoga)
        elif real_type == "주식체결":
            kiwoom_time, price = data.get('시간'), abs(int(data.get('체결가')))
            stock.set_current_price(kiwoom_time, price, data)
