from PyQt5.QtWidgets import *

from gostock.utils import *


class LoginWidget(QWidget):
    def __init__(self, kiwoom):
        super().__init__()
        self.kiwoom = kiwoom

        self.btn_login = QPushButton("로그인")
        self.btn_login.clicked.connect(self.will_login)

        layout = QVBoxLayout()
        layout.addWidget(self.btn_login)
        self.setLayout(layout)

    def enter(self):
        return True

    def leave(self):
        pass

    def will_login(self):
        self.kiwoom.add_login_callback(self.did_login)
        self.kiwoom.login()

    def did_login(self, err_code):
        # 초과 호출로 재로그인 요구 시 여기에 에러 코드가 떨어질지 궁금해서 주석처리.
        # self.kiwoom.remove_login_callback(self.did_login)
        if err_code != 0:
            print('로그인 에러')
            return
        self.btn_login.setDisabled(True)
        self.refresh_all_stocks_code_name()

    def refresh_all_stocks_code_name(self):
        for market_code in [StockUtil.MARKET_KOSPI, StockUtil.MARKET_KOSDAQ]:
            code_list = list(filter(len, self.kiwoom.GetCodeListByMarket(market_code).split(';')))
            for code in code_list:
                name = self.kiwoom.GetMasterCodeName(code)
                StockUtil.add_stock(market_code, code, name)
