from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QFrame, QLabel
from qfluentwidgets import (
    SettingCard, ComboBox, SpinBox, DoubleSpinBox,
    ColorPickerButton, FluentIcon, StrongBodyLabel, BodyLabel, isDarkTheme
)


class DropdownSettingCard(SettingCard):
    def __init__(self, icon, title, content, texts, parent=None):
        super().__init__(icon, title, content, parent)
        self.comboBox = ComboBox(self)
        self.comboBox.addItems(texts)
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)


class NumberSettingCard(SettingCard):
    def __init__(self, icon, title, content, min_val, max_val, is_double=False, parent=None):
        super().__init__(icon, title, content, parent)
        self.spinBox = DoubleSpinBox(self) if is_double else SpinBox(self)
        self.spinBox.setRange(min_val, max_val)
        self.spinBox.setFixedWidth(120)
        self.hBoxLayout.addWidget(self.spinBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)


class ColorSettingCard(SettingCard):
    def __init__(self, icon, title, content, default_color, parent=None):
        super().__init__(icon, title, content, parent)
        self.colorButton = ColorPickerButton(default_color, title, self)
        self.colorButton.setFixedSize(60, 32)
        self.hBoxLayout.addWidget(self.colorButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)


class SongCard(QFrame):
    def __init__(self, title, artist, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(13, 5, 10, 5)
        layout.setSpacing(10)

        # 内容区域
        icon = StrongBodyLabel()
        icon.setPixmap(FluentIcon.MUSIC.icon().pixmap(20, 20))
        layout.addWidget(icon)
        layout.addWidget(StrongBodyLabel(title, self))
        layout.addStretch(1)
        layout.addWidget(BodyLabel(artist, self))