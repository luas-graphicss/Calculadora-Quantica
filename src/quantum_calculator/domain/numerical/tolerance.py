from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Tolerance:
    absolute: float
    relative: float

    def bound(self, scale: float) -> float:
        return self.absolute + self.relative * abs(scale)

    def allows(self, error: float, scale: float) -> bool:
        return abs(error) <= self.bound(scale)
