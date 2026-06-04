"""
tests/test_math.py  —  seção _money (substituição completa)
------------------------------------------------------------
Remove testes de cache em disco (load_from_disk, _CACHE_DIR, _CACHE_FILE)
e adapta TestMoneyCache ao novo _RateCache somente em memória.
"""

from __future__ import annotations

import math
import time
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from arkhe.math._types import BigDecimal, FailureResult, DivisionByZeroError
from arkhe.math._money import Money, Currency, Portfolio, _FALLBACK_RATES_FROM_USD, _cache


# ---------------------------------------------------------------------------
# Fixture — reseta cache antes/depois de cada teste
# ---------------------------------------------------------------------------

def _force_fallback():
    """Força o Money a usar taxas de fallback (sem rede, sem cache)."""
    _cache._rates = {}
    _cache._fetched_at = None


@pytest.fixture(autouse=True)
def reset_money_cache():
    _force_fallback()
    yield
    _force_fallback()


# ===========================================================================
# Currency
# ===========================================================================

class TestCurrency:
    def test_fiat_constants(self):
        assert Currency.USD == "USD"
        assert Currency.BRL == "BRL"
        assert Currency.EUR == "EUR"
        assert Currency.JPY == "JPY"
        assert Currency.GBP == "GBP"

    def test_crypto_constants(self):
        assert Currency.BTC  == "BTC"
        assert Currency.ETH  == "ETH"
        assert Currency.SOL  == "SOL"
        assert Currency.USDT == "USDT"
        assert Currency.USDC == "USDC"
        assert Currency.DOGE == "DOGE"


# ===========================================================================
# Money — criação
# ===========================================================================

class TestMoneyCreation:
    def test_from_string(self):
        m = Money("19.99", "USD")
        assert isinstance(m.amount(), BigDecimal)
        assert m.currency() == "USD"

    def test_from_int(self):
        m = Money(100, "BRL")
        assert m.amount().to_float() == pytest.approx(100.0)

    def test_from_float(self):
        m = Money(9.99, "EUR")
        assert m.amount().to_float() == pytest.approx(9.99, rel=1e-4)

    def test_from_decimal(self):
        m = Money(Decimal("50.00"), "USD")
        assert m.amount().to_decimal() == Decimal("50.00")

    def test_from_bigdecimal(self):
        bd = BigDecimal("25.50")
        m = Money(bd, "USD")
        assert m.amount() is bd

    def test_currency_uppercased(self):
        assert Money("10", "usd").currency() == "USD"

    def test_from_currency_constant(self):
        m = Money(100, Currency.USD)
        assert m.currency() == "USD"


# ===========================================================================
# Money — conversão
# ===========================================================================

class TestMoneyConversion:
    def test_same_currency(self):
        result = Money("100", "USD").to("USD")
        assert result.amount().to_float() == pytest.approx(100.0)

    def test_usd_to_brl(self):
        result = Money("100", "USD").to("BRL")
        assert result.currency() == "BRL"
        rates = Money._get_rates()
        expected = BigDecimal("100").divide(rates["USD"]).multiply(rates["BRL"])
        assert result.amount().to_float() == pytest.approx(expected.to_float(), rel=1e-6)

    def test_brl_to_usd(self):
        result = Money("100", "BRL").to("USD")
        assert result.currency() == "USD"
        rates = Money._get_rates()
        expected = BigDecimal("100").divide(rates["BRL"]).multiply(rates["USD"])
        assert result.amount().to_float() == pytest.approx(expected.to_float(), rel=1e-6)

    def test_eur_to_jpy(self):
        result = Money("100", "EUR").to("JPY")
        assert result.currency() == "JPY"
        assert result.amount().to_float() > 100

    def test_unknown_from_currency_raises(self):
        with pytest.raises(ValueError):
            Money("10", "XYZ").to("USD")

    def test_unknown_to_currency_raises(self):
        with pytest.raises(ValueError):
            Money("10", "USD").to("XYZ")

    def test_chain_conversion(self):
        result = Money("100", "USD").to("BRL").to("USD")
        assert result.amount().to_float() == pytest.approx(100.0, rel=1e-4)

    def test_crypto_usd_to_btc(self):
        btc = Money("1", "USD").to("BTC")
        assert btc.currency() == "BTC"
        assert btc.amount().to_float() > 0

    def test_btc_to_usd(self):
        result = Money("1", "BTC").to("USD")
        assert result.currency() == "USD"
        rates = Money._get_rates()
        expected = BigDecimal("1").divide(rates["BTC"]).multiply(rates["USD"])
        assert result.amount().to_float() == pytest.approx(expected.to_float(), rel=1e-6)


# ===========================================================================
# Money — aritmética
# ===========================================================================

class TestMoneyArithmetic:
    def test_add_same_currency(self):
        result = Money("10", "USD").add(Money("5", "USD"))
        assert result.amount().to_float() == pytest.approx(15.0)
        assert result.currency() == "USD"

    def test_add_different_currency(self):
        result = Money("100", "USD").add(Money("0", "BRL"))
        assert result.amount().to_float() == pytest.approx(100.0, rel=1e-4)

    def test_subtract(self):
        result = Money("20", "USD").subtract(Money("5", "USD"))
        assert result.amount().to_float() == pytest.approx(15.0)

    def test_multiply_by_scalar(self):
        result = Money("100", "USD").multiply("0.17")
        assert result.amount().to_float() == pytest.approx(17.0)

    def test_multiply_int(self):
        result = Money("50", "BRL").multiply(3)
        assert result.amount().to_float() == pytest.approx(150.0)

    def test_divide(self):
        result = Money("100", "USD").divide("4")
        assert result.amount().to_float() == pytest.approx(25.0)

    def test_divide_by_zero_returns_failure(self):
        result = Money("100", "USD").divide("0")
        assert isinstance(result, FailureResult)

    def test_ratio_same_currency(self):
        ratio = Money("100", "USD").ratio(Money("25", "USD"))
        assert ratio.to_float() == pytest.approx(4.0)

    def test_ratio_equal_values(self):
        ratio = Money("100", "USD").ratio(Money("100", "USD"))
        assert ratio.to_float() == pytest.approx(1.0, rel=1e-6)

    def test_operator_add(self):
        result = Money("10", "USD") + Money("5", "USD")
        assert result.amount().to_float() == pytest.approx(15.0)

    def test_operator_sub(self):
        result = Money("10", "USD") - Money("3", "USD")
        assert result.amount().to_float() == pytest.approx(7.0)

    def test_operator_mul(self):
        result = Money("10", "USD") * 2
        assert result.amount().to_float() == pytest.approx(20.0)

    def test_operator_rmul(self):
        result = 3 * Money("10", "USD")
        assert result.amount().to_float() == pytest.approx(30.0)

    def test_operator_div(self):
        result = Money("20", "USD") / 4
        assert result.amount().to_float() == pytest.approx(5.0)

    def test_fluent_chain(self):
        # 100 * 0.17 + 10 - 5 = 22
        result = (
            Money("100", "USD")
            .multiply("0.17")
            .add(Money("10", "USD"))
            .subtract(Money("5", "USD"))
        )
        assert result.amount().to_float() == pytest.approx(22.0)


# ===========================================================================
# Money — arredondamento
# ===========================================================================

class TestMoneyRounding:
    def test_round(self):
        result = Money("19.999", "USD").round(2)
        assert result.amount().to_float() == pytest.approx(20.0, rel=1e-4)

    def test_floor(self):
        result = Money("19.9", "USD").floor()
        assert result.amount().to_int() == 19

    def test_ceil(self):
        result = Money("19.1", "USD").ceil()
        assert result.amount().to_int() == 20

    def test_round_preserves_currency(self):
        assert Money("1.235", "BRL").round(2).currency() == "BRL"


# ===========================================================================
# Money — comparações
# ===========================================================================

class TestMoneyComparisons:
    def test_eq_same_currency(self):
        assert Money("100", "USD") == Money("100", "USD")

    def test_neq_same_currency(self):
        assert Money("100", "USD") != Money("101", "USD")

    def test_lt_same_currency(self):
        assert Money("50", "USD") < Money("100", "USD")

    def test_gt_same_currency(self):
        assert Money("100", "USD") > Money("50", "USD")

    def test_le_same_currency(self):
        assert Money("50", "USD") <= Money("100", "USD")
        assert Money("100", "USD") <= Money("100", "USD")

    def test_ge_same_currency(self):
        assert Money("100", "USD") >= Money("50", "USD")
        assert Money("100", "USD") >= Money("100", "USD")

    def test_comparison_different_currencies(self):
        assert Money("100", "USD") > Money("1", "BRL")

    def test_zero_is_not_greater(self):
        assert not (Money("0", "USD") > Money("100", "USD"))


# ===========================================================================
# Money — formatação
# ===========================================================================

class TestMoneyFormatting:
    def test_str(self):
        s = str(Money("19.99", "USD"))
        assert "USD" in s
        assert "19.99" in s

    def test_repr(self):
        r = repr(Money("10", "USD"))
        assert "Money" in r
        assert "USD" in r

    def test_format_en_us(self):
        result = Money("1234.56", "USD").format(locale="en_US")
        assert "$" in result
        assert "1,234.56" in result

    def test_format_pt_br(self):
        result = Money("1234.56", "BRL").format(locale="pt_BR")
        assert "R$" in result
        assert "1.234,56" in result

    def test_format_de_de(self):
        result = Money("1234.56", "EUR").format(locale="de_DE")
        assert "€" in result
        assert "1.234,56" in result

    def test_format_decimal_places(self):
        result = Money("10", "USD").format(decimal_places=4, locale="en_US")
        assert "10.0000" in result

    def test_to_float(self):
        assert Money("9.99", "USD").to_float() == pytest.approx(9.99)

    def test_to_decimal(self):
        assert Money("9.99", "USD").to_decimal() == Decimal("9.99")


# ===========================================================================
# Money — cache (somente memória)
# ===========================================================================

class TestMoneyCache:
    def test_cache_max_age(self):
        Money.cache(hours=6)  # não deve lançar exceção

    def test_cache_stores_bigdecimal(self):
        rates = Money._get_rates()
        for key, val in rates.items():
            assert isinstance(val, BigDecimal), f"{key} não é BigDecimal"

    def test_cache_is_valid_after_store(self):
        rates = {k: BigDecimal(v) for k, v in _FALLBACK_RATES_FROM_USD.items()}
        _cache.store(rates)
        assert _cache.is_valid()

    def test_cache_invalid_after_invalidate(self):
        rates = {k: BigDecimal(v) for k, v in _FALLBACK_RATES_FROM_USD.items()}
        _cache.store(rates)
        _cache.invalidate()
        assert not _cache.is_valid()

    def test_cache_expires(self):
        rates = {k: BigDecimal(v) for k, v in _FALLBACK_RATES_FROM_USD.items()}
        _cache.store(rates)
        # Simula expiração retroagindo o timestamp
        _cache._fetched_at = time.time() - (_cache._max_age_seconds + 1)
        assert not _cache.is_valid()

    def test_second_call_uses_cache(self):
        # Primeira chamada popula o cache
        rates1 = Money._get_rates()
        assert _cache.is_valid()
        # Segunda chamada deve retornar o mesmo objeto (cache em memória)
        rates2 = Money._get_rates()
        assert rates1 is rates2

    def test_refresh_rates_invalidates_cache(self):
        Money._get_rates()
        assert _cache.is_valid()
        # Invalida sem ir à rede (forçamos fallback logo depois)
        _cache.invalidate()
        assert not _cache.is_valid()


# ===========================================================================
# Money — fallback estático
# ===========================================================================

class TestMoneyFallbackRates:
    def test_no_float_in_fallback(self):
        for symbol, rate in _FALLBACK_RATES_FROM_USD.items():
            assert isinstance(rate, str), f"{symbol}: esperado str, recebeu {type(rate)}"

    def test_fallback_rates_convert_to_bigdecimal(self):
        for symbol, rate in _FALLBACK_RATES_FROM_USD.items():
            bd = BigDecimal(rate)
            assert bd.to_float() > 0, f"Taxa de {symbol} deve ser positiva"

    def test_crypto_symbols_in_fallback(self):
        crypto = ["BTC", "ETH", "SOL", "ADA", "XRP", "DOGE",
                  "USDT", "USDC", "BNB", "TRX", "AVAX", "MATIC", "DAI"]
        for symbol in crypto:
            assert symbol in _FALLBACK_RATES_FROM_USD, f"{symbol} ausente no fallback"

    def test_get_rates_always_has_crypto(self):
        """Mesmo sem rede, _get_rates deve conter todos os criptoativos."""
        rates = Money._get_rates()
        for symbol in ["BTC", "ETH", "SOL", "DOGE", "USDT"]:
            assert symbol in rates, f"{symbol} ausente em _get_rates"
            assert isinstance(rates[symbol], BigDecimal)


# ===========================================================================
# Money — log e fetcher
# ===========================================================================

class TestMoneyConversionLog:
    def test_enable_log_flag(self):
        Money.enable_conversion_log(True)
        assert Money._log_conversions is True
        Money.enable_conversion_log(False)
        assert Money._log_conversions is False


class TestMoneyAutoNet:
    def test_set_fetcher_manually(self):
        mock_fetcher = MagicMock()
        Money.set_fetcher(mock_fetcher)
        assert Money._fetcher is mock_fetcher
        Money._fetcher = None  # restaura

    def test_set_timeout(self):
        Money.set_timeout(15)
        assert Money._HTTP_TIMEOUT == 15
        Money.set_timeout(8)  # restaura padrão

    def test_set_retries(self):
        Money.set_retries(5)
        assert Money._HTTP_RETRIES == 5
        Money.set_retries(2)  # restaura padrão


# ===========================================================================
# Portfolio
# ===========================================================================

class TestPortfolio:
    def test_add_and_len(self):
        p = Portfolio()
        p.add(Money("100", "USD"))
        p.add(Money("50", "USD"))
        assert len(p) == 2

    def test_total_same_currency(self):
        p = Portfolio()
        p.add(Money("100", "USD"))
        p.add(Money("50", "USD"))
        total = p.total("USD")
        assert total.amount().to_float() == pytest.approx(150.0)
        assert total.currency() == "USD"

    def test_total_empty_portfolio(self):
        total = Portfolio().total("USD")
        assert total.amount().to_float() == pytest.approx(0.0)

    def test_total_different_currencies(self):
        p = Portfolio()
        p.add(Money("0", "BRL"))
        p.add(Money("100", "USD"))
        total = p.total("USD")
        assert total.amount().to_float() == pytest.approx(100.0, rel=1e-3)

    def test_remove(self):
        p = Portfolio()
        m = Money("100", "USD")
        p.add(m)
        p.add(Money("50", "USD"))
        p.remove(m)
        assert len(p) == 1

    def test_positions(self):
        p = Portfolio()
        p.add(Money("100", "USD")).add(Money("200", "USD"))
        assert len(p.positions()) == 2

    def test_chaining(self):
        p = Portfolio()
        result = p.add(Money("10", "USD")).add(Money("20", "USD"))
        assert result is p
        assert len(p) == 2

    def test_summary_contains_total(self):
        p = Portfolio()
        p.add(Money("100", "USD"))
        summary = p.summary("USD")
        assert "Total" in summary
        assert "100" in summary

    def test_repr(self):
        p = Portfolio()
        p.add(Money("1", "USD"))
        assert "Portfolio" in repr(p)

    def test_total_converted_currency(self):
        p = Portfolio()
        p.add(Money("100", "USD"))
        total_brl = p.total("BRL")
        assert total_brl.currency() == "BRL"
        rates = Money._get_rates()
        expected = BigDecimal("100").divide(rates["USD"]).multiply(rates["BRL"])
        assert total_brl.amount().to_float() == pytest.approx(expected.to_float(), rel=1e-6)
