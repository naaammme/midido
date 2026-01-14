import keyboard
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
from qfluentwidgets import FluentWindow, FluentIcon, InfoBar, NavigationItemPosition

from ui.pages import LibraryPage, CollectionPage, SettingsPage, AboutPage
from core.player import MidiPlayer
from core.driver import WinInput
from profiles.piano import PianoProfile
from profiles.guitar import GuitarProfile
from profiles.harp import HarpProfile


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MidiDo-自动演奏]")
        self.resize(950, 650)
        self.move(self.screen().availableGeometry().center() - self.rect().center())

        # 初始化配置与核心
        self.settings_conf = QSettings("AutoPiano", "UserConfig")
        self.player = MidiPlayer()
        self.player.on_progress.connect(self.on_progress)
        self.player.on_finished.connect(lambda: self.update_status(False, False, "完成"))
        self.player.on_error.connect(lambda e: self.update_status(False, False, f"错误: {e}"))

        # 初始化页面
        self.collection_page = CollectionPage(self)
        self.collection_page.setObjectName("CollectionPage")

        self.library_page = LibraryPage(self)
        self.library_page.setObjectName("LibraryPage")

        self.settings_page = SettingsPage(self)
        self.settings_page.setObjectName("SettingPage")

        # 关于页面
        self.about_page = AboutPage(self)
        self.about_page.setObjectName("AboutPage")

        # 添加侧边栏
        self.addSubInterface(self.library_page, FluentIcon.MUSIC_FOLDER, "音乐库")
        self.addSubInterface(self.collection_page, FluentIcon.HOME, "我的演奏")
        self.addSubInterface(self.settings_page, FluentIcon.SETTING, "设置", NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.about_page, FluentIcon.INFO, "关于", NavigationItemPosition.BOTTOM)

        # 信号
        self.collection_page.play_signal.connect(self.start_play)
        self.collection_page.stop_signal.connect(self.player.stop)
        keyboard.add_hotkey('f1', self.toggle_play)

    def start_play(self, path):
        # 从设置页获取参数
        s_page = self.settings_page
        game = s_page.card_game.comboBox.currentText()
        hwnd, _ = WinInput.find_window(game)

        if not hwnd:
            InfoBar.error(title="错误", content=f"未找到游戏窗口: {game}", parent=self)
            return

        p_idx = s_page.card_profile.comboBox.currentIndex()
        profiles = {0: PianoProfile(), 1: GuitarProfile(), 2: HarpProfile()}
        profile = profiles.get(p_idx, PianoProfile())

        self.player.load(
            hwnd, path, profile,
            s_page.card_speed.spinBox.value(),
            s_page.card_pitch.spinBox.value(),
            s_page.card_delay.spinBox.value()
        )
        self.update_status(False, True, "准备中...")
        self.player.start()

    def toggle_play(self):
        if self.player.isRunning():
            self.player.stop()
        elif self.collection_page.curr_path:
            self.start_play(self.collection_page.curr_path)

    def on_progress(self, msg):
        is_countdown = "倒计时" in msg
        is_playing = "开始" in msg or "演奏" in msg
        self.update_status(is_playing, is_countdown, msg)

    def update_status(self, playing, countdown, msg):
        self.collection_page.update_state(playing, countdown, msg)