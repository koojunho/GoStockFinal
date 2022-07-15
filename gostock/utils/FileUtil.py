from gostock.utils.JsonUtil import JsonUtil


class FileUtil:
    @staticmethod
    def load_json(file_name):
        content = FileUtil.load_file(file_name)
        obj = JsonUtil.parse(content)
        return obj

    @staticmethod
    def write_json(file_name, data):
        content = JsonUtil.stringify(data)
        FileUtil.write_file(file_name, content)

    @staticmethod
    def load_file(file_name):
        f = open(file_name, "r", encoding="utf-8")
        content = f.read()
        f.close()
        return content

    @staticmethod
    def write_file(file_name, content):
        f = open(file_name, "w", encoding="utf-8")
        f.write(content)
        f.close()
