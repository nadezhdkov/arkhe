"""
nestifypy.utils
------------
General helper utilities: strings, random, time, math, colors, validation.
"""

from __future__ import annotations

import hashlib
import math
import random as _random
import re
import time
import uuid
from datetime import datetime
from typing import Any, Iterable, List, Optional, Tuple, TypeVar

T = TypeVar("T")


class Strings:
    @staticmethod
    def capitalize_words(text: str) -> str:
        return text.title()

    @staticmethod
    def slugify(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        return re.sub(r"[\s_-]+", "-", text)

    @staticmethod
    def truncate(text: str, max_len: int, suffix: str = "...") -> str:
        if len(text) <= max_len:
            return text
        return text[: max_len - len(suffix)] + suffix

    @staticmethod
    def pad(text: str, width: int, char: str = " ", align: str = "left") -> str:
        if align == "left":
            return text.ljust(width, char)
        elif align == "right":
            return text.rjust(width, char)
        else:
            return text.center(width, char)

    @staticmethod
    def is_empty(text: str) -> bool:
        return not text or not text.strip()

    @staticmethod
    def snake_to_camel(text: str) -> str:
        parts = text.split("_")
        return parts[0] + "".join(p.title() for p in parts[1:])

    @staticmethod
    def camel_to_snake(text: str) -> str:
        s = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s).lower()


class Random:
    @staticmethod
    def uuid() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def int(min_val: int = 0, max_val: int = 100) -> int:
        return _random.randint(min_val, max_val)

    @staticmethod
    def float(min_val: float = 0.0, max_val: float = 1.0) -> float:
        return _random.uniform(min_val, max_val)

    @staticmethod
    def choice(items: List[T]) -> T:
        return _random.choice(items)

    @staticmethod
    def shuffle(items: List[T]) -> List[T]:
        result = list(items)
        _random.shuffle(result)
        return result

    @staticmethod
    def sample(items: List[T], k: int) -> List[T]:
        return _random.sample(items, k)

    @staticmethod
    def seed(value: int) -> None:
        _random.seed(value)


class Time:
    @staticmethod
    def now() -> datetime:
        return datetime.now()

    @staticmethod
    def timestamp() -> float:
        return time.time()

    @staticmethod
    def monotonic() -> float:
        return time.monotonic()

    @staticmethod
    def sleep(seconds: float) -> None:
        time.sleep(seconds)

    @staticmethod
    def format(dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        return (dt or datetime.now()).strftime(fmt)

    @staticmethod
    def elapsed(start: float) -> float:
        return time.monotonic() - start


class Math:
    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(max_val, value))

    @staticmethod
    def lerp(a: float, b: float, t: float) -> float:
        return a + (b - a) * t

    @staticmethod
    def map_range(
        value: float,
        in_min: float,
        in_max: float,
        out_min: float,
        out_max: float,
    ) -> float:
        return out_min + (value - in_min) / (in_max - in_min) * (out_max - out_min)

    @staticmethod
    def distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)

    @staticmethod
    def normalize(value: float, min_val: float, max_val: float) -> float:
        return (value - min_val) / (max_val - min_val)

    @staticmethod
    def degrees(radians: float) -> float:
        return math.degrees(radians)

    @staticmethod
    def radians(degrees: float) -> float:
        return math.radians(degrees)


class Colors:
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)

    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str:
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def lerp(
        c1: Tuple[int, int, int],
        c2: Tuple[int, int, int],
        t: float,
    ) -> Tuple[int, int, int]:
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )


class Validator:
    @staticmethod
    def email(value: str) -> bool:
        return bool(re.match(r"^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$", value))

    @staticmethod
    def url(value: str) -> bool:
        return bool(re.match(r"^https?://[^\s/$.?#].[^\s]*$", value, re.I))

    @staticmethod
    def integer(value: Any) -> bool:
        try:
            int(value)
            return True
        except (TypeError, ValueError):
            return False

    @staticmethod
    def non_empty(value: Any) -> bool:
        if isinstance(value, str):
            return bool(value.strip())
        return value is not None


__all__ = ["Strings", "Random", "Time", "Math", "Colors", "Validator"]
