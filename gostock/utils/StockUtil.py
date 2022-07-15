class StockUtil:
    MARKET_KOSPI = '0'
    MARKET_KOSDAQ = '10'
    stock_info = {}

    @staticmethod
    def add_stock(market, code, name):
        StockUtil.stock_info[code] = market, code, name

    @staticmethod
    def get_market(code):
        return StockUtil.stock_info[code][0]
