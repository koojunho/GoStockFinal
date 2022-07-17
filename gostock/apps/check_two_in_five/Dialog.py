from PyQt5.QtWidgets import *

from gostock.kiwoom.Kiwoom import MyKiwoom
from gostock.utils import *


class Dialog(QDialog):
    def __init__(self, kiwoom):
        super().__init__()
        self.setWindowTitle("5초 내에 2% 상승 여부 확인")

        self.kiwoom = kiwoom

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.edit = QLineEdit()
        layout.addWidget(self.edit)

        btn = QPushButton("실행")
        btn.clicked.connect(self.load_tick_tr)
        layout.addWidget(btn)

        btn = QPushButton("테스트")
        btn.clicked.connect(self.test)
        layout.addWidget(btn)

        self.code = None
        self.run = True
        self.yyyymmdd = None
        self.result = []

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
                    FileUtil.write_json(f'_data/{self.yyyymmdd}_{self.code}.json', self.result)
                    break
                if amount == 1:  # 거래량이 1인 매매 제거
                    continue
                self.result.append(row)
            if self.run:
                self.kiwoom.opt10079_주식틱차트조회요청(MyKiwoom.SCREEN_주식틱차트조회요청_틱얻기, self.code, 2, result)

        self.code = self.edit.text()
        self.run = True
        self.yyyymmdd = None
        self.result = []
        self.kiwoom.opt10079_주식틱차트조회요청(MyKiwoom.SCREEN_주식틱차트조회요청_틱얻기, self.code, 0, result)

    def test(self):
        rows = FileUtil.load_json(f'_data/20220715_357580.json')
        begin_price = 12700
        last_time = None
        price_history = []
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
                if curr_time - ph.time > 5:
                    break
                # 급등을 찾아야 하므로 급등률이 2보다 작으면 종료
                if curr_rate - ph.rate < 2:
                    break
                soar = True
                break

            if soar:
                print('급등:', curr_time, curr_price)

            price_history.append(DotDict({'time': curr_time, 'price': curr_price, 'rate': curr_rate}))
            price_history = price_history[-5:]
        print('종료')
