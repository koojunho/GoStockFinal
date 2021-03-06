import time

from PyQt5.QAxContainer import *

from gostock.utils import *


class MyKiwoom:
    SCREEN_거래량급증요청_실시간열람용 = '2000'
    SCREEN_주식기본정보요청_종목명얻기 = '3000'
    SCREEN_주식틱차트조회요청_틱얻기 = '4000'
    SCREEN_전일대비등락률상위요청_실시간열람용 = '5000'
    SCREEN_주식분봉차트조회요청_분석용 = '6000'

    def __init__(self):
        self.real_fields = FileUtil.load_json('static/real_fields.json')
        self.ocx = QAxWidget('KHOPENAPI.KHOpenAPICtrl.1')
        self.ocx.OnEventConnect.connect(self._on_login)
        self.ocx.OnReceiveTrData.connect(self._on_tr_data)
        self.ocx.OnReceiveConditionVer.connect(self._on_condition_ver)
        self.ocx.OnReceiveTrCondition.connect(self._on_tr_condition)
        self.ocx.OnReceiveRealData.connect(self._on_real_data)
        self.ocx.OnReceiveMsg.connect(self._on_msg)
        self.ocx.OnReceiveChejanData.connect(self._on_chejan_data)
        self.b_login = False

        self.login_callbacks = []
        self.tr_callbacks = {}
        self.real_data_callbacks = []
        self.chejan_data_callbacks = []

        self.order_works = []
        self.gap_order_work = 0.2
        self.last_time_order_work = 0

        self.comm_rq_works = []
        self.gap_comm_rq_work = 4
        self.last_time_comm_rq_work = 0

        self.last_next = None

    ####################################################################################################################

    def add_login_callback(self, callback):
        self.login_callbacks.append(callback)

    def remove_login_callback(self, callback):
        self.login_callbacks.remove(callback)

    def login(self):
        self.ocx.dynamicCall('CommConnect()')

    def _on_login(self, err_code):
        if err_code == 0:
            self.b_login = True
            self.refresh_all_stocks_code_name()
        for cb in self.login_callbacks:
            cb(err_code)

    def is_login(self):
        return self.b_login

    def refresh_all_stocks_code_name(self):
        for market_code in [StockUtil.MARKET_KOSPI, StockUtil.MARKET_KOSDAQ]:
            code_list = list(filter(len, self.GetCodeListByMarket(market_code).split(';')))
            for code in code_list:
                name = self.GetMasterCodeName(code)
                StockUtil.add_stock(market_code, code, name)
        StockUtil.dump_stocks()

    ####################################################################################################################

    def add_real_data_callback(self, callback):
        self.real_data_callbacks.append(callback)

    def remove_real_data_callback(self, callback):
        self.real_data_callbacks.remove(callback)

    def reg_real(self, screen_no, new_code_list):
        code = ';'.join(new_code_list)
        self.ocx.dynamicCall('SetRealReg(QString, QString, QString, QString)', screen_no, code, '10;21', 0)

    def set_real_remove(self, screen_no, code):
        self.ocx.dynamicCall('SetRealRemove(QString, QString)', screen_no, code)

    def unreg_screen_real(self, screen_no):
        self.ocx.dynamicCall('DisConnectRealData(QString)', screen_no)

    def _on_real_data(self, code, real_type, data):
        result = {}
        fields = self.real_fields.get(real_type)
        if fields:
            for key, fid in fields.items():
                result[key] = self.ocx.dynamicCall('GetCommRealData(QString, int)', code, fid)
        else:
            result['data'] = data

        for cb in self.real_data_callbacks:
            cb(code, real_type, result)

    ####################################################################################################################

    def interval(self):
        if len(self.order_works) > 0:
            curr = time.time()
            gap = curr - self.last_time_order_work
            if gap > self.gap_order_work:
                self.last_time_order_work = curr
                call_data = self.order_works.pop(0)
                method = call_data.pop(0)
                method(*call_data)
            # else:
            #     print('거부:', gap, len(self.order_works))
        if len(self.comm_rq_works) > 0:
            curr = time.time()
            gap = curr - self.last_time_comm_rq_work
            if gap >= self.gap_comm_rq_work:
                self.last_time_comm_rq_work = curr
                call_data = self.comm_rq_works.pop(0)
                method = call_data.pop(0)
                method(*call_data)
            # else:
            #     print('거부:', gap, len(self.comm_rq_works))

    ####################################################################################################################

    def OPT10023_거래량급증요청(self, screen, tr_callback):
        def impl(screen, tr_callback):
            # 시장구분 = 000:전체, 001:코스피, 101:코스닥
            self.SetInputValue("시장구분", "000")
            # 정렬구분 = 1:급증량, 2:급증률
            self.SetInputValue("정렬구분", "1")
            # 시간구분 = 1:분, 2:전일
            self.SetInputValue("시간구분", "1")
            # 거래량구분 = 5:5천주이상, 10:만주이상, 50:5만주이상, 100:10만주이상, 200:20만주이상, 300:30만주이상, 500:50만주이상, 1000:백만주이상
            self.SetInputValue("거래량구분", "5")
            # 시간 = 분 입력
            self.SetInputValue("시간", "1")
            # 종목조건 = 0:전체조회, 1:관리종목제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기
            self.SetInputValue("종목조건", "0")
            # 가격구분 = 0:전체조회, 2:5만원이상, 5:1만원이상, 6:5천원이상, 8:1천원이상, 9:10만원이상
            self.SetInputValue("가격구분", "0")
            self.CommRqData("거래량급증요청", "OPT10023", 0, screen)
            self.tr_callbacks[screen] = tr_callback

        self.comm_rq_works.append([impl, screen, tr_callback])

    def opt10027_전일대비등락률상위요청(self, screen, tr_callback, 상하한포함='0', next=0):
        def impl(screen, tr_callback):
            # 시장구분 = 000:전체, 001:코스피, 101:코스닥
            self.SetInputValue("시장구분", "000")

            # 정렬구분 = 1:상승률, 2:상승폭, 3:하락률, 4:하락폭, 5:보합
            self.SetInputValue("정렬구분", "1")

            # 거래량조건 = 0000:전체조회, 0010:만주이상, 0050:5만주이상, 0100:10만주이상, 0150:15만주이상, 0200:20만주이상,
            #               0300:30만주이상, 0500:50만주이상, 1000:백만주이상
            self.SetInputValue("거래량조건", "0000")

            # 종목조건 = 0:전체조회, 1:관리종목제외, 4:우선주+관리주제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기,
            #           8:증30만보기, 9:증20만보기, 11:정리매매종목제외, 12:증50만 보기, 13:증60만 보기, 14:ETF제외, 15:스팩제외,
            #           16:ETF+ETN제외
            self.SetInputValue("종목조건", "16")

            # 신용조건 = 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 5:신용한도초과제외, 8:신용대주, 9:신용융자전체
            self.SetInputValue("신용조건", "0")

            # 상하한포함 = 0:불 포함, 1:포함
            self.SetInputValue("상하한포함", 상하한포함)

            # 가격조건 = 0:전체조회, 1:1천원미만, 2:1천원~2천원, 3:2천원~5천원, 4:5천원~1만원, 5:1만원이상, 8:1천원이상, 10:1만원미만
            self.SetInputValue("가격조건", "0")

            # 거래대금조건 = 0:전체조회, 3:3천만원이상, 5:5천만원이상, 10:1억원이상, 30:3억원이상, 50:5억원이상, 100:10억원이상,
            #               300:30억원이상, 500:50억원이상, 1000:100억원이상, 3000:300억원이상, 5000:500억원이상
            self.SetInputValue("거래대금조건", "0")

            self.CommRqData("전일대비등락률상위요청", "opt10027", next, screen)
            self.tr_callbacks[screen] = tr_callback

        self.comm_rq_works.append([impl, screen, tr_callback])

    def opt10001_주식기본정보요청(self, screen, code, tr_callback):
        def impl(screen, code, tr_callback):
            self.SetInputValue("종목코드", code)
            self.CommRqData("주식기본정보요청", "opt10001", 0, screen)
            self.tr_callbacks[screen] = tr_callback

        self.comm_rq_works.append([impl, screen, code, tr_callback])

    def opt10079_주식틱차트조회요청(self, screen, code, next, tr_callback):
        def impl(screen, code, tr_callback):
            self.SetInputValue("종목코드", code)
            self.SetInputValue("틱범위", "1")
            self.SetInputValue("수정주가구분", "0")
            self.CommRqData("주식틱차트조회요청", "opt10079", next, screen)
            self.tr_callbacks[screen] = tr_callback

        self.comm_rq_works.append([impl, screen, code, tr_callback])

    def opt10080_주식분봉차트조회요청(self, screen, code, next, tr_callback):
        def impl(screen, code, tr_callback):
            self.SetInputValue("종목코드", code)
            self.SetInputValue("틱범위", "1")
            self.SetInputValue("수정주가구분", "0")
            self.CommRqData("주식분봉차트조회요청", "opt10080", next, screen)
            self.tr_callbacks[screen] = tr_callback

        self.comm_rq_works.append([impl, screen, code, tr_callback])

    def SetInputValue(self, id, value):
        """
        TR 입력값을 설정하는 메서드
        :param id: TR INPUT의 아이템명
        :param value: 입력 값
        :return: None
        """
        self.ocx.dynamicCall("SetInputValue(QString, QString)", id, value)

    def CommRqData(self, rqname, trcode, next, screen):
        """
        TR을 서버로 송신합니다.
        :param rqname: 사용자가 임의로 지정할 수 있는 요청 이름
        :param trcode: 요청하는 TR의 코드
        :param next: 0: 처음 조회, 2: 연속 조회
        :param screen: 화면번호 ('0000' 또는 '0' 제외한 숫자값으로 200개로 한정된 값
        :return: None
        """
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen)

    def _on_tr_data(self, screen, rqname, trcode, record, next):
        # print('_on_tr_data', screen, rqname, trcode, record, next)
        self.last_next = next

        fields = self.real_fields.get(rqname)
        if not fields:
            print(f'real_fields.json에 "{rqname}"에 대한 필드 정보가 없습니다.')
            return []

        count = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        if count == 0:
            count = 1

        rows = []
        for row_idx in range(count):
            row = {}
            for fid in fields:
                data = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, row_idx, fid)
                row[fid] = data.strip()
            rows.append(row)

        tr_callback = self.tr_callbacks.get(screen)
        if tr_callback:
            del self.tr_callbacks[screen]
            tr_callback(rows)

    def _on_condition_ver(self, ret, msg):
        print('_on_condition_ver', ret, msg)

    def _on_tr_condition(self, screen_no, code_list, cond_name, cond_index, next):
        print('_on_tr_condition', screen_no, code_list, cond_name, cond_index, next)

    ####################################################################################################################

    def SendOrder(self, rqname, screen, accno, order_type, code, quantity, price, hoga, order_no, tr_callback=None):
        """
        주식 주문을 서버로 전송하는 메서드
        시장가 주문시 주문단가는 0으로 입력해야 함 (가격을 입력하지 않음을 의미)
        :param rqname: 사용자가 임의로 지정할 수 있는 요청 이름
        :param screen: 화면번호 ('0000' 또는 '0' 제외한 숫자값으로 200개로 한정된 값
        :param accno: 계좌번호 10자리
        :param order_type: 1: 신규매수, 2: 신규매도, 3: 매수취소, 4: 매도취소, 5: 매수정정, 6: 매도정정
        :param code: 종목코드
        :param quantity: 주문수량
        :param price: 주문단가
        :param hoga: 00: 지정가, 03: 시장가,
                     05: 조건부지정가, 06: 최유리지정가, 07: 최우선지정가,
                     10: 지정가IOC, 13: 시장가IOC, 16: 최유리IOC,
                     20: 지정가FOK, 23: 시장가FOK, 26: 최유리FOK,
                     61: 장전시간외종가, 62: 시간외단일가, 81: 장후시간외종가
        :param order_no: 원주문번호로 신규 주문시 공백, 정정이나 취소 주문시에는 원주문번호를 입력
        :return:
        """

        def impl(args):
            ret = self.ocx.dynamicCall(
                "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)", args)
            if tr_callback:
                self.tr_callbacks[screen] = tr_callback
            return ret

        self.order_works.append([impl, [rqname, screen, accno, order_type, code, quantity, price, hoga, order_no]])

    def _on_msg(self, screen, rqname, trcode, msg):
        print('_on_msg', screen, '|', rqname, '|', trcode, '|', msg)

    def add_chejan_data_callback(self, callback):
        self.chejan_data_callbacks.append(callback)

    def remove_chejan_data_callback(self, callback):
        self.chejan_data_callbacks.remove(callback)

    def _on_chejan_data(self, gubun, item_cnt, fid_list):
        # print('_on_chejan_data', gubun, item_cnt, fid_list)
        data = {}
        fields = self.real_fields.get('주문체결_잔고수신')
        fid_list = fid_list.split(';')
        for fid in fid_list:
            field = fields.get(fid)
            if not field:
                print('필드없음:', fid)
                continue
            data[field] = self.ocx.dynamicCall("GetChejanData(int)", fid).strip()
        # real data 쪽으로 보낸다
        for cb in self.chejan_data_callbacks:
            cb(gubun, data)

    ####################################################################################################################

    def KOA_Functions_ShowAccountWindow(self):
        self.ocx.dynamicCall("KOA_Functions(QString, QString)", "ShowAccountWindow", "")

    def GetMasterCodeName(self, code):
        if not self.b_login:
            return None
        return self.ocx.dynamicCall("GetMasterCodeName(QString)", code)

    def GetCodeListByMarket(self, market):
        return self.ocx.dynamicCall("GetCodeListByMarket(QString)", market)
