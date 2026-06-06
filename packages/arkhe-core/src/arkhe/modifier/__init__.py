"""
arkhe.modifier
--------------
Java-style access modifiers (``private``, ``protected``, ``public``) for
Python classes — enforced at runtime via descriptors and call-stack inspection.

Eliminates the "all attributes are public" limitation of Python by raising
``PrivateAccessError`` / ``ProtectedAccessError`` when code outside the
permitted scope tries to read or write a guarded member.

Visibility rules
~~~~~~~~~~~~~~~~
=========  =====================================================================
Modifier   Who may access
=========  =====================================================================
public     Everyone (Python default — explicit annotation is optional)
protected  The declaring class **and** any of its subclasses
private    **Only** the declaring class (subclasses are denied, as in Java)
=========  =====================================================================

Quick start
~~~~~~~~~~~
    from arkhe.modifier import modifier, private, protected, public

    @modifier
    class BankAccount:
        owner:   str            # public (default)
        balance: float = private.field(0.0)

        @private
        def _validate(self, amount: float) -> None:
            if amount <= 0:
                raise ValueError("amount must be positive")

        @protected
        def _apply(self, amount: float) -> None:
            self._validate(amount)   # OK — same class
            self.balance += amount

        def deposit(self, amount: float) -> None:
            self._apply(amount)      # OK — owner or subclass

    account = BankAccount(owner="Alice")
    account.deposit(100.0)    # OK
    account.balance           # PrivateAccessError — outside the class

Field markers
~~~~~~~~~~~~~
    balance: float = private.field(0.0)     # private with default
    tag:     str   = protected.field()      # protected, no default
    name:    str   = public.field("anon")   # public with default

Method markers
~~~~~~~~~~~~~~
    @private
    def _internal(self): ...

    @protected
    def _shared_with_subclasses(self): ...

Introspection
~~~~~~~~~~~~~
    from arkhe.modifier import ModifierInspector
    info = ModifierInspector(BankAccount)
    print(info.summary())
    print(info.visibility_of("balance"))   # "private"
"""

from arkhe.modifier.core import modifier, private, protected, public
from arkhe.modifier.exceptions import (
    AccessViolationError,
    PrivateAccessError,
    ProtectedAccessError,
)
from arkhe.modifier.inspect import ModifierInspector

__all__ = [
    # Decorators
    "modifier",
    "private",
    "protected",
    "public",
    # Errors
    "AccessViolationError",
    "PrivateAccessError",
    "ProtectedAccessError",
    # Introspection
    "ModifierInspector",
]

__version__ = "0.1.0"
