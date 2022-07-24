import pathlib

from gostock.kiwoom.Kiwoom import MyKiwoom
from gostock.utils import *


class OneMinChartData:
    def __init__(self, kiwoom):
        self.kiwoom = kiwoom
        self.screen = MyKiwoom.SCREEN_주식분봉차트조회요청_분석용

    def download_data(self, code, done):
        def downloaded(rows):
            self.kiwoom.set_real_remove(self.screen, 'ALL')
            # todo: 최근 날짜만 남기고 더 과거 데이터는 지운다.
            rows.reverse()
            pathlib.Path(f'_data/주식분봉차트조회요청').mkdir(parents=True, exist_ok=True)
            FileUtil.write_json(f'_data/주식분봉차트조회요청/{code}.json', rows)
            done(code)

        self.kiwoom.opt10080_주식분봉차트조회요청(self.screen, code, 0, downloaded)

    def load_downloaded_file(self, code):
        path = pathlib.Path(f'_data/주식분봉차트조회요청/{code}.json')
        if not path.is_file():
            return None
        return FileUtil.load_json(f'_data/주식분봉차트조회요청/{code}.json')
