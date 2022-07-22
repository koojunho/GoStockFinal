import glob
import pathlib
import re
from datetime import datetime

from PyQt5.QtWidgets import *

from gostock.kiwoom.Kiwoom import MyKiwoom
from gostock.utils import *


class Widget(QWidget):
    def __init__(self, kiwoom):
        super().__init__()
        self.kiwoom = kiwoom

        load_stock_layout = QHBoxLayout()

        self.edit = QLineEdit()
        load_stock_layout.addWidget(self.edit)

        btn = QPushButton("틱 데이터 불러오기")
        btn.clicked.connect(self.load_tick_tr)
        load_stock_layout.addWidget(btn)

        btn = QPushButton("종목검색")
        btn.clicked.connect(self.test_tick_data)
        load_stock_layout.addWidget(btn)

        btn = QPushButton("새로고침")
        btn.clicked.connect(self.refresh_tick_data_table)
        load_stock_layout.addWidget(btn)

        self.tick_data_table = QTableWidget()
        self.tick_data_table.setColumnCount(3)
        self.tick_data_table.setHorizontalHeaderItem(0, QTableWidgetItem('날짜'))
        self.tick_data_table.setHorizontalHeaderItem(1, QTableWidgetItem('종목코드'))
        self.tick_data_table.setHorizontalHeaderItem(2, QTableWidgetItem('종목명'))
        self.tick_data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tick_data_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tick_data_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tick_data_table.doubleClicked.connect(self.tick_data_table_double_clicked)
        self.refresh_tick_data_table()

        stocks_layout = QVBoxLayout()
        stocks_layout.addLayout(load_stock_layout)
        stocks_layout.addWidget(self.tick_data_table)

        layout = QHBoxLayout()
        layout.addLayout(stocks_layout)
        layout.addWidget(QTableWidget())  # todo: temp
        self.setLayout(layout)

        self.code = None
        self.name = None
        self.run = True
        self.yyyymmdd = None
        self.result = []
        self.init_members()

    def init_members(self):
        self.code = None
        self.name = None
        self.run = True
        self.yyyymmdd = None
        self.result = []

    def enter(self):
        self.kiwoom.gap_comm_rq_work = 0.8  # 이 앱은 장중에 사용하는 것이 아니므로 TR 호출 간격을 4초에서 0.8초로 줄인다.
        self.init_members()
        return True

    def leave(self):
        self.kiwoom.gap_comm_rq_work = 4

    def load_tick_tr(self):
        def result(rows):
            print(rows)
            for row in rows:
                s_time = row.get('체결시간')[:8]
                amount = int(row.get('거래량'))
                if not self.yyyymmdd:
                    self.yyyymmdd = s_time
                if self.yyyymmdd != s_time:
                    s_date = datetime.strftime(datetime.strptime(self.yyyymmdd, '%Y%m%d'), '%Y-%m-%d')
                    self.run = False
                    self.result.reverse()
                    pathlib.Path(f'_data/주식틱차트조회요청/{s_date}').mkdir(parents=True, exist_ok=True)
                    FileUtil.write_json(f'_data/주식틱차트조회요청/{s_date}/{self.code}_{self.name}.json', self.result)
                    self.refresh_tick_data_table()
                    break
                if amount == 1:  # 거래량이 1인 매매 제거
                    continue
                self.result.append(row)
            if self.run:
                self.kiwoom.opt10079_주식틱차트조회요청(MyKiwoom.SCREEN_주식틱차트조회요청_틱얻기, self.code, 2, result)

        if not self.kiwoom.is_login():
            if QtUtil.ask_login():
                self.kiwoom.login()
            return

        self.init_members()
        self.code = self.edit.text()
        self.name = StockUtil.get_name(self.code)
        if not self.name:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("종목코드가 잘못됐습니다. 종목코드를 다시 입력해주세요.")
            msg.setWindowTitle("잘못된 종목코드")
            msg.exec_()
            return
        self.kiwoom.opt10079_주식틱차트조회요청(MyKiwoom.SCREEN_주식틱차트조회요청_틱얻기, self.code, 0, result)

    def refresh_tick_data_table(self):
        filenames = glob.glob("_data/주식틱차트조회요청/*/*.json")
        self.tick_data_table.setRowCount(len(filenames))
        idx = 0
        for filename in filenames:
            tokens = re.split("\\\\", filename)
            date = tokens[1]
            file = tokens[2]
            tokens = re.split("_", file)
            code = tokens[0]
            fname = tokens[1]
            tokens = re.split("\.", fname)
            name = tokens[0]
            self.tick_data_table.setItem(idx, 0, QTableWidgetItem(date))
            self.tick_data_table.setItem(idx, 1, QTableWidgetItem(code))
            self.tick_data_table.setItem(idx, 2, QTableWidgetItem(name))
            idx += 1

    def tick_data_table_double_clicked(self, mi):
        row_idx = mi.row()
        item = self.tick_data_table.item(row_idx, 1)
        code = item.text()
        self.test_tick_data(code)

    def test_tick_data(self, code):
        rows = []
        for filename in glob.glob(f'_data/주식틱차트조회요청/*/{code}*'):
            rows = FileUtil.load_json(filename)
            print(filename)
            break
        if rows and len(rows) == 0:
            return

        begin_price = int(rows[0].get('현재가'))
        last_time = None
        price_history = []
        sec_size = 50
        for row in rows:
            curr_time = int(row.get('체결시간'))
            if last_time == curr_time:
                continue
            last_time = curr_time

            curr_price = int(row.get('현재가'))
            curr_rate = (curr_price / begin_price - 1) * 100

            soar = False
            for ph in reversed(price_history):
                # 5초 이내의 급등을 찾아야 하므로 5초를 넘어가면 종료
                if curr_time - ph.time > sec_size:
                    break
                # 급등을 찾아야 하므로 급등률이 2보다 작으면 종료
                if curr_rate - ph.rate < 1:
                    break
                soar = True
                break

            if soar:
                dt = datetime.strptime(str(curr_time), '%Y%m%d%H%M%S')
                s_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                print(f'급등:', s_date)

            price_history.append(DotDict({'time': curr_time, 'price': curr_price, 'rate': curr_rate}))
            price_history = price_history[-sec_size:]
        print('완료')
