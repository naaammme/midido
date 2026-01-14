import os
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidgetItem, QFileDialog
from qfluentwidgets import (
    ScrollArea, BodyLabel, SubtitleLabel, StrongBodyLabel,
    PrimaryPushButton, PushButton, FluentIcon, CardWidget,
    IndeterminateProgressRing, ListWidget
)

from ui.components import SongCard
from core.data import get_data_manager

class CollectionPage(ScrollArea):
    play_signal = pyqtSignal(str)
    stop_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CollectionPage")
        self.data_mgr = get_data_manager()
        self.data_mgr.favorites_changed.connect(self.refresh)
        self.curr_path = None

        self.view = QWidget(self)
        self.view.setObjectName("CollectionView")
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setStyleSheet("CollectionPage, QWidget#CollectionView { background: transparent; border: none; }")

        layout = QVBoxLayout(self.view)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 播放控制
        self.control_panel = CardWidget()
        cp_layout = QHBoxLayout(self.control_panel)

        info_layout = QVBoxLayout()
        self.lbl_status = SubtitleLabel("就绪")
        self.lbl_song = BodyLabel("未选择曲目")
        self.lbl_song.setStyleSheet("color:gray")
        info_layout.addWidget(self.lbl_status)
        info_layout.addWidget(self.lbl_song)

        self.loading = IndeterminateProgressRing()
        self.loading.hide()
        self.loading.setFixedSize(24, 24)
        self.btn_play = PrimaryPushButton("开始 (F1)", self, FluentIcon.PLAY)
        self.btn_play.clicked.connect(self.req_play)
        self.btn_play.setEnabled(False)
        self.btn_stop = PushButton("停止 (F1)", self, FluentIcon.PAUSE)
        self.btn_stop.clicked.connect(self.req_stop)
        self.btn_stop.setEnabled(False)

        cp_layout.addLayout(info_layout)
        cp_layout.addStretch(1)
        cp_layout.addWidget(self.loading)
        cp_layout.addSpacing(16)
        cp_layout.addWidget(self.btn_play)
        cp_layout.addWidget(self.btn_stop)
        layout.addWidget(self.control_panel)

        # 列表区
        tool_layout = QHBoxLayout()
        tool_layout.addWidget(StrongBodyLabel("收藏列表"))
        tool_layout.addStretch(1)
        self.btn_del = PushButton("删除选中", self, FluentIcon.DELETE)
        self.btn_del.clicked.connect(self.delete_selected)
        self.btn_del.setEnabled(False)
        self.btn_import = PushButton("导入本地", self, FluentIcon.FOLDER)
        self.btn_import.clicked.connect(self.import_midi)

        tool_layout.addWidget(self.btn_del)
        tool_layout.addWidget(self.btn_import)
        layout.addLayout(tool_layout)

        self.list_widget = ListWidget()
        self.list_widget.setStyleSheet("ListWidget{background:transparent; border:none}")
        self.list_widget.itemClicked.connect(self.select_song)
        layout.addWidget(self.list_widget)

        self.refresh()

    def refresh(self):
        self.list_widget.clear()
        for favorite in self.data_mgr.get_favorites():
            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(QSize(0, 60))
            list_item.setData(Qt.ItemDataRole.UserRole, favorite)
            path = favorite['path']
            exists = os.path.exists(path)
            title = favorite['title'] if exists else f"{favorite['title']} (文件丢失)"
            widget = SongCard(title, path)
            if not exists: widget.setStyleSheet("opacity: 0.5; color: red;")
            self.list_widget.setItemWidget(list_item, widget)

    def select_song(self, list_item):
        favorite_data = list_item.data(Qt.ItemDataRole.UserRole)
        self.curr_path = favorite_data['path']
        self.lbl_song.setText(favorite_data['title'])
        self.btn_play.setEnabled(os.path.exists(self.curr_path))
        self.btn_del.setEnabled(True)

    def import_midi(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择MIDI", "", "MIDI (*.mid)")
        if path:
            self.data_mgr.add_favorite(os.path.basename(path), path)

    def delete_selected(self):
        if self.curr_path:
            self.data_mgr.remove_favorite(self.curr_path)
            self.lbl_song.setText("未选择曲目")
            self.curr_path = None
            self.btn_play.setEnabled(False)
            self.btn_del.setEnabled(False)

    def req_play(self):
        if self.curr_path: self.play_signal.emit(self.curr_path)

    def req_stop(self):
        self.stop_signal.emit()

    def update_state(self, is_playing, is_countdown, msg):
        self.lbl_status.setText(msg)
        self.loading.setVisible(is_playing or is_countdown)
        if is_countdown: self.loading.start()
        self.btn_play.setEnabled(not is_playing and not is_countdown)
        self.btn_stop.setEnabled(is_playing or is_countdown)