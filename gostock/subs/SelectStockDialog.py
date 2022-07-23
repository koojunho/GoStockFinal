from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from gostock.kiwoom.Kiwoom import MyKiwoom
from gostock.utils import *


class SelectStockDialog(QDialog):
    def __init__(self, kiwoom):
        super().__init__()

        self.kiwoom = kiwoom

        self.setWindowTitle("종목검색")

        self.settings = QSettings("9Cells", "GoStock")
        if self.settings.value("SelectStockDialog_geometry"):
            self.restoreGeometry(self.settings.value("SelectStockDialog_geometry"))

        self.all_tab = AllStocksWidget(kiwoom)
        self.all_tab.stocks_table.doubleClicked.connect(self.all_table_double_clicked)

        self.rank_tab = RankingStocksWidget(kiwoom)
        self.rank_tab.stocks_table.doubleClicked.connect(self.rank_table_double_clicked)

        tabs = QTabWidget()
        tabs.addTab(self.all_tab, '전체종목')
        tabs.addTab(self.rank_tab, '지난상위종목')

        btn_select = QPushButton('선택')
        btn_select.clicked.connect(self.select)

        layout = QVBoxLayout()
        layout.addWidget(tabs)
        layout.addWidget(btn_select, alignment=Qt.AlignRight)
        self.setLayout(layout)

        self.code = None

    def closeEvent(self, event):
        self.settings.setValue("SelectStockDialog_geometry", self.saveGeometry())
        super().closeEvent(event)

    def all_table_double_clicked(self, mi):
        row_idx = mi.row()
        item = self.all_tab.stocks_table.item(row_idx, 1)
        code = item.text()
        self.code = code
        self.accept()

    def rank_table_double_clicked(self, mi):
        row_idx = mi.row()
        item = self.rank_tab.stocks_table.item(row_idx, 0)
        code = item.text()
        self.code = code
        self.accept()

    def select(self):
        if not self.code:
            return
        self.accept()


class AllStocksWidget(QWidget):
    def __init__(self, kiwoom):
        super().__init__()

        self.kiwoom = kiwoom

        top_h_layout = QHBoxLayout()

        self.label_update = QLabel('종목 정보가 없습니다. 새로고침을 클릭하세요.')
        top_h_layout.addWidget(self.label_update)

        btn_refresh = QPushButton('새로고침')
        btn_refresh.clicked.connect(self.refresh)
        top_h_layout.addWidget(btn_refresh, alignment=Qt.AlignRight)

        self.stocks_table = QTableWidget()
        self.stocks_table.setColumnCount(3)
        self.stocks_table.setHorizontalHeaderItem(0, QTableWidgetItem('시장'))
        self.stocks_table.setHorizontalHeaderItem(1, QTableWidgetItem('종목코드'))
        self.stocks_table.setHorizontalHeaderItem(2, QTableWidgetItem('종목명'))
        self.stocks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.stocks_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.stocks_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.load_stocks_file()

        layout = QVBoxLayout()
        layout.addLayout(top_h_layout)
        layout.addWidget(self.stocks_table)
        self.setLayout(layout)

    def load_stocks_file(self):
        path = Path(StockUtil.STOCKS_FILENAME)
        if not path.is_file():
            return
        stocks_data = DotDict(FileUtil.load_json(StockUtil.STOCKS_FILENAME))
        self.label_update.setText(f'마지막 업데이트: {stocks_data.updated_at}')
        stocks = stocks_data.stocks
        self.stocks_table.setRowCount(0)
        for stock in stocks:
            stock = DotDict(stock)
            idx = self.stocks_table.rowCount()
            self.stocks_table.insertRow(idx)
            self.stocks_table.setItem(idx, 0, QTableWidgetItem(stock.market))
            self.stocks_table.setItem(idx, 1, QTableWidgetItem(stock.code))
            self.stocks_table.setItem(idx, 2, QTableWidgetItem(stock.name))

    def refresh(self):
        if not self.kiwoom.is_login():
            if QtUtil.ask_login():
                self.kiwoom.login()
            return
        self.kiwoom.refresh_all_stocks_code_name()
        self.load_stocks_file()


class RankingStocksWidget(QWidget):
    def __init__(self, kiwoom):
        super().__init__()

        self.kiwoom = kiwoom

        top_h_layout = QHBoxLayout()

        self.label_update = QLabel('종목 정보가 없습니다. 새로고침을 클릭하세요.')
        top_h_layout.addWidget(self.label_update)

        btn_refresh = QPushButton('새로고침')
        btn_refresh.clicked.connect(self.refresh)
        top_h_layout.addWidget(btn_refresh, alignment=Qt.AlignRight)

        self.stocks_table = QTableWidget()
        self.stocks_table.setColumnCount(3)
        self.stocks_table.setHorizontalHeaderItem(0, QTableWidgetItem('종목코드'))
        self.stocks_table.setHorizontalHeaderItem(1, QTableWidgetItem('종목명'))
        self.stocks_table.setHorizontalHeaderItem(2, QTableWidgetItem('등락률'))
        self.stocks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.stocks_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.stocks_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.load_stocks_file()

        layout = QVBoxLayout()
        layout.addLayout(top_h_layout)
        layout.addWidget(self.stocks_table)
        self.setLayout(layout)

        self.result = []

    def load_stocks_file(self):
        path = Path('_data/지난상위종목.json')
        if not path.is_file():
            return
        stocks_data = DotDict(FileUtil.load_json('_data/지난상위종목.json'))
        self.label_update.setText(f'마지막 업데이트: {stocks_data.updated_at}')
        stocks = stocks_data.stocks
        self.stocks_table.setRowCount(0)
        for stock in stocks:
            stock = DotDict(stock)
            idx = self.stocks_table.rowCount()
            self.stocks_table.insertRow(idx)
            self.stocks_table.setItem(idx, 0, QTableWidgetItem(stock['종목코드']))
            self.stocks_table.setItem(idx, 1, QTableWidgetItem(stock['종목명']))
            self.stocks_table.setItem(idx, 2, QTableWidgetItem(stock['등락률']))

    def refresh(self):
        if not self.kiwoom.is_login():
            if QtUtil.ask_login():
                self.kiwoom.login()
            return
        self.load_전일대비등락률상위()

    def load_전일대비등락률상위(self):
        def end():
            result = {'updated_at': datetime.today().strftime('%Y-%m-%d %H:%M:%S'), 'stocks': self.result}
            FileUtil.write_json('_data/지난상위종목.json', result)
            self.load_stocks_file()

        def keep_loading(rows):
            self.kiwoom.set_real_remove(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용, 'ALL')
            self.result += rows
            if self.kiwoom.last_next == '2':
                self.kiwoom.opt10027_전일대비등락률상위요청(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용, keep_loading, next=2)
            else:
                end()

        self.result = []
        self.kiwoom.opt10027_전일대비등락률상위요청(MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용, keep_loading)
