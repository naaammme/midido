import json
import os
import traceback
from urllib import request, error
from urllib.parse import urljoin, quote, urlsplit, urlunsplit
from PyQt6.QtCore import QObject, pyqtSignal, QSettings, QThread

DEFAULT_SOURCE_URL = "https://gitee.com/hualahuala1/midi-collection/raw/master/music_list.json"


class LibraryFetchWorker(QThread):
    success = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        print(f"[DEBUG]正在请求音乐库 URL: {self.url}")
        try:
            http_request = request.Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})

            with request.urlopen(http_request, timeout=10) as response:
                response_content = response.read().decode('utf-8').strip()

                if not response_content:
                    raise ValueError("服务器返回了空内容")
                if response_content.lstrip().startswith("<"):
                    raise ValueError("返回内容看起来像HTML而不是JSON。")

                library_data = json.loads(response_content)

            base_url = self.url.rsplit('/', 1)[0] + '/'
            for song in library_data:
                if not song['file'].startswith('http'):
                    song['file_url'] = urljoin(base_url, song['file'])
                else:
                    song['file_url'] = song['file']

            print(f"[DEBUG] 解析成功，共 {len(library_data)} 首曲目")
            self.success.emit(library_data)

        except Exception as e:
            traceback.print_exc()
            self.failed.emit(f"无法连接音乐库: {str(e)}")


class MidiDownloadWorker(QThread):
    success = pyqtSignal(str, dict)
    failed = pyqtSignal(str)

    def __init__(self, song_data):
        super().__init__()
        self.song_data = song_data

    def run(self):
        title = self.song_data.get('title', '未知')
        print(f"[DEBUG] 开始下载: {title}")
        try:
            download_dir = "downloads"
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)

            filename = f"{title}.mid"
            filename = "".join([c for c in filename if c not in r'<>:"/\|?*']).strip()
            if not filename or filename == '.mid':
                filename = "untitled.mid"
            save_path = os.path.join(os.getcwd(), download_dir, filename)

            url = self.song_data['file_url']
            split_result = urlsplit(url)
            encoded_path = quote(split_result.path, safe='/')
            safe_url = urlunsplit((
                split_result.scheme,
                split_result.netloc,
                encoded_path,
                split_result.query,
                split_result.fragment
            ))

            http_request = request.Request(safe_url, headers={'User-Agent': 'Mozilla/5.0'})
            with request.urlopen(http_request, timeout=15) as response:
                file_content = response.read()
                if file_content.lstrip().startswith(b"<"):
                    raise ValueError("下载内容无效")
                with open(save_path, 'wb') as f:
                    f.write(file_content)

            self.success.emit(save_path, self.song_data)
        except Exception as e:
            traceback.print_exc()
            self.failed.emit(f"下载失败: {str(e)}")


class DataManager(QObject):
    favorites_changed = pyqtSignal()
    library_loaded = pyqtSignal(list) # [data_list]
    load_failed = pyqtSignal(str) # [error_msg]
    download_progress = pyqtSignal(int) #(0-100)
    download_finished = pyqtSignal(bool, str) # [success, msg/path]

    def __init__(self):
        super().__init__()
        self.settings = QSettings("AutoPiano", "UserConfig")
        self._favorites = self._load_favorites()
        self._online_cache = []
        self.fetch_worker = None
        self.download_worker = None

    def _load_favorites(self):
        try:
            return json.loads(self.settings.value("favorites", "[]"))
        except (json.JSONDecodeError, TypeError):
            return []

    def get_favorites(self):
        return self._favorites

    def is_collected(self, title):
        # 这里简单用标题判重
        return any(f['title'] == title for f in self._favorites)

    def add_favorite(self, title, path, artist="未知", type_id="0", upload_time="未知"):

        if self.is_collected(title): return False

        item = {
            "title": title,
            "path": path,
            "artist": artist,
            "type": str(type_id),
            "upload_time": upload_time
        }

        self._favorites.append(item)
        self.settings.setValue("favorites", json.dumps(self._favorites))
        self.favorites_changed.emit()
        return True

    def remove_favorite(self, path):
        self._favorites = [f for f in self._favorites if f['path'] != path]
        self.settings.setValue("favorites", json.dumps(self._favorites))
        self.favorites_changed.emit()

    def fetch_library(self, url=None):
        if not url:
            url = self.settings.value("repo_url", DEFAULT_SOURCE_URL)
            if not url: url = DEFAULT_SOURCE_URL

        self.fetch_worker = LibraryFetchWorker(url)
        self.fetch_worker.success.connect(self._on_library_fetched)
        self.fetch_worker.failed.connect(self.load_failed.emit)
        self.fetch_worker.start()

    def _on_library_fetched(self, library_data):
        self._online_cache = library_data
        self.library_loaded.emit(library_data)

    def download_midi(self, song_data):
        self.download_worker = MidiDownloadWorker(song_data)
        self.download_worker.success.connect(self._on_download_success)
        self.download_worker.failed.connect(lambda msg: self.download_finished.emit(False, msg))
        self.download_worker.start()

    def _on_download_success(self, save_path, song_data):
        title = song_data.get('title', '未知')
        self.add_favorite(
            title=title,
            path=save_path,
            artist=song_data.get('artist', '未知'),
            type_id=song_data.get('type', '0'),
            upload_time=song_data.get('upload_time', '未知')
        )
        self.download_finished.emit(True, f"已下载并收藏: {title}")


_instance = None


def get_data_manager():
    global _instance
    if _instance is None:
        _instance = DataManager()
    return _instance