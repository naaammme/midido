from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget
from qfluentwidgets import (
    ScrollArea, SettingCardGroup, ExpandLayout, Theme, setTheme, setThemeColor, FluentIcon
)

from ui.components import DropdownSettingCard, NumberSettingCard, ColorSettingCard
from profiles.piano import PianoProfile
from profiles.guitar import GuitarProfile
from profiles.harp import HarpProfile


class SettingsPage(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsPage")
        parent_widget = self.parent()
        self.conf = parent_widget.settings_conf if parent_widget else None

        self.view = QWidget(self)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.view.setObjectName("SettingsView")
        self.setStyleSheet("SettingsPage, QWidget#SettingsView { background: transparent; border: none; }")

        self.layout = ExpandLayout(self.view)

        # 游戏配置
        g_group = SettingCardGroup("配置", self.view)
        self.card_game = DropdownSettingCard(FluentIcon.GAME, "游戏", "", ["明日之后"], g_group)
        self.card_profile = DropdownSettingCard(FluentIcon.MUSIC, "乐器", "",
                                                [p.name for p in [PianoProfile(), GuitarProfile(), HarpProfile()]],
                                                g_group)
        self.card_speed = NumberSettingCard(FluentIcon.SPEED_HIGH, "速度", "", 0.1, 5.0, True, g_group)
        self.card_pitch = NumberSettingCard(FluentIcon.UP, "音调", "", -24, 24, False, g_group)
        self.card_delay = NumberSettingCard(FluentIcon.HISTORY, "延迟", "", 0, 10, False, g_group)
        g_group.addSettingCards([self.card_game, self.card_profile, self.card_speed, self.card_pitch, self.card_delay])
        self.layout.addWidget(g_group)

        # 外观配置
        t_group = SettingCardGroup("外观", self.view)
        self.card_theme = DropdownSettingCard(FluentIcon.BRUSH, "主题", "", ["跟随系统", "浅色", "深色"], t_group)
        self.card_theme.comboBox.currentIndexChanged.connect(self.set_theme)

        default_color = QColor(self.conf.value("theme_color", "#808000")) if self.conf else QColor("#808000")
        setThemeColor(default_color)
        self.card_color = ColorSettingCard(FluentIcon.PALETTE, "主题颜色", "", default_color, t_group)
        self.card_color.colorButton.colorChanged.connect(self.set_theme_color)

        t_group.addSettingCard(self.card_theme) 
        t_group.addSettingCard(self.card_color)
        self.layout.addWidget(t_group)

        # 回显
        if self.conf:
            mode = self.conf.value("theme_mode", "Auto")
            self.card_theme.comboBox.setCurrentIndex(0 if mode == "Auto" else (1 if mode == "Light" else 2))
            self.card_profile.comboBox.setCurrentIndex(int(self.conf.value("profile", 0)))
            self.card_speed.spinBox.setValue(float(self.conf.value("speed", 1.0)))
            self.card_pitch.spinBox.setValue(int(self.conf.value("pitch", 0)))
            self.card_delay.spinBox.setValue(int(self.conf.value("delay", 3)))

        # 信号
        self.card_profile.comboBox.currentIndexChanged.connect(lambda i: self.conf.setValue("profile", i))
        self.card_speed.spinBox.valueChanged.connect(lambda v: self.conf.setValue("speed", v))
        self.card_pitch.spinBox.valueChanged.connect(lambda v: self.conf.setValue("pitch", v))
        self.card_delay.spinBox.valueChanged.connect(lambda v: self.conf.setValue("delay", v))

    def set_theme(self, idx):
        t = [Theme.AUTO, Theme.LIGHT, Theme.DARK][idx]
        setTheme(t)
        self.conf.setValue("theme_mode", ["Auto", "Light", "Dark"][idx])

    def set_theme_color(self, c):
        setThemeColor(c)
        self.conf.setValue("theme_color", c.name())