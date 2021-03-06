from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class QtUtil:
    @staticmethod
    def copy_to_clipboard(text):
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(text, mode=cb.Clipboard)

    @staticmethod
    def ask_login():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText("로그인 할까요?")
        msg.setWindowTitle("로그인")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg.exec_()
        if retval == QMessageBox.Yes:
            return True
        return False

    @staticmethod
    def find_table_item(table, search, col_idx):
        matching_items = table.findItems(search, Qt.MatchExactly)
        for matching_item in matching_items:
            if matching_item.column() is not col_idx:
                continue
            return matching_item
        return None
