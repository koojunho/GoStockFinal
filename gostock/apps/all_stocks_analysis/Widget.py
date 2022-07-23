import pathlib
from datetime import datetime

from PyQt5.QtWidgets import *

from gostock.kiwoom.Kiwoom import MyKiwoom
from gostock.utils import *


class Widget(QWidget):
    def __init__(self, kiwoom):
        super().__init__()
        self.kiwoom = kiwoom

        btn_load_all = QPushButton("전체종목 분봉차트 불러오기")
        btn_load_all.clicked.connect(self.refresh)

        self.stocks_table = QTableWidget()
        self.stocks_table.setColumnCount(4)
        self.stocks_table.setHorizontalHeaderItem(0, QTableWidgetItem('종목코드'))
        self.stocks_table.setHorizontalHeaderItem(1, QTableWidgetItem('종목명'))
        self.stocks_table.setHorizontalHeaderItem(2, QTableWidgetItem('등락률'))
        self.stocks_table.setHorizontalHeaderItem(3, QTableWidgetItem('시초가'))
        self.stocks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.stocks_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.stocks_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.load_stocks_file()

        stocks_layout = QVBoxLayout()
        stocks_layout.addWidget(btn_load_all)
        stocks_layout.addWidget(self.stocks_table)

        layout = QHBoxLayout()
        layout.addLayout(stocks_layout)
        layout.addWidget(QTableWidget())  # todo: temp
        self.setLayout(layout)

        self.result = []

    def enter(self):
        self.kiwoom.gap_comm_rq_work = 0.8  # 이 앱은 장중에 사용하는 것이 아니므로 TR 호출 간격을 4초에서 0.8초로 줄인다.
        return True

    def leave(self):
        self.kiwoom.gap_comm_rq_work = 4

    def refresh(self):
        if not self.kiwoom.is_login():
            if QtUtil.ask_login():
                self.kiwoom.login()
            return
        self.load_전일대비등락률상위()

    def load_stocks_file(self):
        path = pathlib.Path('_data/지난상위종목.json')
        if not path.is_file():
            return
        stocks_data = DotDict(FileUtil.load_json('_data/지난상위종목.json'))
        stocks = stocks_data.stocks
        self.stocks_table.setRowCount(0)
        for stock in stocks:
            stock = DotDict(stock)
            code = stock['종목코드']
            idx = self.stocks_table.rowCount()
            self.stocks_table.insertRow(idx)
            self.stocks_table.setItem(idx, 0, QTableWidgetItem(code))
            self.stocks_table.setItem(idx, 1, QTableWidgetItem(stock['종목명']))
            self.stocks_table.setItem(idx, 2, QTableWidgetItem(stock['등락률']))

    def load_전일대비등락률상위(self):
        def end():
            result = {'updated_at': datetime.today().strftime('%Y-%m-%d %H:%M:%S'), 'stocks': self.result}
            FileUtil.write_json('_data/지난상위종목.json', result)
            self.load_stocks_file()
            idx = 0
            for stock in self.result:
                self.load_분봉차트(idx, stock['종목코드'])
                idx += 1

        def keep_loading(rows):
            self.kiwoom.set_real_remove(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용, 'ALL')
            self.result += rows
            if self.kiwoom.last_next == '2':
                self.kiwoom.opt10027_전일대비등락률상위요청(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용, keep_loading, 상하한포함=1, next=2)
            else:
                end()

        self.result = []
        self.kiwoom.opt10027_전일대비등락률상위요청(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용, keep_loading, 상하한포함=1)

    def load_분봉차트(self, idx, code):
        def keep_loading(rows):
            self.kiwoom.set_real_remove(MyKiwoom.SCREEN_주식분봉차트조회요청_분석용, 'ALL')
            pathlib.Path(f'_data/주식분봉차트조회요청').mkdir(parents=True, exist_ok=True)
            rows.reverse()
            FileUtil.write_json(f'_data/주식분봉차트조회요청/{code}.json', rows)
            self.stocks_table.setItem(idx, 3, QTableWidgetItem(rows[0]['현재가']))

        self.kiwoom.opt10080_주식분봉차트조회요청(MyKiwoom.SCREEN_주식분봉차트조회요청_분석용, code, 0, keep_loading)
