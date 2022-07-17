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

        layout = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        btn = QPushButton("2% 상승 시 매수")
        btn.clicked.connect(self.open_dlg_two_percent)
        layout.addWidget(btn)

        btn = QPushButton("5초 내에 2% 상승 여부 확인")
        btn.clicked.connect(self.open_dlg_check_two_in_five)
        layout.addWidget(btn)

    def will_login(self):
        self.kiwoom.add_login_callback(self.did_login)
        self.kiwoom.login()

    def did_login(self, err_code):
        self.kiwoom.remove_login_callback(self.did_login)
        if err_code != 0:
            print('로그인 에러')
            return
        self.refresh_all_stocks_code_name()

    def refresh_all_stocks_code_name(self):
        for market_code in [StockUtil.MARKET_KOSPI, StockUtil.MARKET_KOSDAQ]:
            code_list = list(filter(len, self.kiwoom.GetCodeListByMarket(market_code).split(';')))
            for code in code_list:
                name = self.kiwoom.GetMasterCodeName(code)
                StockUtil.add_stock(market_code, code, name)

    def _on_timer(self):
        self.kiwoom.interval()

    def open_dlg_two_percent(self):
        from gostock.apps.two_percent_up.Dialog import Dialog
        dlg = Dialog(self.kiwoom)
        dlg.exec()

    def open_dlg_check_two_in_five(self):
        from gostock.apps.check_two_in_five.Dialog import Dialog
        dlg = Dialog(self.kiwoom)
        dlg.exec()
