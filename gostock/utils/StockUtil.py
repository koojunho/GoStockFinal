from datetime import datetime

from gostock.utils import *


class StockUtil:
    MARKET_KOSPI = '0'
    MARKET_KOSDAQ = '10'
    STOCKS_FILENAME = '_data/전체종목.json'
    stock_info = {}

    @staticmethod
    def add_stock(market, code, name):
        StockUtil.stock_info[code] = market, code, name

    @staticmethod
    def dump_stocks(output=None):
        stocks = StockUtil.stock_info
        rows = []
        for code in stocks:
            data = stocks[code]
            market = data[0]
            s_market = '??'
            if market == StockUtil.MARKET_KOSPI:
                s_market = '코스피'
            elif market == StockUtil.MARKET_KOSDAQ:
                s_market = '코스닥'
            name = data[2]
            rows.append({'market': s_market, 'code': code, 'name': name})
        result = {'updated_at': datetime.today().strftime('%Y-%m-%d %H:%M:%S'), 'stocks': rows}

        if not output:
            output = StockUtil.STOCKS_FILENAME

        FileUtil.write_json(output, result)

    @staticmethod
    def get_market(code):
        data = StockUtil.stock_info.get(code)
        if not data:
            return None
        return data[0]

    @staticmethod
    def get_name(code):
        data = StockUtil.stock_info.get(code)
        if not data:
            return None
        return data[2]

    @staticmethod
    def get_hoga_gap(begin_price, end_price, market):
        gaps = [
            {'min': 0, 'unit': 1},
            {'min': 1000, 'unit': 5},
            {'min': 5000, 'unit': 10},
            {'min': 10000, 'unit': 50},
            {'min': 50000, 'unit': 100}
        ]
        if market == StockUtil.MARKET_KOSPI:
            gaps += [{'min': 100000, 'unit': 500}, {'min': 500000, 'unit': 1000}]
        elif market == StockUtil.MARKET_KOSDAQ:
            pass
        else:
            raise Exception(f'알 수 없는 마켓: {market}')

        if begin_price < end_price:
            sign = 1
            temp_begin_price = begin_price
            temp_end_price = end_price
        else:
            sign = -1
            temp_begin_price = end_price
            temp_end_price = begin_price

        begin_gap_idx = -1
        end_gap_idx = -1
        for idx, gap in enumerate(gaps):
            if gap['min'] <= temp_begin_price:
                begin_gap_idx = idx
            if gap['min'] <= temp_end_price:
                end_gap_idx = idx

        n_gap = 0
        for idx in range(begin_gap_idx, end_gap_idx + 1):
            unit = gaps[idx]['unit']
            if idx == begin_gap_idx:
                left = temp_begin_price
            else:
                left = gaps[idx]['min']
            if idx == end_gap_idx:
                right = temp_end_price
            else:
                right = gaps[idx + 1]['min']
            n_gap += int((right - left) / unit)
        n_gap = sign * n_gap

        return n_gap
