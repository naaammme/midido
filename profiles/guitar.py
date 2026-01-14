from core.profile_base import BaseProfile


class GuitarProfile(BaseProfile):
    # 我的基准分辨率
    REF_W, REF_H = 2047, 1151

    # 原始坐标数据
    Y_HIGH = 1030
    Y_MID = 900
    Y_LOW = 750

    # 12个半音列的 X 坐标
    X_COORDS = [215, 340, 470, 600, 730, 990, 1120, 1250, 1380, 1520, 1650, 1780]

    def __init__(self):
        super().__init__()
        self._cache = {}
        self._last_size = (0, 0)

    @property
    def name(self):
        return "PC 吉他 (自动缩放)"

    def _remap(self):
        if (self.w, self.h) == self._last_size:
            return

        rx = self.w / self.REF_W
        ry = self.h / self.REF_H

        # Y轴缩放
        cy_high = int(self.Y_HIGH * ry)
        cy_mid = int(self.Y_MID * ry)
        cy_low = int(self.Y_LOW * ry)

        # X轴缩放
        cx_coords = [int(x * rx) for x in self.X_COORDS]

        self._cache.clear()

        # note:
        # MIDI Note < 60 -> 低音 (Y_LOW)
        # 60 <= Note <= 71 -> 中音 (Y_MID)
        # Note > 71 -> 高音 (Y_HIGH)
        # 列索引 = note % 12

        for note in range(0, 128):
            col_idx = note % 12
            if col_idx >= len(cx_coords):
                continue

            x = cx_coords[col_idx]

            if note < 60:
                y = cy_low
            elif 60 <= note <= 71:
                y = cy_mid
            else:
                y = cy_high

            self._cache[note] = (x, y)

        self._last_size = (self.w, self.h)

    def get_pos(self, note):
        self._remap()
        return self._cache.get(note)