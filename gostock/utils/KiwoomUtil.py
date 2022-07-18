from datetime import datetime

import winsound


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
    def ding(frequency=2500, duration=20, repeat=10):
        for i in range(repeat):
            winsound.Beep(frequency, duration)
