import time

from PyQt5.QAxContainer import *

from gostock.utils import *


class ScreenNoManager:
    def __init__(self):
        self.screen_no__stock_codes = {}
        self.stock_code__screen_no = {}

    def get_screen_no_list(self):
        return list(self.screen_no__stock_codes.keys())

    def get_available_screen_no(self):
        curr_screen_no = 1000
        while True:
            screen_no = str(curr_screen_no)
            curr_list = self.screen_no__stock_codes.get(screen_no)
            if not curr_list:
                return screen_no
            elif len(curr_list) < 100:
                return screen_no
            else:
                curr_screen_no += 1

    def register_stock_code(self, stock_code):
        screen_no = self.stock_code__screen_no.get(stock_code)
        if screen_no:
            raise Exception('이미 등록된 stock_code:', stock_code)

        screen_no = self.get_available_screen_no()

        self.stock_code__screen_no[stock_code] = screen_no

        if not self.screen_no__stock_codes.get(screen_no):
            self.screen_no__stock_codes[screen_no] = []
        self.screen_no__stock_codes[screen_no].append(stock_code)

        return screen_no

    def unregister_stock_code(self, stock_code):
        screen_no = self.stock_code__screen_no.get(stock_code)
        if not screen_no:
            raise Exception('등록되지 않은 stock_code:', stock_code)

        del self.stock_code__screen_no[stock_code]

        self.screen_no__stock_codes[screen_no].remove(stock_code)

        return screen_no

    def unregister_all(self):
        self.screen_no__stock_codes = {}
        self.stock_code__screen_no = {}


class MyKiwoom:
    SCREEN_거래량급증요청_실시간열람용 = '2000'
    SCREEN_주식기본정보요청_종목명얻기 = '3000'
    SCREEN_주식틱차트조회요청_틱얻기 = '4000'
    SCREEN_전일대비등락률상위요청_실시간열람용 = '5000'

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

        self.screen_no_manager = ScreenNoManager()

        self.login_callbacks = []
        self.tr_callbacks = {}
        self.real_data_callbacks = []
        self.chejan_data_callbacks = []

        self.order_works = []
        self.last_time_order_work = 0

        self.comm_rq_works = []
        self.last_time_comm_rq_work = 0

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
        for cb in self.login_callbacks:
            cb(err_code)

    ####################################################################################################################

    def add_real_data_callback(self, callback):
        self.real_data_callbacks.append(callback)

    def remove_real_data_callback(self, callback):
        self.real_data_callbacks.remove(callback)

    def reg_real(self, old_code_list, existing_code_list, new_code_list):
        real_type = 0
        if len(existing_code_list) > 0:
            real_type = 1

        if len(new_code_list) > 0:
            hoga_fids = '21;50;70;49;69;48;68;47;67;46;66;45;65;44;64;43;63;42;62;41;61;51;71;52;72;53;73;54;74;55;75;56;76;57;77;58;78;59;79;60;80;216'
            for code in new_code_list:
                screen_no = self.screen_no_manager.register_stock_code(code)
                self.ocx.dynamicCall(
                    'SetRealReg(QString, QString, QString, QString)', screen_no, code, '10;' + hoga_fids, real_type)
                real_type = 1
            # FileUtil.write_json('_data/screen.json', self.screen_no_manager.screen_no__stock_codes)

        for code in old_code_list:
            screen_no = self.screen_no_manager.unregister_stock_code(code)
            self.ocx.dynamicCall('SetRealRemove(QString, QString)', screen_no, code)

    def unreg_real(self):
        screen_no_list = self.screen_no_manager.get_screen_no_list()
        for screen_no in screen_no_list:
            print('scree_no 삭제:', screen_no)
            self.ocx.dynamicCall('DisConnectRealData(QString)', screen_no)
        self.screen_no_manager.unregister_all()

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
            if gap > 0.2:
                self.last_time_order_work = curr
                call_data = self.order_works.pop(0)
                method = call_data.pop(0)
                method(*call_data)
            # else:
            #     print('거부:', gap, len(self.order_works))
        if len(self.comm_rq_works) > 0:
            curr = time.time()
            gap = curr - self.last_time_comm_rq_work
            if gap >= 4:
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

    def opt10027_전일대비등락률상위요청(self, screen, tr_callback):
        def impl(screen, tr_callback):
            # 시장구분 = 000:전체, 001:코스피, 101:코스닥
            self.SetInputValue("시장구분", "000")
            # 정렬구분 = 1:상승률, 2:상승폭, 3:하락률, 4:하락폭, 5:보합
            self.SetInputValue("정렬구분", "1")
            # 거래량조건 = 0000:전체조회, 0010:만주이상, 0050:5만주이상, 0100:10만주이상, 0150:15만주이상, 0200:20만주이상, 0300:30만주이상, 0500:50만주이상, 1000:백만주이상
            self.SetInputValue("거래량조건", "0000")
            # 종목조건 = 0:전체조회, 1:관리종목제외, 4:우선주+관리주제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기, 11:정리매매종목제외, 12:증50만 보기, 13:증60만 보기, 14:ETF제외, 15:스팩제외, 16:ETF+ETN제외
            self.SetInputValue("종목조건", "16")
            # 신용조건 = 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 5:신용한도초과제외, 8:신용대주, 9:신용융자전체
            self.SetInputValue("신용조건", "0")
            # 상하한포함 = 0:불 포함, 1:포함
            self.SetInputValue("상하한포함", "0")
            # 가격조건 = 0:전체조회, 1:1천원미만, 2:1천원~2천원, 3:2천원~5천원, 4:5천원~1만원, 5:1만원이상, 8:1천원이상, 10:1만원미만
            self.SetInputValue("가격조건", "0")
            # 거래대금조건 = 0:전체조회, 3:3천만원이상, 5:5천만원이상, 10:1억원이상, 30:3억원이상, 50:5억원이상, 100:10억원이상, 300:30억원이상, 500:50억원이상, 1000:100억원이상, 3000:300억원이상, 5000:500억원이상
            self.SetInputValue("거래대금조건", "0")
            self.CommRqData("전일대비등락률상위요청", "opt10027", 0, screen)
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
        fields = self.real_fields.get(rqname)
        if not fields:
            print('real_fields.json에 필드 정보가 없습니다.')
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
        print('_on_chejan_data', gubun, item_cnt, fid_list)
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
