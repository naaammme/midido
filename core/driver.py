import ctypes
from ctypes import wintypes

# Windows API Constants
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001  # 标记左键按下状态


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class WinInput:
    _user32 = ctypes.windll.user32

    @classmethod
    def screen_size(cls):
        return (
            cls._user32.GetSystemMetrics(0),
            cls._user32.GetSystemMetrics(1)
        )

    @classmethod
    def find_window(cls, title_part: str):
        target_hwnd = None
        found_title = ""

        def callback(hwnd, _):
            nonlocal target_hwnd, found_title
            if not cls._user32.IsWindowVisible(hwnd):
                return True
            length = cls._user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            buff = ctypes.create_unicode_buffer(length + 1)
            cls._user32.GetWindowTextW(hwnd, buff, length + 1)

            if title_part.lower() in buff.value.lower():
                target_hwnd = hwnd
                found_title = buff.value
                return False  # Stop enumeration
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.POINTER(ctypes.c_int))
        cls._user32.EnumWindows(WNDENUMPROC(callback), 0)
        return target_hwnd, found_title

    @classmethod
    def click(cls, hwnd, x, y):
        if not hwnd or not cls._user32.IsWindow(hwnd):
            return

        pt = POINT(int(x), int(y))
        if not cls._user32.ScreenToClient(hwnd, ctypes.byref(pt)):
            return

        lparam = (pt.y << 16) | (pt.x & 0xFFFF)
        cls._user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        cls._user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lparam)