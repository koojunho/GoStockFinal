import pathlib
from datetime import datetime

from gostock.kiwoom.Kiwoom import MyKiwoom
from gostock.utils import *


class StockRanking:
    def __init__(self, kiwoom):
        self.kiwoom = kiwoom
        self.result = None
        self.screen = MyKiwoom.SCREEN_전일대비등락률상위요청_실시간열람용
        self.filename = '_data/지난상위종목.json'

    def download_data(self, done):
        def downloaded():
            result = {'updated_at': datetime.today().strftime('%Y-%m-%d %H:%M:%S'), 'stocks': self.result}
            FileUtil.write_json(self.filename, result)
            done()

        def keep_loading(rows):
            self.kiwoom.set_real_remove(self.screen, 'ALL')
            self.result += rows
            if self.kiwoom.last_next == '2':
                self.kiwoom.opt10027_전일대비등락률상위요청(self.screen, keep_loading, 상하한포함=1, next=2)
            else:
                downloaded()

        self.result = []
        self.kiwoom.opt10027_전일대비등락률상위요청(self.screen, keep_loading, 상하한포함=1)

    def load_downloaded_file(self):
        path = pathlib.Path(self.filename)
        if not path.is_file():
            return None
        return DotDict(FileUtil.load_json(self.filename))
