import json
from urllib import request
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QThread
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    ScrollArea, TitleLabel, BodyLabel, StrongBodyLabel, SubtitleLabel,
    PrimaryPushButton, PushButton, FluentIcon, CardWidget, InfoBar,
    IndeterminateProgressRing
)

VERSION = "1.0.0"
GITHUB_REPO = "naaammme/midido"
QQ_GROUP_URL = "https://qm.qq.com/cgi-bin/qm/qr?k=LcBVvZdH05AILOPso4QSAEM6bbtj3qsI&jump_from=webapi&authKey=Nyna4+DSJGk/+Am6cLzQKsedbyeHUf3MU68Ik+C6nIgz50NEya5lAu+aZi3cM8XT"


class UpdateCheckWorker(QThread):
    finished = pyqtSignal(bool, str)

    def run(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            http_request = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with request.urlopen(http_request, timeout=10) as response:
                release_data = json.loads(response.read().decode('utf-8'))
                latest_version = release_data.get('tag_name', '').lstrip('v')
                if latest_version and self._version_tuple(latest_version) > self._version_tuple(VERSION):
                    self.finished.emit(True, latest_version)
                else:
                    self.finished.emit(False, VERSION)
        except Exception as e:
            self.finished.emit(False, str(e))

    @staticmethod
    def _version_tuple(version_str):
        return tuple(int(x) for x in version_str.split('.'))


class ReleasesLoadWorker(QThread):
    finished = pyqtSignal(list)

    def run(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
            http_request = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with request.urlopen(http_request, timeout=10) as response:
                releases_data = json.loads(response.read().decode('utf-8'))
                self.finished.emit(releases_data[:5])
        except Exception:
            self.finished.emit([])


class AboutPage(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AboutPage")
        self.update_worker = None
        self.releases_worker = None

        self.view = QWidget(self)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setStyleSheet("AboutPage, QWidget { background: transparent; border: none; }")

        main_layout = QHBoxLayout(self.view)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(10)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

        left_layout.addWidget(TitleLabel("关于 MidiDo", self.view))

        version_card = CardWidget()
        version_layout = QVBoxLayout(version_card)
        version_layout.setSpacing(10)

        version_layout.addWidget(StrongBodyLabel("版本信息"))
        version_layout.addWidget(BodyLabel(f"当前版本: v{VERSION}"))

        btn_layout = QHBoxLayout()
        self.btn_check_update = PushButton("检查更新", self, FluentIcon.UPDATE)
        self.btn_check_update.clicked.connect(self.check_update)
        self.btn_github = PushButton("访问 GitHub", self, FluentIcon.GITHUB)
        self.btn_github.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(f"https://github.com/{GITHUB_REPO}")))
        btn_layout.addWidget(self.btn_check_update)
        btn_layout.addWidget(self.btn_github)
        btn_layout.addStretch()
        version_layout.addLayout(btn_layout)

        left_layout.addWidget(version_card)

        intro_card = CardWidget()
        intro_layout = QVBoxLayout(intro_card)
        intro_layout.setSpacing(10)

        intro_layout.addWidget(StrongBodyLabel("软件介绍"))
        intro_txt = BodyLabel(
            "MidiDo 是一款基于 Python 开发的自动演奏辅助工具，旨在帮助玩家在游戏中自动演奏 MIDI 音乐"
        )
        intro_txt.setWordWrap(True)
        intro_layout.addWidget(intro_txt)
        left_layout.addWidget(intro_card)

        intro_card = CardWidget()
        intro_layout = QVBoxLayout(intro_card)
        intro_layout.setSpacing(10)

        intro_layout.addWidget(StrongBodyLabel("使用方法"))
        intro_txt = BodyLabel(
            "选择midi文件后打开游戏窗口，全屏化状态后按f1开始弹奏，再按一次停止演奏"
        )
        intro_txt.setWordWrap(True)
        intro_layout.addWidget(intro_txt)
        left_layout.addWidget(intro_card)


        warn_card = CardWidget()
        warn_layout = QVBoxLayout(warn_card)
        warn_layout.setSpacing(10)

        warn_label = StrongBodyLabel("风险警告与免责声明")
        warn_layout.addWidget(warn_label)

        warn_txt = BodyLabel(
            "1. 本软件仅供编程学习与技术交流使用，严禁用于任何商业用途。\n"
            "2. 软件原理为模拟鼠标输入，有被游戏检测封号的风险。\n"
            "3. 使用本软件造成的账号封禁等后果，由用户自行承担。\n"
            "4. 请勿在游戏内频繁骚扰他人，请勿在游戏内宣传本软件，维护良好的游戏环境。"
        )
        warn_txt.setWordWrap(True)
        warn_layout.addWidget(warn_txt)
        left_layout.addWidget(warn_card)

        left_layout.addStretch()

        self.btn_group = PrimaryPushButton("加入QQ交流群: 924787418", self, FluentIcon.PEOPLE)
        self.btn_group.setFixedSize(240, 30)
        self.btn_group.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(QQ_GROUP_URL)))
        left_layout.addWidget(self.btn_group, 0, Qt.AlignmentFlag.AlignLeft)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.addWidget(SubtitleLabel("更新历史", self.view))
        self.btn_refresh_releases = PushButton("刷新", self, FluentIcon.SYNC)
        self.btn_refresh_releases.clicked.connect(self.load_releases)
        header_layout.addWidget(self.btn_refresh_releases)
        header_layout.addStretch()
        right_layout.addLayout(header_layout)

        self.releases_card = CardWidget()
        releases_layout = QVBoxLayout(self.releases_card)
        releases_layout.setSpacing(10)

        self.loading_releases = IndeterminateProgressRing()
        self.loading_releases.hide()
        releases_layout.addWidget(self.loading_releases, 0, Qt.AlignmentFlag.AlignCenter)

        self.releases_content = QWidget()
        self.releases_content_layout = QVBoxLayout(self.releases_content)
        self.releases_content_layout.setSpacing(15)
        self.releases_content_layout.setContentsMargins(0, 0, 0, 0)
        releases_layout.addWidget(self.releases_content)

        right_layout.addWidget(self.releases_card)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)

        self.load_releases()

    def check_update(self):
        self.btn_check_update.setEnabled(False)
        self.btn_check_update.setText("检查中...")

        self.update_worker = UpdateCheckWorker()
        self.update_worker.finished.connect(self.on_update_checked)
        self.update_worker.start()

    def load_releases(self):
        self.btn_refresh_releases.setEnabled(False)
        self.loading_releases.show()
        self.loading_releases.start()

        while self.releases_content_layout.count():
            child = self.releases_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.releases_worker = ReleasesLoadWorker()
        self.releases_worker.finished.connect(self.on_releases_loaded)
        self.releases_worker.start()

    def on_releases_loaded(self, releases):
        self.loading_releases.stop()
        self.loading_releases.hide()
        self.btn_refresh_releases.setEnabled(True)

        if not releases:
            empty_label = BodyLabel("暂无更新历史或加载失败")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.releases_content_layout.addWidget(empty_label)
            return

        for release in releases:
            release_widget = QWidget()
            release_layout = QVBoxLayout(release_widget)
            release_layout.setSpacing(5)
            release_layout.setContentsMargins(10, 10, 10, 10)

            version_label = StrongBodyLabel(release.get('tag_name', 'Unknown'))
            release_layout.addWidget(version_label)

            date_label = BodyLabel(release.get('published_at', '')[:10])
            date_label.setStyleSheet("color: gray;")
            release_layout.addWidget(date_label)

            body = release.get('body', '暂无描述')
            if len(body) > 200:
                body = body[:200] + "..."
            body_label = BodyLabel(body)
            body_label.setWordWrap(True)
            release_layout.addWidget(body_label)

            self.releases_content_layout.addWidget(release_widget)

        self.releases_content_layout.addStretch()

    def on_update_checked(self, has_update, version_str):
        self.btn_check_update.setEnabled(True)
        self.btn_check_update.setText("检查更新")

        if has_update:
            InfoBar.success(
                title="发现新版本",
                content=f"最新版本: v{version_str}，点击访问 GitHub 下载",
                parent=self
            )
        else:
            if version_str == VERSION:
                InfoBar.info(title="已是最新版本", content=f"当前版本 v{VERSION} 已是最新", parent=self)
            else:
                InfoBar.error(title="检查失败", content=f"无法检查更新: {version_str}", parent=self)