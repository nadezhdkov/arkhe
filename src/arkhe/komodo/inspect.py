"""
arkhe.komodo.inspect
-----------------------
Runtime introspection for komodo-decorated classes.

``KomodoInspector`` surfaces which komodo features are active on a class,
lists generated methods, and can produce a human-readable summary —
similar to IntelliJ's ``@Contract`` annotation inspector or the
``@Slf4j`` generated field viewer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Type

_KOMODO_META_ATTR = "__komodo_meta__"


class KomodoInspector:
    """
    Inspect komodo metadata on a class at runtime.

    Usage::

        @komodo.data
        @komodo.builder
        class User:
            name: str
            age: int

        info = KomodoInspector(User)
        print(info.features)        # {'data', 'constructor', 'to_str', 'eq', 'builder'}
        print(info.fields)          # {'name': <class 'str'>, 'age': <class 'int'>}
        print(info.summary())
    """

    def __init__(self, cls: Type) -> None:
        if not isinstance(cls, type):
            raise TypeError(
                f"KomodoInspector expects a class, got {type(cls).__name__}"
            )
        self._cls = cls

    # ── features ─────────────────────────────────────────────────────────────

    @property
    def features(self) -> Set[str]:
        """Set of komodo features applied to this class."""
        return set(getattr(self._cls, _KOMODO_META_ATTR, set()))

    # ── fields ───────────────────────────────────────────────────────────────

    @property
    def fields(self) -> Dict[str, Any]:
        """Annotated fields declared directly on this class."""
        return {
            k: v
            for k, v in getattr(self._cls, "__annotations__", {}).items()
            if not k.startswith("_")
        }

    # ── defaults ─────────────────────────────────────────────────────────────

    @property
    def defaults(self) -> Dict[str, Any]:
        """Fields that have default values defined at the class level."""
        return {
            k: getattr(self._cls, k)
            for k in self.fields
            if hasattr(self._cls, k) and not callable(getattr(self._cls, k))
        }

    # ── generated_methods ────────────────────────────────────────────────────

    @property
    def generated_methods(self) -> List[str]:
        """List of dunder / helper methods added by komodo."""
        known = {
            "__init__", "__repr__", "__str__", "__eq__", "__hash__",
            "__setattr__", "__delattr__", "__new__",
            "copy", "copy_with", "on_change", "off_change",
            "Builder", "builder", "logger",
        }
        return [
            m for m in known
            if m in self._cls.__dict__
        ]

    # ── has_builder ──────────────────────────────────────────────────────────

    @property
    def has_builder(self) -> bool:
        """True if ``@komodo.builder`` was applied."""
        return "builder" in self.features

    # ── is_immutable ─────────────────────────────────────────────────────────

    @property
    def is_immutable(self) -> bool:
        """True if ``@komodo.immutable`` or ``@komodo.value`` was applied."""
        return bool(self.features & {"immutable", "value"})

    # ── is_record ────────────────────────────────────────────────────────────

    @property
    def is_record(self) -> bool:
        """True if ``@komodo.record`` was applied."""
        return "record" in self.features

    # ── contract_info ────────────────────────────────────────────────────────

    def contract_info(self, method_name: str) -> Optional[Dict[str, Any]]:
        """
        Return contract metadata for a method decorated with ``@contract``,
        or ``None`` if the method has no contracts.

        Returns a dict with keys ``preconditions``, ``postconditions``,
        ``invariants``, each a list of ``(predicate, message)`` tuples.
        """
        method = getattr(self._cls, method_name, None)
        if method is None:
            return None
        return getattr(method, "__contracts__", None)

    # ── summary ──────────────────────────────────────────────────────────────

    def summary(self) -> str:
        """
        Return a human-readable summary of komodo metadata on the class.

        Example output::

            ┌─────────────────────────────────────────┐
            │  komodo.inspect  →  User                  │
            ├─────────────────────────────────────────┤
            │  Features   : constructor, data, eq...  │
            │  Fields     : name: str, age: int       │
            │  Defaults   : (none)                    │
            │  Generated  : __init__, __repr__, ...   │
            │  Immutable  : No                        │
            │  Record     : No                        │
            │  Has Builder: Yes                       │
            └─────────────────────────────────────────┘
        """
        cls_name = self._cls.__name__
        features = ", ".join(sorted(self.features)) or "(none)"
        fields_str = ", ".join(
            f"{k}: {v.__name__ if hasattr(v, '__name__') else str(v)}"
            for k, v in self.fields.items()
        ) or "(none)"
        defaults_str = ", ".join(
            f"{k}={v!r}" for k, v in self.defaults.items()
        ) or "(none)"
        methods_str = ", ".join(self.generated_methods) or "(none)"

        width = 50
        line = "─" * width

        def row(label: str, value: str) -> str:
            return f"│  {label:<13}: {value:<{width - 17}}│"

        lines = [
            f"┌{line}┐",
            f"│  {'komodo.inspect  →  ' + cls_name:<{width - 2}}│",
            f"├{line}┤",
            row("Features", features),
            row("Fields", fields_str),
            row("Defaults", defaults_str),
            row("Generated", methods_str),
            row("Immutable", "Yes" if self.is_immutable else "No"),
            row("Record", "Yes" if self.is_record else "No"),
            row("Has Builder", "Yes" if self.has_builder else "No"),
            f"└{line}┘",
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"KomodoInspector({self._cls.__name__})"


__all__ = ["KomodoInspector"]
