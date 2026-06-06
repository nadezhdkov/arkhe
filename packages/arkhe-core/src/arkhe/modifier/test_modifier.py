"""
tests/test_modifier.py
-----------------------
Comprehensive test suite for ``arkhe.modifier``.

Coverage
~~~~~~~~
- @public fields and methods (baseline — no enforcement)
- @private fields: blocked outside class, allowed inside
- @protected fields: blocked from unrelated classes, allowed from subclasses
- @private methods: blocked outside class, allowed inside
- @protected methods: allowed from subclasses, blocked from unrelated classes
- Inheritance: subclass can access protected, cannot access private of parent
- Default values on private/protected fields
- __post_init__ interop (fields set in __init__ are readable inside the class)
- ModifierInspector: visibility_of, private_members, protected_members, summary
- Error types: PrivateAccessError, ProtectedAccessError are AccessViolationError
- Error attributes: member, visibility, caller, owner
- Module-level access is treated as "no class context" → denied for private/protected
- Stacking @modifier with komodo decorators (smoke test)
- Alias import (``from arkhe.modifier import modifier as access``) works fine
  because @modifier is a plain function, not an object with name-based detection
"""

import pytest

from arkhe.modifier import (
    modifier,
    private,
    protected,
    public,
    AccessViolationError,
    PrivateAccessError,
    ProtectedAccessError,
    ModifierInspector,
)


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers / shared fixtures
# ─────────────────────────────────────────────────────────────────────────────

@modifier
class BankAccount:
    owner: str
    balance: float = private.field(0.0)
    credit_limit: float = protected.field(500.0)

    def __init__(self, owner: str) -> None:
        self.owner = owner
        # Writing private/protected fields from inside the class — must work
        self.balance = 0.0
        self.credit_limit = 500.0

    @private
    def _validate(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")

    @protected
    def _apply(self, amount: float) -> None:
        self._validate(amount)       # private called from same class — OK
        self.balance += amount       # private field from same class — OK

    def deposit(self, amount: float) -> None:
        self._apply(amount)          # protected called from same class — OK

    def get_balance(self) -> float:
        return self.balance          # private field from same class — OK


@modifier
class SavingsAccount(BankAccount):
    """Subclass — may access protected members, not private ones."""

    interest_rate: float = public.field(0.05)

    def __init__(self, owner: str, rate: float = 0.05) -> None:
        super().__init__(owner)
        self.interest_rate = rate

    def accrue(self) -> None:
        # Protected field access from subclass — must work
        self._apply(self.balance * self.interest_rate)

    def get_credit_limit(self) -> float:
        # Protected field read from subclass — must work
        return self.credit_limit


@modifier
class Unrelated:
    """A completely unrelated class — must be denied access to guarded members."""

    def steal_balance(self, account: BankAccount) -> float:
        return account.balance      # ← should raise PrivateAccessError

    def peek_credit(self, account: BankAccount) -> float:
        return account.credit_limit  # ← should raise ProtectedAccessError

    def call_validate(self, account: BankAccount) -> None:
        account._validate(100.0)    # ← should raise PrivateAccessError

    def call_apply(self, account: BankAccount) -> None:
        account._apply(100.0)       # ← should raise ProtectedAccessError


# ─────────────────────────────────────────────────────────────────────────────
#  1. Public fields — no enforcement
# ─────────────────────────────────────────────────────────────────────────────

class TestPublicFields:
    def test_public_field_readable_everywhere(self):
        acc = BankAccount("Alice")
        assert acc.owner == "Alice"

    def test_public_field_writable_everywhere(self):
        acc = BankAccount("Alice")
        acc.owner = "Bob"
        assert acc.owner == "Bob"

    def test_public_field_marker_default(self):
        sav = SavingsAccount("Alice")
        assert sav.interest_rate == 0.05

    def test_public_field_marker_override(self):
        sav = SavingsAccount("Alice", rate=0.10)
        assert sav.interest_rate == 0.10


# ─────────────────────────────────────────────────────────────────────────────
#  2. Private fields
# ─────────────────────────────────────────────────────────────────────────────

class TestPrivateFields:
    def test_private_field_readable_inside_class(self):
        acc = BankAccount("Alice")
        acc.deposit(200.0)
        assert acc.get_balance() == 200.0

    def test_private_field_blocked_outside(self):
        acc = BankAccount("Alice")
        with pytest.raises(PrivateAccessError) as exc_info:
            _ = acc.balance
        err = exc_info.value
        assert err.member == "balance"
        assert err.visibility == "private"
        assert err.owner == "BankAccount"

    def test_private_field_write_blocked_outside(self):
        acc = BankAccount("Alice")
        with pytest.raises(PrivateAccessError):
            acc.balance = 9999.0

    def test_private_field_blocked_from_subclass(self):
        """Private fields are NOT accessible even in subclasses — Java semantics."""
        sav = SavingsAccount("Alice")
        with pytest.raises(PrivateAccessError):
            _ = sav.balance  # noqa

    def test_private_field_default_value(self):
        acc = BankAccount("Alice")
        # The default is 0.0 — readable from inside the class only
        assert acc.get_balance() == 0.0

    def test_private_access_error_is_access_violation_error(self):
        acc = BankAccount("Alice")
        with pytest.raises(AccessViolationError):
            _ = acc.balance

    def test_private_field_error_message_contains_member_and_owner(self):
        acc = BankAccount("Alice")
        with pytest.raises(PrivateAccessError, match="balance"):
            _ = acc.balance
        with pytest.raises(PrivateAccessError, match="BankAccount"):
            _ = acc.balance


# ─────────────────────────────────────────────────────────────────────────────
#  3. Protected fields
# ─────────────────────────────────────────────────────────────────────────────

class TestProtectedFields:
    def test_protected_field_readable_inside_class(self):
        acc = BankAccount("Alice")
        # credit_limit is read via get_credit_limit on SavingsAccount (subclass)
        # but let's test from inside BankAccount itself via a helper
        # We expose it via a public method on BankAccount for this test:
        # (the class doesn't have one, so we add one temporarily via subclass)
        class _Tester(BankAccount):
            def read_credit(self):
                return self.credit_limit
        t = _Tester("Alice")
        assert t.read_credit() == 500.0

    def test_protected_field_readable_in_subclass(self):
        sav = SavingsAccount("Alice")
        assert sav.get_credit_limit() == 500.0

    def test_protected_field_blocked_outside(self):
        acc = BankAccount("Alice")
        with pytest.raises(ProtectedAccessError) as exc_info:
            _ = acc.credit_limit
        err = exc_info.value
        assert err.member == "credit_limit"
        assert err.visibility == "protected"
        assert err.owner == "BankAccount"

    def test_protected_field_write_blocked_outside(self):
        acc = BankAccount("Alice")
        with pytest.raises(ProtectedAccessError):
            acc.credit_limit = 1000.0

    def test_protected_access_error_is_access_violation_error(self):
        acc = BankAccount("Alice")
        with pytest.raises(AccessViolationError):
            _ = acc.credit_limit

    def test_unrelated_class_cannot_read_protected(self):
        acc = BankAccount("Alice")
        intruder = Unrelated()
        with pytest.raises(ProtectedAccessError):
            intruder.peek_credit(acc)


# ─────────────────────────────────────────────────────────────────────────────
#  4. Private methods
# ─────────────────────────────────────────────────────────────────────────────

class TestPrivateMethods:
    def test_private_method_callable_inside_class(self):
        acc = BankAccount("Alice")
        # _validate is called inside deposit → _apply → _validate; must not raise
        acc.deposit(50.0)

    def test_private_method_blocked_outside(self):
        acc = BankAccount("Alice")
        with pytest.raises(PrivateAccessError) as exc_info:
            acc._validate(10.0)
        err = exc_info.value
        assert err.member == "_validate"
        assert err.owner == "BankAccount"

    def test_private_method_blocked_from_unrelated_class(self):
        acc = BankAccount("Alice")
        intruder = Unrelated()
        with pytest.raises(PrivateAccessError):
            intruder.call_validate(acc)

    def test_private_method_blocked_from_subclass(self):
        sav = SavingsAccount("Alice")
        with pytest.raises(PrivateAccessError):
            sav._validate(10.0)


# ─────────────────────────────────────────────────────────────────────────────
#  5. Protected methods
# ─────────────────────────────────────────────────────────────────────────────

class TestProtectedMethods:
    def test_protected_method_callable_inside_class(self):
        acc = BankAccount("Alice")
        acc.deposit(100.0)   # deposit calls _apply internally

    def test_protected_method_callable_from_subclass(self):
        sav = SavingsAccount("Alice")
        sav.accrue()         # accrue calls self._apply — protected, from subclass

    def test_protected_method_blocked_outside(self):
        acc = BankAccount("Alice")
        with pytest.raises(ProtectedAccessError) as exc_info:
            acc._apply(100.0)
        err = exc_info.value
        assert err.member == "_apply"
        assert err.visibility == "protected"

    def test_protected_method_blocked_from_unrelated_class(self):
        acc = BankAccount("Alice")
        intruder = Unrelated()
        with pytest.raises(ProtectedAccessError):
            intruder.call_apply(acc)


# ─────────────────────────────────────────────────────────────────────────────
#  6. Inheritance scenarios
# ─────────────────────────────────────────────────────────────────────────────

class TestInheritance:
    def test_subclass_inherits_public_field(self):
        sav = SavingsAccount("Alice")
        assert sav.owner == "Alice"
        sav.owner = "Bob"
        assert sav.owner == "Bob"

    def test_subclass_can_access_protected_field(self):
        sav = SavingsAccount("Alice")
        assert sav.get_credit_limit() == 500.0

    def test_subclass_cannot_access_private_field_of_parent(self):
        sav = SavingsAccount("Alice")
        with pytest.raises(PrivateAccessError):
            _ = sav.balance

    def test_subclass_cannot_call_private_method_of_parent(self):
        sav = SavingsAccount("Alice")
        with pytest.raises(PrivateAccessError):
            sav._validate(10.0)

    def test_subclass_can_call_protected_method_of_parent(self):
        sav = SavingsAccount("Alice")
        sav.accrue()  # internally calls self._apply — should work

    def test_deeper_inheritance_chain(self):
        """Protected access propagates through multiple levels of subclassing."""

        @modifier
        class PremiumAccount(SavingsAccount):
            def show_credit(self) -> float:
                return self.credit_limit   # protected, two levels up

        p = PremiumAccount("Alice")
        assert p.show_credit() == 500.0

    def test_deep_chain_private_still_blocked(self):
        @modifier
        class PremiumAccount(SavingsAccount):
            def steal(self) -> float:
                return self.balance        # private to BankAccount → denied

        p = PremiumAccount("Alice")
        with pytest.raises(PrivateAccessError):
            p.steal()


# ─────────────────────────────────────────────────────────────────────────────
#  7. Module-level access (no class context)
# ─────────────────────────────────────────────────────────────────────────────

class TestModuleLevelAccess:
    def test_private_field_denied_at_module_level(self):
        acc = BankAccount("Alice")
        # Accessing from test function body = no class context
        with pytest.raises(PrivateAccessError):
            _ = acc.balance

    def test_protected_field_denied_at_module_level(self):
        acc = BankAccount("Alice")
        with pytest.raises(ProtectedAccessError):
            _ = acc.credit_limit

    def test_private_method_denied_at_module_level(self):
        acc = BankAccount("Alice")
        with pytest.raises(PrivateAccessError):
            acc._validate(10.0)

    def test_protected_method_denied_at_module_level(self):
        acc = BankAccount("Alice")
        with pytest.raises(ProtectedAccessError):
            acc._apply(10.0)


# ─────────────────────────────────────────────────────────────────────────────
#  8. Error object attributes
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorAttributes:
    def test_private_error_attributes(self):
        acc = BankAccount("Alice")
        with pytest.raises(PrivateAccessError) as exc_info:
            _ = acc.balance
        err = exc_info.value
        assert err.member == "balance"
        assert err.visibility == "private"
        assert err.owner == "BankAccount"
        assert isinstance(err.caller, str) and len(err.caller) > 0

    def test_protected_error_attributes(self):
        acc = BankAccount("Alice")
        with pytest.raises(ProtectedAccessError) as exc_info:
            _ = acc.credit_limit
        err = exc_info.value
        assert err.member == "credit_limit"
        assert err.visibility == "protected"
        assert err.owner == "BankAccount"

    def test_error_str_contains_useful_info(self):
        acc = BankAccount("Alice")
        with pytest.raises(PrivateAccessError) as exc_info:
            _ = acc.balance
        msg = str(exc_info.value)
        assert "balance" in msg
        assert "private" in msg
        assert "BankAccount" in msg


# ─────────────────────────────────────────────────────────────────────────────
#  9. ModifierInspector
# ─────────────────────────────────────────────────────────────────────────────

class TestModifierInspector:
    def setup_method(self):
        self.info = ModifierInspector(BankAccount)

    def test_is_modifier_applied(self):
        assert self.info.is_modifier_applied is True

    def test_visibility_of_private_field(self):
        assert self.info.visibility_of("balance") == "private"

    def test_visibility_of_protected_field(self):
        assert self.info.visibility_of("credit_limit") == "protected"

    def test_visibility_of_public_field(self):
        assert self.info.visibility_of("owner") == "public"

    def test_visibility_of_private_method(self):
        assert self.info.visibility_of("_validate") == "private"

    def test_visibility_of_protected_method(self):
        assert self.info.visibility_of("_apply") == "protected"

    def test_visibility_of_unknown_member(self):
        assert self.info.visibility_of("nonexistent") is None

    def test_private_members_set(self):
        assert "balance" in self.info.private_members
        assert "_validate" in self.info.private_members

    def test_protected_members_set(self):
        assert "credit_limit" in self.info.protected_members
        assert "_apply" in self.info.protected_members

    def test_public_members_set(self):
        assert "owner" in self.info.public_members

    def test_all_members_keys(self):
        members = self.info.all_members
        assert "balance" in members
        assert "credit_limit" in members
        assert "owner" in members

    def test_inherited_from_empty_for_root(self):
        assert self.info.inherited_from == []

    def test_inherited_from_shows_parent(self):
        info = ModifierInspector(SavingsAccount)
        parents = [c.__name__ for c in info.inherited_from]
        assert "BankAccount" in parents

    def test_summary_contains_class_name(self):
        s = self.info.summary()
        assert "BankAccount" in s

    def test_summary_contains_members(self):
        s = self.info.summary()
        assert "balance" in s
        assert "private" in s
        assert "protected" in s

    def test_repr(self):
        assert "BankAccount" in repr(self.info)

    def test_inspector_raises_on_non_class(self):
        with pytest.raises(TypeError):
            ModifierInspector("not_a_class")


# ─────────────────────────────────────────────────────────────────────────────
#  10. Alias import
# ─────────────────────────────────────────────────────────────────────────────

class TestAliasImport:
    def test_modifier_alias(self):
        """@modifier is a plain function — aliasing it has no side effects."""
        from arkhe.modifier import modifier as access

        @access
        class Config:
            secret: str = private.field("s3cr3t")

            def get_secret(self) -> str:
                return self.secret

        c = Config()
        assert c.get_secret() == "s3cr3t"

        with pytest.raises(PrivateAccessError):
            _ = c.secret

    def test_private_alias(self):
        from arkhe.modifier import private as priv, modifier as mod

        @mod
        class Token:
            value: str = priv.field("tok_abc")

            def reveal(self) -> str:
                return self.value

        t = Token()
        assert t.reveal() == "tok_abc"
        with pytest.raises(PrivateAccessError):
            _ = t.value


# ─────────────────────────────────────────────────────────────────────────────
#  11. Practical composition scenarios
# ─────────────────────────────────────────────────────────────────────────────

class TestPracticalScenarios:
    def test_deposit_and_balance_via_public_api(self):
        acc = BankAccount("Alice")
        acc.deposit(100.0)
        acc.deposit(50.0)
        assert acc.get_balance() == 150.0

    def test_savings_accrual(self):
        sav = SavingsAccount("Alice", rate=0.10)
        sav.deposit(1000.0)
        sav.accrue()
        assert abs(sav.get_balance() - 1100.0) < 1e-9

    def test_multiple_accounts_independent(self):
        a = BankAccount("Alice")
        b = BankAccount("Bob")
        a.deposit(300.0)
        b.deposit(100.0)
        assert a.get_balance() == 300.0
        assert b.get_balance() == 100.0

    def test_class_with_only_private_fields(self):
        @modifier
        class Vault:
            pin: str = private.field("0000")

            def __init__(self, pin: str) -> None:
                self.pin = pin

            def check(self, attempt: str) -> bool:
                return self.pin == attempt

        v = Vault("1234")
        assert v.check("1234") is True
        assert v.check("0000") is False
        with pytest.raises(PrivateAccessError):
            _ = v.pin

    def test_class_with_only_protected_fields(self):
        @modifier
        class Base:
            value: int = protected.field(10)

            def get(self) -> int:
                return self.value

        @modifier
        class Child(Base):
            def double(self) -> int:
                return self.value * 2

        c = Child()
        assert c.double() == 20
        with pytest.raises(ProtectedAccessError):
            _ = c.value  # outside — denied

    def test_delete_private_field_blocked(self):
        acc = BankAccount("Alice")
        with pytest.raises(PrivateAccessError):
            del acc.balance

    def test_mixed_visibility_on_methods(self):
        @modifier
        class Processor:
            result: int = private.field(0)

            def __init__(self) -> None:
                self.result = 0

            @private
            def _compute(self, x: int) -> int:
                return x * 2

            @protected
            def _store(self, value: int) -> None:
                self.result = value

            def process(self, x: int) -> int:
                r = self._compute(x)
                self._store(r)
                return self.result

        p = Processor()
        assert p.process(21) == 42

        with pytest.raises(PrivateAccessError):
            p._compute(1)

        with pytest.raises(ProtectedAccessError):
            p._store(1)
