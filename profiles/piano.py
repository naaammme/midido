from core.profile_base import BaseProfile


class PianoProfile(BaseProfile):
    REF_W, REF_H = 2047, 1151
    Y_BLACK, Y_WHITE = 930, 1080

    WHITE_KEYS = [
        20, 60, 100, 135, 180, 215, 255, 295, 335, 375, 415, 450, 495, 535, 575, 615, 650, 690, 730, 770,
        810, 850, 885, 930, 970, 1010, 1045, 1085, 1125, 1165, 1205, 1245, 1285, 1325, 1360, 1400,
        1440, 1480, 1520, 1560, 1600, 1640, 1675, 1720, 1755, 1795, 1835, 1875, 1915, 1950, 1995, 2030
    ]

    BLACK_KEYS = [
        35, 115, 155, 235, 275, 315, 395, 430, 510, 550, 585, 665, 705, 785, 825, 865,
        945, 985, 1065, 1100, 1145, 1220, 1260, 1340, 1375, 1415, 1495, 1535, 1615,
        1655, 1695, 1770, 1815, 1890, 1930, 1970
    ]

    def __init__(self):
        super().__init__()
        self._cache = {}
        self._last_size = (0, 0)

    @property
    def name(self):
        return "PC 标准钢琴 (88键)"

    def _remap(self):
        if (self.w, self.h) == self._last_size:
            return

        rx = self.w / self.REF_W
        ry = self.h / self.REF_H

        cy_black = int(self.Y_BLACK * ry)
        cy_white = int(self.Y_WHITE * ry)

        self._cache.clear()

        b_ptr, w_ptr = 0, 0
        for note in range(21, 109):
            is_black = (note % 12) in {1, 3, 6, 8, 10}

            if is_black:
                if b_ptr < len(self.BLACK_KEYS):
                    x = int(self.BLACK_KEYS[b_ptr] * rx)
                    self._cache[note] = (x, cy_black)
                b_ptr += 1
            else:
                if w_ptr < len(self.WHITE_KEYS):
                    x = int(self.WHITE_KEYS[w_ptr] * rx)
                    self._cache[note] = (x, cy_white)
                w_ptr += 1

        self._last_size = (self.w, self.h)

    def get_pos(self, note):
        self._remap()
        return self._cache.get(note)