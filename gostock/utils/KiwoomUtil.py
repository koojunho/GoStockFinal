from datetime import datetime


class KiwoomUtil:
    @staticmethod
    def kiwoom_time_2_datetime(kiwoom_time):
        pretty_time = datetime.today().strftime('%Y%m%d') + kiwoom_time
        dt = datetime.strptime(pretty_time, '%Y%m%d%H%M%S')
        return dt

    @staticmethod
    def kiwoom_time_2_timestamp(kiwoom_time):
        ts = KiwoomUtil.datetime_2_timestamp(KiwoomUtil.kiwoom_time_2_datetime(kiwoom_time))
        return ts

    @staticmethod
    def datetime_2_timestamp(dt):
        return datetime.timestamp(dt)

    @staticmethod
    def timestamp_2_datetime(timestamp):
        return datetime.fromtimestamp(timestamp)

    @staticmethod
    def str_2_dt(s_dt):
        return datetime.strptime(s_dt, '%Y-%m-%d %H:%M:%S')

    @staticmethod
    def dt_2_str(dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def ts_2_str(ts):
        return KiwoomUtil.dt_2_str(KiwoomUtil.timestamp_2_datetime(ts))

    @staticmethod
    def str_now_v1():
        return datetime.today().strftime('%Y_%m_%d_%H%M%S')

    @staticmethod
    def is_ban_kwd(keyword):
        for ban_kwd in [
            'ETN', '인버스', 'KODEX', '레버리지', '스팩', '채권', 'TIGER', 'ARIRANG', 'HANARO',
            'KBSTAR', 'KINDEX', 'KOSEF', '액티브', 'SOL', 'TIMEFOLIO', 'TREX', '마이다스', '코스피', '파워 '
        ]:
            if keyword.find(ban_kwd) >= 0:
                return True
        return False

    @staticmethod
    def subscribe(old_code_list, new_code_list):
        left = old_code_list
        right = list(dict.fromkeys(new_code_list))  # 중복 제거

        old_list = list(set(left) - set(right))  # 사라진 코드
        new_list = list(set(right) - set(left))  # 추가된 코드
        result = right  # 최종 코드

        return old_list, result, new_list

    @staticmethod
    def get_hoga_gap(begin_price, end_price, market):
        gaps = [
            {'min': 0, 'unit': 1},
            {'min': 1000, 'unit': 5},
            {'min': 5000, 'unit': 10},
            {'min': 10000, 'unit': 50},
            {'min': 50000, 'unit': 100}
        ]
        if market == '0':
            gaps += [{'min': 100000, 'unit': 500}, {'min': 500000, 'unit': 1000}]
        elif market == '10':
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
