from PyQt5.QtWidgets import *


class QtUtil:
    @staticmethod
    def copy_to_clipboard(text):
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(text, mode=cb.Clipboard)
