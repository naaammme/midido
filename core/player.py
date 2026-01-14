import time
import mido
import ctypes
from PyQt6.QtCore import QThread, pyqtSignal

from core.driver import WinInput
from core.profile_base import BaseProfile


class MidiPlayer(QThread):
    on_progress = pyqtSignal(str)
    on_finished = pyqtSignal()
    on_error = pyqtSignal(str)

    SLEEP_COMPENSATION_MS = 0.015
    BATCH_WINDOW_MS = 0.01

    def __init__(self):
        super().__init__()
        self.hwnd = None
        self.midi_file = None
        self.profile: BaseProfile | None = None
        self.params = {}
        self._active = False
        self._winmm = ctypes.windll.winmm

    def load(self, hwnd, midi_path, profile, speed, pitch, delay):
        self.hwnd = hwnd
        self.midi_file = midi_path
        self.profile = profile
        self.params = {
            'speed': float(speed),
            'pitch': int(pitch),
            'delay': int(delay)
        }

    def stop(self):
        self._active = False

    def run(self):
        self._active = True
        self._winmm.timeBeginPeriod(1)

        try:
            if not self.profile:
                raise ValueError("配置未加载")

            if not self.hwnd:
                raise ValueError("未绑定游戏窗口")

            w, h = WinInput.screen_size()
            self.profile.update_size(w, h)
            self.profile.reset()

            delay = self.params['delay']
            for i in range(delay, 0, -1):
                if not self._active: return
                self.on_progress.emit(f"倒计时 {i}...")
                time.sleep(1)

            if not self._active: return

            self.on_progress.emit("▶ 演奏开始 (后台高精模式)")

            mid = mido.MidiFile(self.midi_file)

            queue = []
            t = 0.0
            pitch_off = self.params['pitch']

            for msg in mid:
                t += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    note = msg.note + pitch_off
                    if self.profile.can_play(note):
                        queue.append((t, note))

            if not queue:
                raise ValueError("没有可演奏的音符")

            t0 = time.perf_counter()
            idx = 0
            speed = self.params['speed']
            total_notes = len(queue)
            MAX_POLYPHONY = 5

            while idx < total_notes and self._active:
                midi_time, _ = queue[idx]
                target = midi_time / speed
                current_perf = time.perf_counter() - t0
                delta = target - current_perf

                if delta <= 0:
                    batch_notes = []
                    temp_idx = idx
                    while temp_idx < total_notes:
                        next_t, next_n = queue[temp_idx]
                        if (next_t / speed) - target < self.BATCH_WINDOW_MS:
                            batch_notes.append(next_n)
                            temp_idx += 1
                        else:
                            break

                    idx = temp_idx

                    final_notes = batch_notes[:MAX_POLYPHONY]

                    for note in final_notes:
                        clicks = self.profile.get_clicks(note)
                        for x, y in clicks:
                            WinInput.click(self.hwnd, x, y)

                elif delta < self.SLEEP_COMPENSATION_MS:
                    pass

                else:
                    time.sleep(delta - self.SLEEP_COMPENSATION_MS)

            self.on_finished.emit()

        except Exception as e:
            self.on_error.emit(str(e))

        finally:
            self._winmm.timeEndPeriod(1)