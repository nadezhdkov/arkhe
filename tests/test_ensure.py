"""
tests/test_ensure.py
---------------------
Suite de testes para nestifypy.ensure.

Cobre:
  - exceptions  : EnsureError, EnsureValueError, EnsureTypeError
  - core (Ensure): toda a API estática
  - chain        : toda a API fluente via Ensure.that()

Execução
--------
::

    pytest tests/test_ensure.py -v
    pytest tests/test_ensure.py -v --tb=short
"""

from __future__ import annotations

import pytest

from nestifypy.ensure import Ensure, EnsureChain, EnsureError, EnsureValueError, EnsureTypeError


# ===========================================================================
# Exceptions
# ===========================================================================

class TestExceptions:
    def test_ensure_value_error_is_value_error(self):
        err = EnsureValueError("bad")
        assert isinstance(err, ValueError)
        assert isinstance(err, EnsureError)

    def test_ensure_type_error_is_type_error(self):
        err = EnsureTypeError("bad type")
        assert isinstance(err, TypeError)
        assert isinstance(err, EnsureError)

    def test_catch_as_ensure_error(self):
        with pytest.raises(EnsureError):
            raise EnsureValueError("caught as EnsureError")

    def test_catch_as_value_error(self):
        with pytest.raises(ValueError):
            raise EnsureValueError("caught as ValueError")

    def test_catch_as_type_error(self):
        with pytest.raises(TypeError):
            raise EnsureTypeError("caught as TypeError")


# ===========================================================================
# Ensure — API estática
# ===========================================================================

class TestEnsureNotNone:
    def test_returns_value(self):
        assert Ensure.not_none("hello") == "hello"

    def test_raises_on_none(self):
        with pytest.raises(EnsureValueError):
            Ensure.not_none(None)

    def test_custom_message(self):
        with pytest.raises(EnsureValueError, match="custom msg"):
            Ensure.not_none(None, "custom msg")

    def test_zero_is_not_none(self):
        assert Ensure.not_none(0) == 0

    def test_empty_string_is_not_none(self):
        assert Ensure.not_none("") == ""


class TestEnsureIsNone:
    def test_passes_on_none(self):
        Ensure.is_none(None)

    def test_raises_on_value(self):
        with pytest.raises(EnsureValueError):
            Ensure.is_none("something")


class TestEnsureNotEmpty:
    def test_non_empty_string(self):
        assert Ensure.not_empty("hello") == "hello"

    def test_non_empty_list(self):
        assert Ensure.not_empty([1, 2]) == [1, 2]

    def test_non_empty_dict(self):
        assert Ensure.not_empty({"a": 1}) == {"a": 1}

    def test_empty_string_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.not_empty("")

    def test_empty_list_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.not_empty([])

    def test_empty_set_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.not_empty(set())

    def test_empty_dict_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.not_empty({})

    def test_empty_tuple_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.not_empty(())


class TestEnsureNotBlank:
    def test_normal_string(self):
        assert Ensure.not_blank("hello") == "hello"

    def test_blank_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.not_blank("   ")

    def test_empty_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.not_blank("")

    def test_non_string_raises_type_error(self):
        with pytest.raises(EnsureTypeError):
            Ensure.not_blank(42)  # type: ignore


class TestEnsureMinMaxLength:
    def test_min_length_ok(self):
        assert Ensure.min_length("hello", 3) == "hello"

    def test_min_length_exact(self):
        assert Ensure.min_length("abc", 3) == "abc"

    def test_min_length_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.min_length("ab", 3)

    def test_max_length_ok(self):
        assert Ensure.max_length("hi", 5) == "hi"

    def test_max_length_exact(self):
        assert Ensure.max_length("hello", 5) == "hello"

    def test_max_length_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.max_length("toolong", 4)

    def test_works_with_list(self):
        assert Ensure.min_length([1, 2, 3], 2) == [1, 2, 3]


class TestEnsureMatches:
    EMAIL = r"[^@]+@[^@]+\.[^@]+"

    def test_valid_email(self):
        assert Ensure.matches("user@example.com", self.EMAIL) == "user@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.matches("not-an-email", self.EMAIL)

    def test_non_string_raises(self):
        with pytest.raises(EnsureTypeError):
            Ensure.matches(123, self.EMAIL)  # type: ignore


class TestEnsureStartsEndsWith:
    def test_starts_with_ok(self):
        assert Ensure.starts_with("/api/users", "/") == "/api/users"

    def test_starts_with_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.starts_with("api/users", "/")

    def test_ends_with_ok(self):
        assert Ensure.ends_with("config.json", ".json") == "config.json"

    def test_ends_with_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.ends_with("config.yaml", ".json")

    def test_non_string_starts_with_raises(self):
        with pytest.raises(EnsureTypeError):
            Ensure.starts_with(123, "/")  # type: ignore

    def test_non_string_ends_with_raises(self):
        with pytest.raises(EnsureTypeError):
            Ensure.ends_with(123, ".json")  # type: ignore


class TestEnsureNumeric:
    def test_positive_ok(self):
        assert Ensure.positive(5) == 5

    def test_positive_zero_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.positive(0)

    def test_positive_negative_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.positive(-1)

    def test_negative_ok(self):
        assert Ensure.negative(-3) == -3

    def test_negative_zero_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.negative(0)

    def test_non_negative_zero_ok(self):
        assert Ensure.non_negative(0) == 0

    def test_non_negative_positive_ok(self):
        assert Ensure.non_negative(1) == 1

    def test_non_negative_negative_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.non_negative(-1)

    def test_greater_than_ok(self):
        assert Ensure.greater_than(10, 5) == 10

    def test_greater_than_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.greater_than(5, 5)

    def test_greater_or_equal_ok(self):
        assert Ensure.greater_or_equal(5, 5) == 5

    def test_greater_or_equal_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.greater_or_equal(4, 5)

    def test_less_than_ok(self):
        assert Ensure.less_than(3, 10) == 3

    def test_less_than_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.less_than(10, 10)

    def test_less_or_equal_ok(self):
        assert Ensure.less_or_equal(10, 10) == 10

    def test_less_or_equal_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.less_or_equal(11, 10)

    def test_between_ok(self):
        assert Ensure.between(5, 1, 10) == 5

    def test_between_lower_bound(self):
        assert Ensure.between(1, 1, 10) == 1

    def test_between_upper_bound(self):
        assert Ensure.between(10, 1, 10) == 10

    def test_between_raises_below(self):
        with pytest.raises(EnsureValueError):
            Ensure.between(0, 1, 10)

    def test_between_raises_above(self):
        with pytest.raises(EnsureValueError):
            Ensure.between(11, 1, 10)

    def test_float_positive(self):
        assert Ensure.positive(0.1) == pytest.approx(0.1)

    def test_float_between(self):
        assert Ensure.between(0.5, 0.0, 1.0) == pytest.approx(0.5)


class TestEnsureCollection:
    def test_contains_ok(self):
        assert Ensure.contains(["admin", "user"], "admin") == ["admin", "user"]

    def test_contains_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.contains(["admin", "user"], "root")

    def test_not_contains_ok(self):
        assert Ensure.not_contains(["a", "b"], "c") == ["a", "b"]

    def test_not_contains_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.not_contains(["a", "banned"], "banned")

    def test_unique_ok(self):
        assert Ensure.unique([1, 2, 3]) == [1, 2, 3]

    def test_unique_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.unique([1, 2, 2, 3])

    def test_contains_string(self):
        assert Ensure.contains("hello world", "world") == "hello world"

    def test_contains_dict_key(self):
        d = {"role": "admin"}
        assert Ensure.contains(d, "role") == d


class TestEnsureType:
    def test_is_instance_ok(self):
        assert Ensure.is_instance("hello", str) == "hello"

    def test_is_instance_raises(self):
        with pytest.raises(EnsureTypeError):
            Ensure.is_instance(42, str)

    def test_is_subclass_ok(self):
        class Animal: pass
        class Dog(Animal): pass
        assert Ensure.is_subclass(Dog, Animal) is Dog

    def test_is_subclass_raises(self):
        class Animal: pass
        class Cat: pass
        with pytest.raises(EnsureTypeError):
            Ensure.is_subclass(Cat, Animal)

    def test_is_callable_ok(self):
        assert Ensure.is_callable(len) is len

    def test_is_callable_lambda(self):
        f = lambda x: x
        assert Ensure.is_callable(f) is f

    def test_is_callable_raises(self):
        with pytest.raises(EnsureTypeError):
            Ensure.is_callable("not callable")  # type: ignore


class TestEnsureState:
    def test_is_true_ok(self):
        assert Ensure.is_true(True) is True

    def test_is_true_truthy(self):
        assert Ensure.is_true(1) == 1

    def test_is_true_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.is_true(False)

    def test_is_true_raises_falsy(self):
        with pytest.raises(EnsureValueError):
            Ensure.is_true(0)

    def test_is_false_ok(self):
        assert Ensure.is_false(False) is False

    def test_is_false_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.is_false(True)

    def test_is_true_custom_msg(self):
        with pytest.raises(EnsureValueError, match="Service is inactive"):
            Ensure.is_true(False, "Service is inactive")


class TestEnsureEquality:
    def test_equals_ok(self):
        assert Ensure.equals(42, 42) == 42

    def test_equals_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.equals(42, 43)

    def test_not_equals_ok(self):
        assert Ensure.not_equals(1, 2) == 1

    def test_not_equals_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.not_equals(1, 1)


class TestEnsureMembership:
    STATUSES = ["pending", "approved", "rejected"]

    def test_one_of_ok(self):
        assert Ensure.one_of("approved", self.STATUSES) == "approved"

    def test_one_of_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.one_of("unknown", self.STATUSES)

    def test_not_one_of_ok(self):
        assert Ensure.not_one_of("active", ["banned"]) == "active"

    def test_not_one_of_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.not_one_of("banned", ["banned"])

    def test_one_of_with_set(self):
        assert Ensure.one_of(2, {1, 2, 3}) == 2


# ===========================================================================
# EnsureChain — API fluente
# ===========================================================================

class TestChainNotNone:
    def test_passes(self):
        assert Ensure.that("hello").not_none().unwrap() == "hello"

    def test_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that(None).not_none()

    def test_custom_name_in_message(self):
        with pytest.raises(EnsureValueError, match="email"):
            Ensure.that(None, "email").not_none()


class TestChainIsNone:
    def test_passes(self):
        Ensure.that(None).is_none()

    def test_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that("value").is_none()


class TestChainString:
    def test_not_blank_ok(self):
        assert Ensure.that("hello").not_blank().unwrap() == "hello"

    def test_not_blank_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that("  ").not_blank()

    def test_min_length_ok(self):
        assert Ensure.that("hello").min_length(3).unwrap() == "hello"

    def test_min_length_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that("ab").min_length(3)

    def test_max_length_ok(self):
        assert Ensure.that("hi").max_length(5).unwrap() == "hi"

    def test_max_length_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that("toolong").max_length(4)

    def test_matches_ok(self):
        result = Ensure.that("user@test.com").matches(r"[^@]+@[^@]+\.[^@]+").unwrap()
        assert result == "user@test.com"

    def test_matches_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that("not-email").matches(r"[^@]+@[^@]+\.[^@]+")

    def test_starts_with_ok(self):
        assert Ensure.that("/api/v1").starts_with("/").unwrap() == "/api/v1"

    def test_starts_with_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that("api/v1").starts_with("/")

    def test_ends_with_ok(self):
        assert Ensure.that("data.json").ends_with(".json").unwrap() == "data.json"

    def test_ends_with_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that("data.xml").ends_with(".json")


class TestChainNumeric:
    def test_positive(self):
        assert Ensure.that(5).positive().unwrap() == 5

    def test_negative(self):
        assert Ensure.that(-3).negative().unwrap() == -3

    def test_non_negative(self):
        assert Ensure.that(0).non_negative().unwrap() == 0

    def test_greater_than(self):
        assert Ensure.that(10).greater_than(5).unwrap() == 10

    def test_greater_or_equal(self):
        assert Ensure.that(5).greater_or_equal(5).unwrap() == 5

    def test_less_than(self):
        assert Ensure.that(3).less_than(10).unwrap() == 3

    def test_less_or_equal(self):
        assert Ensure.that(10).less_or_equal(10).unwrap() == 10

    def test_between(self):
        assert Ensure.that(5).between(1, 10).unwrap() == 5

    def test_between_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that(0).between(1, 10)

    def test_chain_positive_less_than(self):
        result = (
            Ensure.that(42)
                .positive()
                .less_than(100)
                .unwrap()
        )
        assert result == 42


class TestChainCollection:
    def test_not_empty_ok(self):
        assert Ensure.that([1, 2]).not_empty().unwrap() == [1, 2]

    def test_not_empty_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that([]).not_empty()

    def test_contains_ok(self):
        assert Ensure.that(["admin", "user"]).contains("admin").unwrap() == ["admin", "user"]

    def test_not_contains_ok(self):
        assert Ensure.that(["a", "b"]).not_contains("c").unwrap() == ["a", "b"]

    def test_unique_ok(self):
        assert Ensure.that([1, 2, 3]).unique().unwrap() == [1, 2, 3]

    def test_unique_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that([1, 1, 2]).unique()


class TestChainType:
    def test_is_instance_ok(self):
        assert Ensure.that("hello").is_instance(str).unwrap() == "hello"

    def test_is_instance_raises(self):
        with pytest.raises(EnsureTypeError):
            Ensure.that(42).is_instance(str)

    def test_is_callable_ok(self):
        assert Ensure.that(len).is_callable().unwrap() is len

    def test_is_callable_raises(self):
        with pytest.raises(EnsureTypeError):
            Ensure.that("not callable").is_callable()

    def test_is_subclass_ok(self):
        class Base: pass
        class Child(Base): pass
        assert Ensure.that(Child).is_subclass(Base).unwrap() is Child


class TestChainState:
    def test_is_true_ok(self):
        assert Ensure.that(True).is_true().unwrap() is True

    def test_is_true_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that(False).is_true()

    def test_is_false_ok(self):
        assert Ensure.that(False).is_false().unwrap() is False

    def test_is_false_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that(True).is_false()


class TestChainEquality:
    def test_equals_ok(self):
        assert Ensure.that(10).equals(10).unwrap() == 10

    def test_equals_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that(10).equals(99)

    def test_not_equals_ok(self):
        assert Ensure.that(1).not_equals(2).unwrap() == 1

    def test_not_equals_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that(1).not_equals(1)


class TestChainMembership:
    def test_one_of_ok(self):
        assert Ensure.that("approved").one_of(["pending", "approved"]).unwrap() == "approved"

    def test_one_of_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that("unknown").one_of(["pending", "approved"])

    def test_not_one_of_ok(self):
        assert Ensure.that("active").not_one_of(["banned"]).unwrap() == "active"

    def test_not_one_of_raises(self):
        with pytest.raises(EnsureValueError):
            Ensure.that("banned").not_one_of(["banned"])


class TestChainMap:
    def test_map_strip(self):
        result = Ensure.that("  hello  ").not_blank().map(str.strip).unwrap()
        assert result == "hello"

    def test_map_lower(self):
        result = Ensure.that("HOPE").map(str.lower).unwrap()
        assert result == "hope"

    def test_map_chain(self):
        result = (
            Ensure.that("  Hope  ")
                .not_blank()
                .map(str.strip)
                .map(str.lower)
                .unwrap()
        )
        assert result == "hope"

    def test_map_numeric(self):
        result = Ensure.that(4).positive().map(lambda x: x * 2).unwrap()
        assert result == 8

    def test_map_to_different_type(self):
        result = Ensure.that("42").not_blank().map(int).unwrap()
        assert result == 42


# ===========================================================================
# Integração — exemplos da spec
# ===========================================================================

class TestIntegration:
    def test_product_entity(self):
        class Product:
            def __init__(self, name, price, categories):
                self.name       = Ensure.not_blank(name)
                self.price      = Ensure.positive(price)
                self.categories = Ensure.not_empty(categories)

        p = Product("Widget", 9.99, ["electronics"])
        assert p.name == "Widget"
        assert p.price == pytest.approx(9.99)
        assert p.categories == ["electronics"]

    def test_product_entity_invalid_price(self):
        class Product:
            def __init__(self, name, price, categories):
                self.name  = Ensure.not_blank(name)
                self.price = Ensure.positive(price)
                self.categories = Ensure.not_empty(categories)

        with pytest.raises(EnsureValueError):
            Product("Widget", -1, ["electronics"])

    def test_payment_service_pattern(self):
        class PaymentService:
            def __init__(self, active):
                self.active = active

            def process(self, amount):
                Ensure.is_true(self.active, "Service is inactive")
                Ensure.greater_or_equal(amount, 5.0)
                return amount

        svc = PaymentService(active=True)
        assert svc.process(10.0) == pytest.approx(10.0)

        with pytest.raises(EnsureValueError, match="Service is inactive"):
            PaymentService(active=False).process(10.0)

        with pytest.raises(EnsureValueError):
            PaymentService(active=True).process(1.0)

    def test_fluent_username_pipeline(self):
        username = (
            Ensure.that("  Hope  ")
                .not_none()
                .not_blank()
                .map(str.strip)
                .min_length(3)
                .max_length(20)
                .map(str.lower)
                .unwrap()
        )
        assert username == "hope"

    def test_fluent_age_validation(self):
        age = (
            Ensure.that(25)
                .positive()
                .less_or_equal(120)
                .unwrap()
        )
        assert age == 25

    def test_fluent_collection_validation(self):
        users = (
            Ensure.that([1, 2, 3])
                .not_empty()
                .unique()
                .unwrap()
        )
        assert users == [1, 2, 3]

    def test_chain_stops_on_first_failure(self):
        with pytest.raises(EnsureValueError):
            (
                Ensure.that(None)
                    .not_none()     # ← falha aqui
                    .not_blank()    # não chega aqui
            )

    def test_repr(self):
        chain = Ensure.that("hello")
        assert "EnsureChain" in repr(chain)
        assert "hello" in repr(chain)
