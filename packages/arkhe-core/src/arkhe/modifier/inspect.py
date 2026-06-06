"""
arkhe.modifier.inspect
-----------------------
Runtime introspection for ``@modifier``-decorated classes.

``ModifierInspector`` surfaces which visibility modifier is applied to each
field and method, and produces a human-readable summary table — similar in
spirit to ``KomodoInspector`` in the komodo module.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Type


class ModifierInspector:
    """
    Inspect access-modifier metadata on a ``@modifier``-decorated class.

    Usage::

        @modifier
        class Account:
            owner: str
            balance: float = private.field(0.0)

            @private
            def _validate(self): ...

        info = ModifierInspector(Account)
        print(info.visibility_of("balance"))   # "private"
        print(info.private_members)            # {"balance", "_validate"}
        print(info.summary())
    """

    def __init__(self, cls: Type) -> None:
        if not isinstance(cls, type):
            raise TypeError(
                f"ModifierInspector expects a class, got {type(cls).__name__}"
            )
        self._cls = cls
        self._map: Dict[str, str] = getattr(cls, "__arkhe_visibility_map__", {})

    # ── per-member query ─────────────────────────────────────────────────────

    def visibility_of(self, member: str) -> Optional[str]:
        """
        Return the visibility string for *member*, or ``None`` if the member
        is not tracked by the modifier system.

        Returns one of ``"public"``, ``"protected"``, ``"private"``, or ``None``.
        """
        return self._map.get(member)

    # ── member sets ──────────────────────────────────────────────────────────

    @property
    def all_members(self) -> Dict[str, str]:
        """All tracked members and their visibility strings."""
        return dict(self._map)

    @property
    def public_members(self) -> Set[str]:
        """Set of member names with ``public`` visibility."""
        return {k for k, v in self._map.items() if v == "public"}

    @property
    def protected_members(self) -> Set[str]:
        """Set of member names with ``protected`` visibility."""
        return {k for k, v in self._map.items() if v == "protected"}

    @property
    def private_members(self) -> Set[str]:
        """Set of member names with ``private`` visibility."""
        return {k for k, v in self._map.items() if v == "private"}

    # ── decorator detection ──────────────────────────────────────────────────

    @property
    def is_modifier_applied(self) -> bool:
        """True if ``@modifier`` was applied to this class."""
        return getattr(self._cls, "__arkhe_modifier_applied__", False)

    # ── inheritance info ─────────────────────────────────────────────────────

    @property
    def inherited_from(self) -> List[Type]:
        """
        List of base classes that also carry ``@modifier`` instrumentation.
        Useful to understand the full visibility inheritance chain.
        """
        return [
            base for base in self._cls.__mro__[1:]
            if base is not object
            and getattr(base, "__arkhe_modifier_applied__", False)
        ]

    # ── summary ──────────────────────────────────────────────────────────────

    def summary(self) -> str:
        """
        Return a formatted summary table of all members and their visibility.

        Example output::

            ┌────────────────────────────────────────────────────┐
            │  arkhe.modifier  →  BankAccount                    │
            ├────────────────────────────────────────────────────┤
            │  Member             Visibility                      │
            │  ──────────────     ─────────                      │
            │  owner              public                         │
            │  balance            private                        │
            │  _validate          private                        │
            │  _apply             protected                      │
            │  deposit            public                         │
            ├────────────────────────────────────────────────────┤
            │  Inherited from: (none)                            │
            └────────────────────────────────────────────────────┘
        """
        width = 52
        line = "─" * width
        cls_name = self._cls.__name__

        inherited = self.inherited_from
        inherited_str = (
            ", ".join(b.__name__ for b in inherited) if inherited else "(none)"
        )

        # Sort: public first, then protected, then private
        order = {"public": 0, "protected": 1, "private": 2}
        sorted_members = sorted(
            self._map.items(),
            key=lambda kv: (order.get(kv[1], 9), kv[0])
        )

        rows = []
        for name, vis in sorted_members:
            icon = {"public": "🟢", "protected": "🟡", "private": "🔴"}.get(vis, "⚪")
            rows.append(f"│  {name:<20} {icon} {vis:<20}│")

        header = [
            f"┌{line}┐",
            f"│  {'arkhe.modifier  →  ' + cls_name:<{width - 2}}│",
            f"├{line}┤",
            f"│  {'Member':<20} {'Visibility':<22}│",
            f"│  {'──────────────────':<20} {'─────────':<22}│",
        ]
        footer = [
            f"├{line}┤",
            f"│  Inherited from: {inherited_str:<{width - 20}}│",
            f"└{line}┘",
        ]

        return "\n".join(header + rows + footer)

    def __repr__(self) -> str:
        return f"ModifierInspector({self._cls.__name__})"


__all__ = ["ModifierInspector"]
