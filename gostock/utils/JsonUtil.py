import json


class JsonUtil:
    @staticmethod
    def stringify(obj):
        return json.dumps(obj, indent=4, ensure_ascii=False)

    @staticmethod
    def parse(json_str):
        return json.loads(json_str)
