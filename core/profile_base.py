from abc import ABC, abstractmethod

class BaseProfile(ABC):
    def __init__(self):
        self.w = 0
        self.h = 0

    def update_size(self, w, h):
        self.w = w
        self.h = h

    def reset(self):
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def get_pos(self, note: int) -> tuple[int, int] | None:
        pass

    def can_play(self, note: int) -> bool:
        return self.get_pos(note) is not None

    def get_clicks(self, note: int) -> list[tuple[int, int]]:
        pos = self.get_pos(note)
        return [pos] if pos else []
