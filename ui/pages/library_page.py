import os
from datetime import datetime
from PyQt6.QtCore import Qt, QSize, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidgetItem, QInputDialog
from qfluentwidgets import (
    ScrollArea, TitleLabel, BodyLabel, SubtitleLabel,
    PrimaryPushButton, PushButton, FluentIcon, InfoBar, CardWidget,
    IndeterminateProgressRing, ListWidget, SearchLineEdit, ComboBox
)

from ui.components import SongCard
from core.data import get_data_manager

QQ_GROUP_URL = "https://qm.qq.com/cgi-bin/qm/qr?k=LcBVvZdH05AILOPso4QSAEM6bbtj3qsI&jump_from=webapi&authKey=Nyna4+DSJGk/+Am6cLzQKsedbyeHUf3MU68Ik+C6nIgz50NEya5lAu+aZi3cM8XT"

TYPE_MAP = {
    "1": "游戏音乐",
    "2": "古典音乐",
    "3": "流行歌曲",
    "4": "影视配乐",
    "5": "民族/国家",
    "0": "其他"
}


class LibraryPage(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LibraryPage")
        self.data_mgr = get_data_manager()
        self.all_songs = []
        self.current_song = None

        # 信号
        self.data_mgr.library_loaded.connect(self.on_library_loaded)
        self.data_mgr.load_failed.connect(self.on_load_failed)
        self.data_mgr.download_finished.connect(self.on_download_finished)

        self.view = QWidget(self)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.view.setObjectName("LibraryView")
        self.setStyleSheet("LibraryPage, QWidget#LibraryView { background: transparent; border: none; }")

        layout = QVBoxLayout(self.view)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        header_layout = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.addWidget(TitleLabel("在线音乐库", self.view))

        search_layout = QHBoxLayout()
        self.search_box = SearchLineEdit(self.view)
        self.search_box.setPlaceholderText("搜索歌曲、歌手...")
        self.search_box.setFixedWidth(200)
        self.search_box.textChanged.connect(lambda: self.filter_library())

        self.combo_type = ComboBox()
        self.combo_type.addItems(["全部类型", "游戏音乐", "古典音乐", "流行歌曲", "影视配乐", "其他"])
        self.combo_type.setFixedWidth(120)
        self.combo_type.currentIndexChanged.connect(lambda: self.filter_library())

        self.combo_sort = ComboBox()
        self.combo_sort.addItems(["默认排序", "最新上传"])
        self.combo_sort.setFixedWidth(120)
        self.combo_sort.currentIndexChanged.connect(lambda: self.filter_library())

        search_layout.addWidget(self.search_box)
        search_layout.addWidget(self.combo_type)
        search_layout.addWidget(self.combo_sort)
        search_layout.addStretch(1)

        header_text.addLayout(search_layout)
        header_layout.addLayout(header_text)
        header_layout.addStretch(1)

        self.btn_refresh = PushButton("刷新列表", self, FluentIcon.SYNC)
        self.btn_refresh.clicked.connect(self.refresh_library)

        self.btn_group = PushButton("进群求音乐", self, FluentIcon.CHAT)
        self.btn_group.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(QQ_GROUP_URL)))

        header_layout.addWidget(self.btn_group)
        header_layout.addWidget(self.btn_refresh)
        layout.addLayout(header_layout)

        # 进度条
        self.loading = IndeterminateProgressRing()
        self.loading.hide()
        layout.addWidget(self.loading, 0, Qt.AlignmentFlag.AlignHCenter)

        # 内容
        content = QHBoxLayout()
        self.list_widget = ListWidget()
        self.list_widget.setStyleSheet(
            "ListWidget{background:transparent; border:none} ListWidget::item{padding:4px}")
        self.list_widget.itemClicked.connect(self.on_item_click)
        content.addWidget(self.list_widget, 4)

        # 详情卡片
        self.info_card = CardWidget()
        info_layout = QVBoxLayout(self.info_card)
        self.lbl_title = SubtitleLabel("请选择曲目")
        self.lbl_desc = BodyLabel("连接到仓库后点击列表查看")
        self.lbl_desc.setWordWrap(True)

        self.btn_add = PrimaryPushButton("下载并收藏", self, FluentIcon.DOWNLOAD)
        self.btn_add.setEnabled(False)
        self.btn_add.clicked.connect(self.download_song)

        info_layout.addWidget(self.lbl_title)
        info_layout.addWidget(self.lbl_desc)
        info_layout.addStretch(1)
        info_layout.addWidget(self.btn_add)

        content.addWidget(self.info_card, 3)
        layout.addLayout(content)

        self.refresh_library()

    def refresh_library(self):
        self.list_widget.clear()
        self.all_songs = []
        self.loading.show()
        self.loading.start()
        self.btn_refresh.setEnabled(False)
        self.lbl_desc.setText("正在加载...")
        self.data_mgr.fetch_library()

    def on_library_loaded(self, library_data):
        self.loading.stop()
        self.loading.hide()
        self.btn_refresh.setEnabled(True)
        self.lbl_desc.setText("加载完成，请选择曲目")
        self.all_songs = library_data
        self.filter_library()

    def filter_library(self):

        self.list_widget.clear()

        search_text = self.search_box.text().lower().strip()
        type_idx = self.combo_type.currentIndex()
        sort_idx = self.combo_sort.currentIndex()

        filtered = []
        for song in self.all_songs:
            title = song.get('title', '未知')
            artist = song.get('artist', '未知')
            desc = song.get('desc', '')
            if search_text and (search_text not in title.lower()) and (search_text not in artist.lower()) and (search_text not in desc.lower()):
                continue

            if type_idx > 0:
                type_ids = ["1", "2", "3", "4", "0"]
                target_id = type_ids[type_idx - 1]
                if song.get('type', '0') != target_id:
                    continue

            filtered.append(song)

        # 排序
        if sort_idx == 1:
            def parse_date(date_str):
                try:
                    parts = date_str.split('-')
                    if len(parts) == 3:
                        return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                except (ValueError, IndexError):
                    pass
                return datetime.min

            filtered.sort(key=lambda x: parse_date(x.get('upload_time', '')), reverse=True)

        # 显示
        for song in filtered:
            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(QSize(0, 70))
            list_item.setData(Qt.ItemDataRole.UserRole, song)
            self.list_widget.setItemWidget(list_item, SongCard(song.get('title', '未知'), song.get('artist', '未知')))

    def on_load_failed(self, msg):
        self.loading.stop()
        self.loading.hide()
        self.btn_refresh.setEnabled(True)
        self.lbl_desc.setText(f"加载失败: {msg}")
        InfoBar.error(title="网络错误", content=msg, parent=self)

    def on_item_click(self, list_item):
        song_data = list_item.data(Qt.ItemDataRole.UserRole)
        self.current_song = song_data

        title = song_data.get('title', '无标题')
        artist = song_data.get('artist', '未知')
        desc = song_data.get('desc', '暂无简介')
        upload_time = song_data.get('upload_time', '未知')
        type_id = song_data.get('type', '0')
        type_str = TYPE_MAP.get(type_id, "其他")

        self.lbl_title.setText(title)

        info_text = (
            f"歌手: {artist}\n"
            f"类型: {type_str}\n"
            f"上传时间: {upload_time}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{desc}"
        )
        self.lbl_desc.setText(info_text)
        if self.data_mgr.is_collected(title):
            self.btn_add.setText("已收藏")
            self.btn_add.setEnabled(False)
        else:
            self.btn_add.setText("下载并收藏")
            self.btn_add.setEnabled(True)

    def download_song(self):
        if not self.current_song: return
        self.btn_add.setEnabled(False)
        self.btn_add.setText("下载中...")
        self.data_mgr.download_midi(self.current_song)

    def on_download_finished(self, success, msg):
        if success:
            self.btn_add.setText("已收藏")
            InfoBar.success(title="完成", content=msg, parent=self)
        else:
            self.btn_add.setText("重试")
            self.btn_add.setEnabled(True)
            InfoBar.error(title="下载失败", content=msg, parent=self)