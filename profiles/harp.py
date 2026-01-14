from core.profile_base import BaseProfile


class HarpProfile(BaseProfile):

    REF_W, REF_H = 2047, 1151

    Y_SHARP = 45
    Y_NAT = 110
    Y_FLAT = 170

    PEDAL_XS = [695, 815, 940, 1100, 1220, 1340, 1465]  # C D E F G A B
    STRING_Y = 910

    BASE_NOTE = 24  # 第1弦 MIDI码
    SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]  # 大调自然音阶

    STRING_XS = [
        155, 190, 230, 265, 305, 340, 380, 420, 460, 495, 535, 570, 610, 645, 685, 725, 760,
        800, 840, 875, 915, 950, 990, 1030, 1065, 1105, 1140, 1175, 1215, 1255, 1290, 1330,
        1370, 1405, 1445, 1480, 1520, 1560, 1595, 1635, 1670, 1710, 1750, 1790, 1825, 1860, 1900
    ]  # 47根

    def __init__(self):
        super().__init__()
        self._last_size = (0, 0)

        self._rx = 1.0
        self._ry = 1.0

        self._pedal_x_scaled = []
        self._y_sharp_scaled = 0
        self._y_nat_scaled = 0
        self._y_flat_scaled = 0

        self._string_x_scaled = []
        self._string_y_scaled = 0

        # 记录当前踏板状态：0=♮, 1=#, -1=b
        self.current_pedal_states = {k: 0 for k in range(7)}

    @property
    def name(self):
        return "PC 竖琴 (含踏板47键)"

    def reset(self):
        # 每次播放开始前重置踏板状态
        self.current_pedal_states = {k: 0 for k in range(7)}

    def _remap(self):
        if (self.w, self.h) == self._last_size:
            return

        self._rx = self.w / self.REF_W
        self._ry = self.h / self.REF_H

        self._pedal_x_scaled = [int(x * self._rx) for x in self.PEDAL_XS]
        self._y_sharp_scaled = int(self.Y_SHARP * self._ry)
        self._y_nat_scaled = int(self.Y_NAT * self._ry)
        self._y_flat_scaled = int(self.Y_FLAT * self._ry)

        self._string_x_scaled = [int(x * self._rx) for x in self.STRING_XS]
        self._string_y_scaled = int(self.STRING_Y * self._ry)

        self._last_size = (self.w, self.h)

    def _pedal_pos(self, diatonic_idx: int, state: int) -> tuple[int, int]:
        # state: 1(#), 0(♮), -1(b)
        x = self._pedal_x_scaled[diatonic_idx]
        if state == 1:
            y = self._y_sharp_scaled
        elif state == 0:
            y = self._y_nat_scaled
        else:
            y = self._y_flat_scaled
        return x, y

    def can_play(self, note: int) -> bool:
        """算法:不改变踏板状态的前提下，判断这个音符是否能被某根弦覆盖"""
        self._remap()
        for s_idx in range(len(self._string_x_scaled)):
            diatonic_idx = s_idx % 7
            octave = s_idx // 7
            natural_pitch = self.BASE_NOTE + (octave * 12) + self.SCALE_INTERVALS[diatonic_idx]
            diff = note - natural_pitch
            if diff in (-1, 0, 1):
                return True
        return False

    def get_pos(self, note: int):
        return None

    def get_clicks(self, note: int) -> list[tuple[int, int]]:
        self._remap()

        best_string_idx = -1
        required_state = 0
        pedal_note_idx = 0
        found = False

        for s_idx in range(len(self._string_x_scaled)):
            diatonic_idx = s_idx % 7
            octave = s_idx // 7
            natural_pitch = self.BASE_NOTE + (octave * 12) + self.SCALE_INTERVALS[diatonic_idx]
            diff = note - natural_pitch

            if diff in (-1, 0, 1):
                if not found:
                    best_string_idx = s_idx
                    required_state = diff
                    pedal_note_idx = diatonic_idx
                    found = True

                cur_state = self.current_pedal_states[diatonic_idx]
                if cur_state == diff:
                    best_string_idx = s_idx
                    required_state = diff
                    pedal_note_idx = diatonic_idx
                    break

        if not found:
            return []

        clicks: list[tuple[int, int]] = []

        # 先踩踏板
        if self.current_pedal_states[pedal_note_idx] != required_state:
            clicks.append(self._pedal_pos(pedal_note_idx, required_state))
            self.current_pedal_states[pedal_note_idx] = required_state

        # 再弹弦
        sx = self._string_x_scaled[best_string_idx]
        clicks.append((sx, self._string_y_scaled))
        return clicks
