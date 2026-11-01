from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Point:
    x: float = 0.0
    y: float = 0.0
