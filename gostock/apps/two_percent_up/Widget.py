import pathlib
from datetime import datetime

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from gostock.apps.two_percent_up.Stock import Stock
from gostock.kiwoom.Kiwoom import MyKiwoom
from gostock.utils import *


class Widget(QWidget):
    def __init__(self, kiwoom):
        super().__init__()
        self.kiwoom = kiwoom
        self.stocks = {}
        self.soar_timer = None

        toolbar_layout = QHBoxLayout()

        self.last_loading_time = QLabel('얻어온 목록이 없습니다.')
        toolbar_layout.addWidget(self.last_loading_time)

        btn_select = QPushButton('목록얻기')
        btn_select.clicked.connect(self._on_btn_load_stock_list_clicked)
        toolbar_layout.addWidget(btn_select, alignment=Qt.AlignRight)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderItem(0, QTableWidgetItem('종목코드'))
        self.table_widget.setHorizontalHeaderItem(1, QTableWidgetItem('종목명'))
        self.table_widget.setHorizontalHeaderItem(2, QTableWidgetItem('등락률'))
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        l_v_layout = QVBoxLayout()
        l_v_layout.addLayout(toolbar_layout)
        l_v_layout.addWidget(self.table_widget)

        lr_layout = QHBoxLayout()
        lr_layout.addLayout(l_v_layout)
        lr_layout.addWidget(QTableWidget())  # todo: temp

        layout = QVBoxLayout()
        layout.addLayout(lr_layout)
        self.setLayout(layout)

    def enter(self):
        self.stocks = {}

        self.kiwoom.add_real_data_callback(self.update_real_data)

        self.soar_timer = QTimer()
        self.soar_timer.setInterval(10000)
        self.soar_timer.timeout.connect(self._on_soar_timer)
        self.soar_timer.start()
        self.load_stock_list()

        return True

    def leave(self):
        self.soar_timer.stop()
        self.kiwoom.set_real_remove(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용, 'ALL')
        self.kiwoom.unreg_screen_real(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용)
        self.kiwoom.remove_real_data_callback(self.update_real_data)

    def _on_soar_timer(self):
        self.load_stock_list()

    def _on_btn_load_stock_list_clicked(self):
        if not self.kiwoom.is_login():
            if QtUtil.ask_login():
                self.kiwoom.login()
            return

        # 버튼을 누른 경우 바로 호출하고 싶어서 delay gap을 0으로 세팅
        # 응답이 받아지면 load_stock_list에서 4로 다시 되돌린다.
        self.kiwoom.gap_comm_rq_work = 0
        self.load_stock_list()

    def load_stock_list(self):
        def result(rows):
            self.kiwoom.gap_comm_rq_work = 4
            self.kiwoom.set_real_remove(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용, 'ALL')
            self.last_loading_time.setText(f'마지막 업데이트: {datetime.today().strftime("%Y-%m-%d %H:%M:%S")}')
            code_list = self.prepare_stock_objs(rows)
            if code_list:
                self.draw_table()
                self.kiwoom.reg_real(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용, code_list)
            # self.save_tr(rows)

        self.kiwoom.opt10027_전일대비등락률상위요청(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용, result)

    def save_tr(self, rows):
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

    def get_stock_codes(self):
        return list(self.stocks.keys())

    def prepare_stock_objs(self, rows):
        stocks = {}
        for idx, row in enumerate(rows):
            rank = idx + 1
            code = row.get('종목코드')
            name = row.get('종목명')
            market = StockUtil.get_market(code)
            if not market:
                return None
            rate = float(row.get('등락률'))
            if rate > 20:
                continue
            row['use'] = True
            existing_stock = self.stocks.get(code)
            if existing_stock:  # 원래 구독 중인 종목은 기존 객체를 사용.
                stocks[code] = existing_stock
            else:
                stock = Stock(code, name, market)
                stocks[code] = stock
            if len(stocks) >= 100:
                break
        self.stocks = stocks
        return self.get_stock_codes()

    def draw_table(self):
        self.table_widget.setRowCount(len(self.stocks))
        idx = 0
        for code in self.stocks:
            stock = self.stocks.get(code)
            self.table_widget.setItem(idx, 0, QTableWidgetItem(stock.code))
            self.table_widget.setItem(idx, 1, QTableWidgetItem(stock.name))
            idx += 1

    def update_real_data(self, code, real_type, data):
        stock = self.stocks.get(code)

        # 시세정보 TR을 호출하면 이어서 실시간 데이터가 지속적으로 들어온다.
        # self.kiwoom.unreg_all_real() 호출로 막기는 하지만
        # 몇 건은 여기까지 들어오게 된다. 따라서 명시적으로 구독 중인 종목이 아니면 무시한다.
        if not stock:
            # print('비구독 코드:', code, real_type)
            return

        if real_type == "주식체결":
            kiwoom_time, price = data.get('시간'), abs(int(data.get('체결가')))
            stock.set_current_price(kiwoom_time, price, data)
            if stock.soar:
                curr_rate = float(data.get('등락율'))
                print(
                    f'{stock.code} {stock.name}, {curr_rate}% ({stock.soar_rate:.2f}% 상승), 주문량 {stock.order_per_sec_last}, 지연 {stock.time_delay}')
                KiwoomUtil.ding(1)
                QtUtil.copy_to_clipboard(f'{stock.code} {stock.name}')

    def buy(self, code):
        self.kiwoom.SendOrder(
            rqname="시장가매수", screen="9101", accno="6064198810", order_type=1,
            code=code, quantity=1, price=0, hoga="03", order_no=""
        )
