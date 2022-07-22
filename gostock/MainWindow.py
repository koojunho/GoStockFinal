from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gostock.apps.default.LoginWidget import LoginWidget
from gostock.kiwoom.Kiwoom import MyKiwoom


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("9Cells", "GoStock")
        if self.settings.value("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.value("windowState"):
            self.restoreState(self.settings.value("windowState"))
        self.always_on_top = False
        aot = self.settings.value("alwaysOnTop")
        if aot and aot == 'true':
            self.always_on_top = True

        # 윈도우

        self.setWindowTitle('GoStock Final')
        if self.always_on_top:
            self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.kiwoom = MyKiwoom()

        # 위젯

        self.curr_widget = self.login_widget = LoginWidget(self.kiwoom)

        # 메뉴

        bar = self.menuBar()

        file_menu = bar.addMenu("파일(&F)")
        apps_menu = bar.addMenu("앱(&A)")
        window_menu = bar.addMenu("창(&W)")

        action = file_menu.addAction("로그인(&L)")
        action.setShortcut(QKeySequence("Ctrl+L"))
        action.triggered.connect(self.login_widget.will_login)

        action = apps_menu.addAction("기간내 상승 잡기 (&1)")
        action.setShortcut(QKeySequence("Ctrl+1"))
        self.real_widget = None
        action.triggered.connect(self.show_two_percent_widget)

        action = apps_menu.addAction("기간내 상승 테스트 (&2)")
        action.setShortcut(QKeySequence("Ctrl+2"))
        self.check_widget = None
        action.triggered.connect(self.show_check_two_in_five_widget)

        action = window_menu.addAction("Always on top")
        action.setShortcut(QKeySequence("Ctrl+T"))
        action.setCheckable(True)
        if self.always_on_top:
            action.setChecked(True)
        action.triggered.connect(self.always_on_top_menu_selected)

        self.kiwoom_timer = QTimer()
        self.kiwoom_timer.setInterval(100)
        self.kiwoom_timer.timeout.connect(self.kiwoom_timer_handler)
        self.kiwoom_timer.start()

        self.show_login_widget()

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("alwaysOnTop", self.always_on_top)
        QMainWindow.closeEvent(self, event)

    def kiwoom_timer_handler(self):
        self.kiwoom.interval()

    def show_login_widget(self):
        self.show_new_widget(self.login_widget)

    def show_two_percent_widget(self):
        if not self.real_widget:
            from gostock.apps.two_percent_up.Widget import Widget
            self.real_widget = Widget(self.kiwoom)

        if not self.show_new_widget(self.real_widget):
            self.show_login_widget()

    def show_check_two_in_five_widget(self):
        if not self.check_widget:
            from gostock.apps.check_two_in_five.Widget import Widget
            self.check_widget = Widget(self.kiwoom)

        self.show_new_widget(self.check_widget)

    def show_new_widget(self, new_widget):
        if new_widget.enter():
            self.curr_widget.leave()
            self.takeCentralWidget()
            self.setCentralWidget(new_widget)
            self.curr_widget = new_widget
            return True
        else:
            return False

    def always_on_top_menu_selected(self, action):
        self.always_on_top = action
        # https://stackoverflow.com/a/33025835 flags 변경 후에 윈도우가 감쳐지는데 show()를 호출하라고 한다.
        if self.always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.show()
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.show()
