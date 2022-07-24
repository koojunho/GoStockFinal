from PyQt5.QtWidgets import *

from gostock.data import *
from gostock.utils import *


class Widget(QWidget):
    def __init__(self, kiwoom):
        super().__init__()
        self.kiwoom = kiwoom
        self.stock_ranking = StockRanking(kiwoom)
        self.one_min_chart_data = OneMinChartData(kiwoom)

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
        self.fill_table_with_stock_ranking()

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
        def done():
            self.fill_table_with_stock_ranking()
            self.download_all_stocks_one_min_chart_data()

        if not self.kiwoom.is_login():
            if QtUtil.ask_login():
                self.kiwoom.login()
            return

        self.stock_ranking.download_data(done)

    def fill_table_with_stock_ranking(self):
        stocks_data = self.stock_ranking.load_downloaded_file()
        if not stocks_data:
            return
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

    def download_all_stocks_one_min_chart_data(self):
        def done(code):
            rows = self.one_min_chart_data.load_downloaded_file(code)
            item = QtUtil.find_table_item(self.stocks_table, code, 0)
            self.stocks_table.setItem(item.row(), 3, QTableWidgetItem(rows[0]['현재가']))

        stocks_data = self.stock_ranking.load_downloaded_file()
        if not stocks_data:
            return

        for stock in stocks_data.stocks:
            code = stock['종목코드']
            self.one_min_chart_data.download_data(code, done)
