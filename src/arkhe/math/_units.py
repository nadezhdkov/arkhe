"""
arkhe.math._units
---------------------
Conversão de unidades: Distance, Weight, Temperature, Duration.

::

    Distance("10km").to("m")    # 10000.0
    Weight("5kg").to("lb")      # 11.023...
    Temperature("32F").to("C")  # 0.0
    Duration("2h 30m").to("s")  # 9000.0
"""

from __future__ import annotations

import re
from typing import Union


# ---------------------------------------------------------------------------
# Distance
# ---------------------------------------------------------------------------

_DISTANCE_TO_METERS = {
    "m": 1.0,
    "meter": 1.0,
    "meters": 1.0,
    "km": 1_000.0,
    "kilometer": 1_000.0,
    "kilometers": 1_000.0,
    "cm": 0.01,
    "centimeter": 0.01,
    "centimeters": 0.01,
    "mm": 0.001,
    "millimeter": 0.001,
    "millimeters": 0.001,
    "mi": 1_609.344,
    "mile": 1_609.344,
    "miles": 1_609.344,
    "ft": 0.3048,
    "foot": 0.3048,
    "feet": 0.3048,
    "in": 0.0254,
    "inch": 0.0254,
    "inches": 0.0254,
    "yd": 0.9144,
    "yard": 0.9144,
    "yards": 0.9144,
    "nm": 1_852.0,          # milha náutica
    "nmi": 1_852.0,
    "nautical mile": 1_852.0,
    "ly": 9.461e15,          # ano-luz
    "light-year": 9.461e15,
    "au": 1.496e11,          # unidade astronômica
}


class Distance:
    """
    Conversão de distâncias.

    ::

        Distance("10km").to("m")    # 10000.0
        Distance("5mi").to("km")    # 8.046...
    """

    def __init__(self, value: Union[str, float], unit: str = "m") -> None:
        if isinstance(value, str):
            val, u = _parse_value_unit(value)
            self._meters = val * _DISTANCE_TO_METERS[u.lower()]
        else:
            self._meters = float(value) * _DISTANCE_TO_METERS[unit.lower()]

    def to(self, unit: str) -> float:
        key = unit.lower()
        if key not in _DISTANCE_TO_METERS:
            raise ValueError(f"Unknown distance unit: {unit!r}")
        return self._meters / _DISTANCE_TO_METERS[key]

    def __repr__(self) -> str:
        return f"Distance({self._meters!r}m)"


# ---------------------------------------------------------------------------
# Weight
# ---------------------------------------------------------------------------

_WEIGHT_TO_KG = {
    "kg": 1.0,
    "kilogram": 1.0,
    "kilograms": 1.0,
    "g": 0.001,
    "gram": 0.001,
    "grams": 0.001,
    "mg": 1e-6,
    "milligram": 1e-6,
    "milligrams": 1e-6,
    "lb": 0.453592,
    "lbs": 0.453592,
    "pound": 0.453592,
    "pounds": 0.453592,
    "oz": 0.0283495,
    "ounce": 0.0283495,
    "ounces": 0.0283495,
    "t": 1_000.0,
    "ton": 1_000.0,
    "tonne": 1_000.0,
    "tonnes": 1_000.0,
    "st": 6.35029,
    "stone": 6.35029,
}


class Weight:
    """
    Conversão de pesos/massas.

    ::

        Weight("5kg").to("lb")  # 11.023...
        Weight("70kg").to("st") # 11.023...
    """

    def __init__(self, value: Union[str, float], unit: str = "kg") -> None:
        if isinstance(value, str):
            val, u = _parse_value_unit(value)
            self._kg = val * _WEIGHT_TO_KG[u.lower()]
        else:
            self._kg = float(value) * _WEIGHT_TO_KG[unit.lower()]

    def to(self, unit: str) -> float:
        key = unit.lower()
        if key not in _WEIGHT_TO_KG:
            raise ValueError(f"Unknown weight unit: {unit!r}")
        return self._kg / _WEIGHT_TO_KG[key]

    def __repr__(self) -> str:
        return f"Weight({self._kg!r}kg)"


# ---------------------------------------------------------------------------
# Temperature
# ---------------------------------------------------------------------------

class Temperature:
    """
    Conversão de temperatura.

    ::

        Temperature("32F").to("C")   # 0.0
        Temperature("100C").to("F")  # 212.0
        Temperature("0K").to("C")    # -273.15
    """

    def __init__(self, value: Union[str, float], unit: str = "C") -> None:
        if isinstance(value, str):
            val, u = _parse_value_unit(value)
            self._celsius = _to_celsius(val, u.upper())
        else:
            self._celsius = _to_celsius(float(value), unit.upper())

    def to(self, unit: str) -> float:
        u = unit.upper()
        if u in ("C", "CELSIUS"):
            return self._celsius
        elif u in ("F", "FAHRENHEIT"):
            return self._celsius * 9 / 5 + 32
        elif u in ("K", "KELVIN"):
            return self._celsius + 273.15
        elif u in ("R", "RANKINE"):
            return (self._celsius + 273.15) * 9 / 5
        else:
            raise ValueError(f"Unknown temperature unit: {unit!r}")

    def __repr__(self) -> str:
        return f"Temperature({self._celsius!r}C)"


def _to_celsius(value: float, unit: str) -> float:
    if unit in ("C", "CELSIUS"):
        return value
    elif unit in ("F", "FAHRENHEIT"):
        return (value - 32) * 5 / 9
    elif unit in ("K", "KELVIN"):
        return value - 273.15
    elif unit in ("R", "RANKINE"):
        return (value - 491.67) * 5 / 9
    raise ValueError(f"Unknown temperature unit: {unit!r}")


# ---------------------------------------------------------------------------
# Duration
# ---------------------------------------------------------------------------

_DURATION_TO_SECONDS = {
    "s": 1.0,
    "sec": 1.0,
    "second": 1.0,
    "seconds": 1.0,
    "ms": 0.001,
    "millisecond": 0.001,
    "milliseconds": 0.001,
    "us": 1e-6,
    "microsecond": 1e-6,
    "microseconds": 1e-6,
    "m": 60.0,
    "min": 60.0,
    "minute": 60.0,
    "minutes": 60.0,
    "h": 3_600.0,
    "hr": 3_600.0,
    "hour": 3_600.0,
    "hours": 3_600.0,
    "d": 86_400.0,
    "day": 86_400.0,
    "days": 86_400.0,
    "w": 604_800.0,
    "week": 604_800.0,
    "weeks": 604_800.0,
}


class Duration:
    """
    Conversão de durações de tempo.
    Aceita formato composto como "2h 30m" ou "1d 4h 30m 15s".

    ::

        Duration("2h 30m").to("s")    # 9000.0
        Duration("1d").to("h")         # 24.0
        Duration(90, "min").to("h")    # 1.5
    """

    def __init__(self, value: Union[str, float], unit: str = "s") -> None:
        if isinstance(value, str):
            self._seconds = _parse_duration(value)
        else:
            self._seconds = float(value) * _DURATION_TO_SECONDS[unit.lower()]

    def to(self, unit: str) -> float:
        key = unit.lower()
        if key not in _DURATION_TO_SECONDS:
            raise ValueError(f"Unknown duration unit: {unit!r}")
        return self._seconds / _DURATION_TO_SECONDS[key]

    def __repr__(self) -> str:
        return f"Duration({self._seconds!r}s)"


def _parse_duration(text: str) -> float:
    """Analisa strings como '2h 30m 15s' e retorna segundos."""
    text = text.strip().lower()
    total = 0.0
    # Tenta cada componente
    pattern = r"([\d.]+)\s*(milliseconds?|microseconds?|ms|us|weeks?|days?|hours?|minutes?|seconds?|hrs?|mins?|secs?|w|d|h|m|s)"
    found = re.findall(pattern, text)
    if found:
        for val_str, unit in found:
            val = float(val_str)
            # Checa a unidade exata primeiro (ex: "ms", "us", "seconds")
            if unit in _DURATION_TO_SECONDS:
                total += val * _DURATION_TO_SECONDS[unit]
            else:
                # Só remove o 's' do plural se a unidade exata não existir na tabela
                # Evita cortar "ms" → "m" ou "us" → "u"
                key = unit.rstrip("s")
                if key in _DURATION_TO_SECONDS:
                    total += val * _DURATION_TO_SECONDS[key]
        return total
    # Fallback: tenta parse simples "valor unidade"
    val, u = _parse_value_unit(text)
    return val * _DURATION_TO_SECONDS[u.lower()]


# ---------------------------------------------------------------------------
# helper genérico
# ---------------------------------------------------------------------------

def _parse_value_unit(text: str) -> tuple[float, str]:
    """Extrai (valor, unidade) de strings como '10km', '5 kg', '32F'."""
    text = text.strip()
    match = re.match(r"^([+-]?[\d.]+(?:[eE][+-]?\d+)?)\s*([a-zA-Z°/]+.*)?$", text)
    if not match:
        raise ValueError(f"Cannot parse value+unit from: {text!r}")
    val = float(match.group(1))
    unit = (match.group(2) or "").strip()
    return val, unit


__all__ = ["Distance", "Weight", "Temperature", "Duration"]