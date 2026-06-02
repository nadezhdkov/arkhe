from datetime import date
from unittest.mock import patch

import pytest

from nestifypy.input import ask
from nestifypy.input.exceptions import InputConversionError


def test_ask_list_default_type():
    with patch("builtins.input", return_value="a, b, c"):
        assert ask("Tags?").list() == ["a", "b", "c"]


def test_ask_list_int_type():
    with patch("builtins.input", return_value="1, 2, 3"):
        assert ask("Numbers?").list(int) == [1, 2, 3]


def test_ask_list_custom_separator():
    with patch("builtins.input", return_value="a b c"):
        assert ask("Hosts?").list(str, separator=" ") == ["a", "b", "c"]


def test_ask_set():
    with patch("builtins.input", return_value="a, b, a, c"):
        assert ask("Tags?").set() == {"a", "b", "c"}


def test_ask_tuple():
    with patch("builtins.input", return_value="3.5, 7.2"):
        assert ask("x,y?").tuple(float, float) == (3.5, 7.2)


def test_ask_cast():
    with patch("builtins.input", return_value="2023-01-01"):
        assert ask("Date?").cast(date.fromisoformat) == date(2023, 1, 1)


def test_ask_choice():
    with patch("builtins.input", return_value="dev"):
        assert ask("Environment?").choice(["dev", "staging", "prod"]) == "dev"


def test_ask_choice_case_insensitive():
    with patch("builtins.input", return_value="STAGING"):
        assert ask("Environment?").choice(["dev", "staging", "prod"]) == "staging"


def test_ask_list_conversion_error():
    with patch("builtins.input", return_value="1, a, 3"):
        with pytest.raises(InputConversionError):
            ask("Numbers?").list(int)


def test_ask_int():
    with patch("builtins.input", return_value=" 42 "):
        assert ask("Age?").int == 42


def test_ask_float():
    with patch("builtins.input", return_value=" 3.14 "):
        assert ask("Pi?").float == 3.14


def test_ask_bool_true():
    for val in ["1", "true", "yes", "y", "on", "sim", "s"]:
        with patch("builtins.input", return_value=val):
            assert ask("Active?").bool is True


def test_ask_bool_false():
    for val in ["0", "false", "no", "n", "off", "não", "nao"]:
        with patch("builtins.input", return_value=val):
            assert ask("Active?").bool is False


def test_ask_auto():
    with patch("builtins.input", return_value="true"):
        assert ask("Auto?").auto is True
    with patch("builtins.input", return_value="42"):
        assert ask("Auto?").auto == 42
    with patch("builtins.input", return_value="3.14"):
        assert ask("Auto?").auto == 3.14
    with patch("builtins.input", return_value="hello"):
        assert ask("Auto?").auto == "hello"


def test_ask_email():
    with patch("builtins.input", return_value="test@example.com"):
        assert ask("Email?").email == "test@example.com"


def test_ask_url():
    with patch("builtins.input", return_value="https://example.com"):
        assert ask("Website?").url == "https://example.com"


def test_ask_json():
    with patch("builtins.input", return_value='{"key": "value"}'):
        assert ask("JSON?").json == {"key": "value"}


def test_ask_str():
    with patch("builtins.input", return_value=" hello  "):
        assert ask("String?").str == "hello"
