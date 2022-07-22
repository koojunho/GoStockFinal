from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gostock.kiwoom.Kiwoom import MyKiwoom
from gostock.utils import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("9Cells", "GoStock")
        if self.settings.value("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.value("windowState"):
            self.restoreState(self.settings.value("windowState"))

        self.setWindowTitle('GoStock Final')
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.kiwoom = MyKiwoom()

        bar = self.menuBar()

        menu = bar.addMenu("파일(&F)")
        action = menu.addAction("로그인(&L)")
        action.setShortcut(QKeySequence("Ctrl+L"))
        action.triggered.connect(self.will_login)

        menu = bar.addMenu("테스트(&T)")
        action = menu.addAction("기간내 상승 잡기 (&1)")
        action.setShortcut(QKeySequence("Ctrl+1"))
        action.triggered.connect(self.open_dlg_two_percent)
        action = menu.addAction("기간내 상승 테스트 (&2)")
        action.setShortcut(QKeySequence("Ctrl+2"))
        action.triggered.connect(self.open_dlg_check_two_in_five)

        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # todo: 얘를 기본 가운데에 위치시킨다.
        btn = QPushButton("로그인")
        btn.clicked.connect(self.will_login)
        layout.addWidget(btn)

        # btn = QPushButton("2% 상승 시 매수")
        # btn.clicked.connect(self.open_dlg_two_percent)
        # layout.addWidget(btn)
        #
        # btn = QPushButton("5초 내에 2% 상승 여부 확인")
        # btn.clicked.connect(self.open_dlg_check_two_in_five)
        # layout.addWidget(btn)

        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._on_timer)
        self.timer.start()

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        QMainWindow.closeEvent(self, event)

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
        from gostock.apps.two_percent_up.Widget import Widget
        widget = Widget(self.kiwoom)
        self.setCentralWidget(widget)

    def open_dlg_check_two_in_five(self):
        from gostock.apps.check_two_in_five.Widget import Widget
        widget = Widget(self.kiwoom)
        self.setCentralWidget(widget)
