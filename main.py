import sys

import matplotlib
from PyQt5.QtWidgets import *

from gostock.windows.MainWindow import MainWindow

matplotlib.use('Qt5Agg')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
