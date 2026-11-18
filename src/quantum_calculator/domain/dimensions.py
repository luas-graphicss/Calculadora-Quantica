from dataclasses import dataclass, replace
from typing import Self


@dataclass(frozen=True, slots=True)
class Dimension:
    mass: int = 0
    length: int = 0
    time: int = 0

    def __mul__(self, other: Self) -> Self:
        return replace(
            self,
            mass=self.mass + other.mass,
            length=self.length + other.length,
            time=self.time + other.time,
        )

    def __truediv__(self, other: Self) -> Self:
        return replace(
            self,
            mass=self.mass - other.mass,
            length=self.length - other.length,
            time=self.time - other.time,
        )

    def __pow__(self, exponent: int) -> Self:
        return replace(
            self,
            mass=self.mass * exponent,
            length=self.length * exponent,
            time=self.time * exponent,
        )

    def base_si_unit(self) -> str:
        factors = [
            symbol if exponent == 1 else f"{symbol}^{exponent}"
            for symbol, exponent in (("kg", self.mass), ("m", self.length), ("s", self.time))
            if exponent != 0
        ]
        return " ".join(factors) if factors else "1"


MASS = Dimension(mass=1)
LENGTH = Dimension(length=1)
TIME = Dimension(time=1)
ENERGY = MASS * LENGTH**2 / TIME**2
ACTION = ENERGY * TIME
