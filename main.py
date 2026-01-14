import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

if __name__ == '__main__':
    # 针对高分屏的缩放优化
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    window = MainWindow()
    window.showNormal()

    sys.exit(app.exec())