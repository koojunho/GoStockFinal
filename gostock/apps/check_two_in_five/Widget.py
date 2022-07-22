import pathlib
from datetime import datetime
import glob
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
        btn.clicked.connect(self.test)
        load_stock_layout.addWidget(btn)

        tick_data_table = QTableWidget()

        stocks_layout = QVBoxLayout()
        stocks_layout.addLayout(load_stock_layout)
        stocks_layout.addWidget(tick_data_table)

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
                    self.run = False
                    self.result.reverse()
                    pathlib.Path(f'_data/주식틱차트조회요청').mkdir(parents=True, exist_ok=True)
                    FileUtil.write_json(f'_data/주식틱차트조회요청/{self.code}_{self.name}.json', self.result)
                    print('완료')
                    break
                if amount == 1:  # 거래량이 1인 매매 제거
                    continue
                self.result.append(row)
            if self.run:
                self.kiwoom.opt10079_주식틱차트조회요청(MyKiwoom.SCREEN_주식틱차트조회요청_틱얻기, self.code, 2, result)

        self.init_members()
        self.code = self.edit.text()
        self.name = StockUtil.get_name(self.code)
        if not self.name:
            return
        self.kiwoom.opt10079_주식틱차트조회요청(MyKiwoom.SCREEN_주식틱차트조회요청_틱얻기, self.code, 0, result)

    def test(self):
        code = self.edit.text()
        if not code:
            return

        rows = []
        for filename in glob.glob(f'_data/주식틱차트조회요청/{code}*'):
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
                if curr_rate - ph.rate < 2:
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
