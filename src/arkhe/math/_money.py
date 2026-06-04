"""
arkhe.math._money
---------------------
Money v2 — Precisão Arbitrária, Cache em Memória, Criptoativos.

Utiliza BigDecimal internamente — sem float em nenhum momento do pipeline
financeiro.

Integra-se automaticamente com NestifyPy Net quando disponível.
Cache somente em memória (sem escrita em disco).

Dependências HTTP (em ordem de preferência):
  1. NestifyPy Net  (arkhe.net)
  2. requests       (pip install requests)
  3. urllib         (stdlib — sempre disponível)

::

    Money("19.99", "USD").multiply("0.17").add(Money("5.00", "USD")).to("BRL")

    Money("0.5", "BTC").to("USD")

    Money(100, Currency.USD) > Money(50, Currency.USD)

    portfolio = Portfolio()
    portfolio.add(Money("0.5", "BTC"))
    portfolio.total("USD")

    btc = CryptoPrice.of("BTC")
    print(btc.price_usd)
"""

from __future__ import annotations

import json
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union


# ---------------------------------------------------------------------------
# Import interno — BigDecimal e _NumericBase
# ---------------------------------------------------------------------------

from arkhe.math._types import BigDecimal, _NumericBase, FailureResult, DivisionByZeroError


# ---------------------------------------------------------------------------
# Integração automática com Net
# ---------------------------------------------------------------------------

try:
    from arkhe.net import request as _net_request  # type: ignore
    _HAS_NET = True
except ImportError:
    _net_request = None  # type: ignore[assignment]
    _HAS_NET = False


# ---------------------------------------------------------------------------
# Detecção de requests
# ---------------------------------------------------------------------------

try:
    import requests as _requests  # type: ignore
    _HAS_REQUESTS = True
except ImportError:
    _requests = None  # type: ignore[assignment]
    _HAS_REQUESTS = False


# ---------------------------------------------------------------------------
# Currency — enum de moedas fiduciárias e criptoativos
# ---------------------------------------------------------------------------

class Currency:
    """
    Constantes de moedas fiduciárias e criptoativos.

    ::

        Money(100, Currency.USD)
        Money("0.5", Currency.BTC)
    """

    # Fiduciárias
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    BRL = "BRL"
    CAD = "CAD"
    AUD = "AUD"
    CHF = "CHF"
    CNY = "CNY"
    INR = "INR"
    MXN = "MXN"
    ARS = "ARS"
    CLP = "CLP"
    COP = "COP"
    PEN = "PEN"
    UYU = "UYU"
    KRW = "KRW"
    SGD = "SGD"
    HKD = "HKD"
    NOK = "NOK"
    SEK = "SEK"
    DKK = "DKK"
    PLN = "PLN"
    CZK = "CZK"
    HUF = "HUF"
    RUB = "RUB"
    TRY = "TRY"
    ZAR = "ZAR"
    NZD = "NZD"
    THB = "THB"
    IDR = "IDR"
    MYR = "MYR"
    PHP = "PHP"
    VND = "VND"
    EGP = "EGP"
    NGN = "NGN"
    KES = "KES"
    AED = "AED"
    SAR = "SAR"
    ILS = "ILS"
    PKR = "PKR"
    BDT = "BDT"
    UAH = "UAH"
    RON = "RON"
    BGN = "BGN"
    HRK = "HRK"

    # Criptoativos
    BTC   = "BTC"
    ETH   = "ETH"
    SOL   = "SOL"
    ADA   = "ADA"
    XRP   = "XRP"
    DOGE  = "DOGE"
    USDT  = "USDT"
    USDC  = "USDC"
    BNB   = "BNB"
    TRX   = "TRX"
    AVAX  = "AVAX"
    MATIC = "MATIC"
    DAI   = "DAI"


# ---------------------------------------------------------------------------
# Taxas de fallback estáticas (strings → sem float)
# Relativas ao USD como base.
# ---------------------------------------------------------------------------

_FALLBACK_RATES_FROM_USD: Dict[str, str] = {
    # Fiduciárias
    "USD":  "1.0",
    "EUR":  "0.92",
    "GBP":  "0.79",
    "JPY":  "149.50",
    "BRL":  "5.00",
    "CAD":  "1.36",
    "AUD":  "1.53",
    "CHF":  "0.89",
    "CNY":  "7.24",
    "INR":  "83.10",
    "MXN":  "17.15",
    "ARS":  "850.0",
    "CLP":  "920.0",
    "COP":  "3950.0",
    "PEN":  "3.72",
    "UYU":  "38.5",
    "KRW":  "1330.0",
    "SGD":  "1.34",
    "HKD":  "7.82",
    "NOK":  "10.55",
    "SEK":  "10.42",
    "DKK":  "6.88",
    "PLN":  "4.03",
    "CZK":  "22.9",
    "HUF":  "355.0",
    "RUB":  "91.0",
    "TRY":  "30.5",
    "ZAR":  "18.6",
    "NZD":  "1.63",
    "THB":  "35.1",
    "IDR":  "15700.0",
    "MYR":  "4.72",
    "PHP":  "56.3",
    "VND":  "24400.0",
    "EGP":  "30.9",
    "NGN":  "1580.0",
    "KES":  "130.0",
    "AED":  "3.67",
    "SAR":  "3.75",
    "ILS":  "3.70",
    "PKR":  "280.0",
    "BDT":  "110.0",
    "UAH":  "37.0",
    "RON":  "4.57",
    "BGN":  "1.80",
    "HRK":  "6.90",
    # Criptoativos (cotações aproximadas; atualizadas via API em tempo real)
    "BTC":  "0.0000094",
    "ETH":  "0.00026",
    "SOL":  "0.0054",
    "ADA":  "1.09",
    "XRP":  "1.82",
    "DOGE": "0.16",
    "USDT": "1.0",
    "USDC": "1.0",
    "BNB":  "0.0016",
    "TRX":  "8.93",
    "AVAX": "0.041",
    "MATIC":"1.02",
    "DAI":  "1.0",
}

# Conjunto de símbolos reconhecidos como criptoativos
_CRYPTO_SYMBOLS = frozenset({
    "BTC", "ETH", "SOL", "ADA", "XRP", "DOGE",
    "USDT", "USDC", "BNB", "TRX", "AVAX", "MATIC", "DAI",
})


# ---------------------------------------------------------------------------
# _RateCache — cache somente em memória
# ---------------------------------------------------------------------------

class _RateCache:
    """Cache de taxas de câmbio somente em memória."""

    def __init__(self) -> None:
        self._rates: Dict[str, BigDecimal] = {}
        self._base: str = "USD"
        self._fetched_at: Optional[float] = None
        self._max_age_seconds: float = 3600.0  # 1 hora padrão

    def set_max_age(self, hours: float) -> None:
        self._max_age_seconds = hours * 3600.0

    def is_valid(self) -> bool:
        if not self._rates or self._fetched_at is None:
            return False
        return (time.time() - self._fetched_at) < self._max_age_seconds

    def store(self, rates: Dict[str, BigDecimal], base: str = "USD") -> None:
        self._rates = rates
        self._base = base
        self._fetched_at = time.time()

    def get_rates(self) -> Dict[str, BigDecimal]:
        return self._rates

    def get_base(self) -> str:
        return self._base

    def invalidate(self) -> None:
        """Descarta o cache em memória."""
        self._rates = {}
        self._fetched_at = None


_cache = _RateCache()


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _to_bigdecimal(value: Any) -> BigDecimal:
    """Converte qualquer valor numérico aceito para BigDecimal."""
    if isinstance(value, BigDecimal):
        return value
    if isinstance(value, _NumericBase):
        return BigDecimal(str(value.value()))
    return BigDecimal(str(value))


def _log_conversion(frm: str, to: str, amount: BigDecimal, result: BigDecimal) -> None:
    """Registra conversão em memória (log simples para stdout quando ativo)."""
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    print(f"[money] {ts} | {amount} {frm} → {result} {to}")


# ---------------------------------------------------------------------------
# Money v2
# ---------------------------------------------------------------------------

class Money:
    """
    Valor monetário com precisão arbitrária (BigDecimal internamente).

    Suporta moedas fiduciárias e criptoativos.
    Cache somente em memória (sem escrita em disco).

    Dependências HTTP (em ordem de preferência):
      1. NestifyPy Net  (arkhe.net)
      2. requests       (pip install requests)
      3. urllib         (stdlib — sempre disponível)

    ::

        Money("19.99", "USD")
        Money(100, Currency.BRL)
        Money("0.5", "BTC")

        Money("100", "USD").multiply("0.17").add(Money("10", "USD"))

        Money(100, "USD").to("BRL")
        Money("0.5", "BTC").to("USD").to("BRL")

        Money(100, "USD") > Money(50, "USD")
        Money(100, "USD") >= Money(500, "BRL")
    """

    _fetcher: Optional[Any] = None
    _log_conversions: bool = False

    # Timeout padrão para requisições HTTP (segundos)
    _HTTP_TIMEOUT: int = 8

    # Número de tentativas em caso de falha de rede
    _HTTP_RETRIES: int = 2

    # APIs de taxas (fiat e crypto separadas)
    _FIAT_API_URL:   str = "https://open.er-api.com/v6/latest/USD"
    _CRYPTO_API_URL: str = "https://api.coingecko.com/api/v3/simple/price"

    # Mapeamento símbolo → id do CoinGecko
    _COINGECKO_IDS: Dict[str, str] = {
        "BTC":   "bitcoin",
        "ETH":   "ethereum",
        "SOL":   "solana",
        "ADA":   "cardano",
        "XRP":   "ripple",
        "DOGE":  "dogecoin",
        "USDT":  "tether",
        "USDC":  "usd-coin",
        "BNB":   "binancecoin",
        "TRX":   "tron",
        "AVAX":  "avalanche-2",
        "MATIC": "matic-network",
        "DAI":   "dai",
    }

    def __init__(
        self,
        amount: Union[str, int, float, Decimal, BigDecimal, "_NumericBase"],
        currency: str,
    ) -> None:
        self._amount: BigDecimal = _to_bigdecimal(amount)
        self._currency: str = currency.upper()

    # ── conversão ─────────────────────────────────────────────────────────

    def to(self, target: str, log: Optional[bool] = None) -> "Money":
        """
        Converte para a moeda alvo.

        ::

            Money(100, "USD").to("BRL")
            Money("0.5", "BTC").to("USD")
            Money("1", "BTC").to("ETH")
        """
        target = target.upper()
        if target == self._currency:
            return Money(self._amount, target)

        rates = self._get_rates()
        from_rate = rates.get(self._currency)
        to_rate   = rates.get(target)

        if from_rate is None:
            raise ValueError(f"Moeda desconhecida: {self._currency!r}")
        if to_rate is None:
            raise ValueError(f"Moeda desconhecida: {target!r}")

        # USD como base intermediária; tudo em BigDecimal
        usd_amount = self._amount.divide(from_rate)
        converted  = usd_amount.multiply(to_rate)

        if log or (log is None and self._log_conversions):
            _log_conversion(self._currency, target, self._amount, converted)

        return Money(converted, target)

    # ── acesso ao valor ───────────────────────────────────────────────────

    def amount(self) -> BigDecimal:
        """Retorna o valor como BigDecimal."""
        return self._amount

    def currency(self) -> str:
        return self._currency

    # ── operações fluentes ────────────────────────────────────────────────

    def add(self, other: "Money") -> "Money":
        """Soma dois valores. O outro é convertido para a moeda deste."""
        converted = other.to(self._currency)
        return Money(self._amount.add(converted._amount), self._currency)

    def subtract(self, other: "Money") -> "Money":
        """Subtrai. O outro é convertido para a moeda deste."""
        converted = other.to(self._currency)
        return Money(self._amount.subtract(converted._amount), self._currency)

    def multiply(self, factor: Union[str, int, float, Decimal, BigDecimal]) -> "Money":
        """Multiplica por um fator escalar."""
        return Money(self._amount.multiply(_to_bigdecimal(factor)), self._currency)

    def divide(self, divisor: Union[str, int, float, Decimal, BigDecimal]) -> "Money":
        """Divide por um divisor escalar."""
        bd = _to_bigdecimal(divisor)
        result = self._amount.divide(bd)
        if isinstance(result, FailureResult):
            return result  # type: ignore[return-value]
        return Money(result, self._currency)

    def ratio(self, other: "Money") -> BigDecimal:
        """
        Retorna a razão entre este e outro valor monetário (ambos na mesma moeda base).

        Útil para ROI, multiplicadores e indicadores financeiros.

        ::

            Money(100, "USD").ratio(Money(25, "USD"))  # BigDecimal("4")
        """
        other_converted = other.to(self._currency)
        return self._amount.divide(other_converted._amount)  # type: ignore[return-value]

    # ── arredondamento ────────────────────────────────────────────────────

    def round(self, places: int = 2) -> "Money":
        """
        ::

            Money("19.999", "USD").round(2)  # Money("20.00", "USD")
        """
        return Money(self._amount.round(places), self._currency)

    def floor(self) -> "Money":
        return Money(self._amount.floor(), self._currency)

    def ceil(self) -> "Money":
        return Money(self._amount.ceil(), self._currency)

    # ── formatação ────────────────────────────────────────────────────────

    def format(self, decimal_places: int = 2, locale: str = "en_US") -> str:
        """
        Formata com símbolo e separadores regionais.

        ::

            Money("1234.56", "USD").format(locale="en_US")   # $1,234.56
            Money("1234.56", "BRL").format(locale="pt_BR")   # R$ 1.234,56
            Money("1234.56", "EUR").format(locale="de_DE")   # 1.234,56 €
        """
        value = self._amount.round(decimal_places).value()
        formatted_number = f"{float(value):.{decimal_places}f}"

        _SYMBOLS: Dict[str, str] = {
            "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
            "BRL": "R$", "CAD": "CA$", "AUD": "A$", "CHF": "Fr",
            "CNY": "¥", "INR": "₹", "KRW": "₩", "RUB": "₽",
            "TRY": "₺", "ILS": "₪", "NGN": "₦", "PKR": "₨",
        }

        _LOCALES: Dict[str, Dict[str, str]] = {
            "en_US": {"thousands": ",",  "decimal": ".", "symbol_pos": "prefix"},
            "en_GB": {"thousands": ",",  "decimal": ".", "symbol_pos": "prefix"},
            "pt_BR": {"thousands": ".",  "decimal": ",", "symbol_pos": "prefix"},
            "de_DE": {"thousands": ".",  "decimal": ",", "symbol_pos": "suffix"},
            "fr_FR": {"thousands": " ",  "decimal": ",", "symbol_pos": "suffix"},
            "es_ES": {"thousands": ".",  "decimal": ",", "symbol_pos": "suffix"},
            "ja_JP": {"thousands": ",",  "decimal": ".", "symbol_pos": "prefix"},
        }

        lc = _LOCALES.get(locale, _LOCALES["en_US"])

        parts = formatted_number.split(".")
        integer_part = parts[0]
        decimal_part = parts[1] if len(parts) > 1 else ""

        groups: List[str] = []
        for i, ch in enumerate(reversed(integer_part)):
            if i > 0 and i % 3 == 0:
                groups.append(lc["thousands"])
            groups.append(ch)
        integer_formatted = "".join(reversed(groups))

        if decimal_places > 0:
            number_str = integer_formatted + lc["decimal"] + decimal_part
        else:
            number_str = integer_formatted

        symbol = _SYMBOLS.get(self._currency, self._currency)

        if lc["symbol_pos"] == "prefix":
            return f"{symbol}{number_str}"
        else:
            return f"{number_str} {symbol}"

    # ── conversões de valor ───────────────────────────────────────────────

    def to_float(self) -> float:
        return self._amount.to_float()

    def to_decimal(self) -> Decimal:
        return self._amount.to_decimal()

    # ── comparações ───────────────────────────────────────────────────────

    def _to_usd_amount(self) -> BigDecimal:
        if self._currency == "USD":
            return self._amount
        return self.to("USD")._amount

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return False
        if self._currency == other._currency:
            return self._amount == other._amount
        try:
            return self._to_usd_amount() == other._to_usd_amount()
        except Exception:
            return False

    def __lt__(self, other: "Money") -> bool:
        if self._currency == other._currency:
            return self._amount < other._amount
        return self._to_usd_amount() < other._to_usd_amount()

    def __le__(self, other: "Money") -> bool:
        return self == other or self < other

    def __gt__(self, other: "Money") -> bool:
        if self._currency == other._currency:
            return self._amount > other._amount
        return self._to_usd_amount() > other._to_usd_amount()

    def __ge__(self, other: "Money") -> bool:
        return self == other or self > other

    def __hash__(self) -> int:
        try:
            usd = self._to_usd_amount()
            return hash(("USD", usd.value()))
        except Exception:
            return hash((self._currency, self._amount.value()))

    # ── operadores Python ─────────────────────────────────────────────────

    def __add__(self, other: "Money") -> "Money":
        return self.add(other)

    def __sub__(self, other: "Money") -> "Money":
        return self.subtract(other)

    def __mul__(self, factor: Union[str, int, float, Decimal]) -> "Money":
        return self.multiply(factor)

    def __rmul__(self, factor: Union[str, int, float, Decimal]) -> "Money":
        return self.multiply(factor)

    def __truediv__(self, divisor: Union[str, int, float, Decimal]) -> "Money":
        return self.divide(divisor)

    # ── repr ──────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"Money({str(self._amount)!r}, {self._currency!r})"

    def __str__(self) -> str:
        return f"{self._amount.round(2)} {self._currency}"

    # ── configuração de classe ────────────────────────────────────────────

    @classmethod
    def cache(cls, hours: float = 1.0) -> None:
        """
        Define o tempo máximo de cache em memória para as taxas de câmbio.

        ::

            Money.cache(hours=12)
        """
        _cache.set_max_age(hours)

    @classmethod
    def set_fetcher(cls, fetcher: Any) -> None:
        """
        Injeta manualmente um cliente HTTP.
        Na maioria dos casos não é necessário — a integração com Net / requests
        é automática.

        ::

            from arkhe.net import request
            Money.set_fetcher(request)
        """
        cls._fetcher = fetcher

    @classmethod
    def set_timeout(cls, seconds: int) -> None:
        """
        Define o timeout (em segundos) para as requisições HTTP.

        ::

            Money.set_timeout(15)
        """
        cls._HTTP_TIMEOUT = seconds

    @classmethod
    def set_retries(cls, retries: int) -> None:
        """
        Define o número de tentativas em caso de falha de rede.

        ::

            Money.set_retries(3)
        """
        cls._HTTP_RETRIES = retries

    @classmethod
    def enable_conversion_log(cls, enabled: bool = True) -> None:
        """
        Ativa o log de conversões no stdout.

        ::

            Money.enable_conversion_log()
        """
        cls._log_conversions = enabled

    @classmethod
    def refresh_rates(cls) -> None:
        """Descarta o cache em memória e busca novas taxas imediatamente."""
        _cache.invalidate()
        cls._get_rates()

    # ── pipeline de taxas ─────────────────────────────────────────────────

    @classmethod
    def _get_rates(cls) -> Dict[str, BigDecimal]:
        # 1. Cache em memória válido → retorna imediatamente
        if _cache.is_valid():
            return _cache.get_rates()

        # 2. Busca online
        try:
            rates = cls._fetch_rates()
        except Exception:
            rates = {}

        # 3. Garante que TODOS os símbolos do fallback estão presentes
        #    (preenche criptos ausentes quando CoinGecko não responde, etc.)
        fallback = {k: BigDecimal(v) for k, v in _FALLBACK_RATES_FROM_USD.items()}
        for symbol, rate in fallback.items():
            rates.setdefault(symbol, rate)

        # 4. Armazena em cache de memória
        _cache.store(rates)
        return rates

    @classmethod
    def _fetch_rates(cls) -> Dict[str, BigDecimal]:
        """
        Busca taxas fiat + crypto. Retorna Dict[str, BigDecimal].

        Pipeline:
          1. Taxas fiat via open.er-api.com  (USD como base)
          2. Taxas crypto via CoinGecko
          3. Criptos ausentes são preenchidos com _FALLBACK_RATES_FROM_USD

        HTTP:
          Usa NestifyPy Net → requests → urllib, nessa ordem de preferência.
        """
        rates: Dict[str, BigDecimal] = {}

        # ── Taxas fiat via open.er-api ────────────────────────────────────
        fiat_data = cls._http_get_json(cls._FIAT_API_URL)
        if fiat_data and "rates" in fiat_data:
            for symbol, rate in fiat_data["rates"].items():
                rates[symbol.upper()] = BigDecimal(str(rate))

        # ── Taxas crypto via CoinGecko ────────────────────────────────────
        ids = ",".join(cls._COINGECKO_IDS.values())
        crypto_url = (
            f"{cls._CRYPTO_API_URL}"
            f"?ids={ids}&vs_currencies=usd"
        )
        crypto_data = cls._http_get_json(crypto_url)
        if crypto_data:
            id_to_symbol = {v: k for k, v in cls._COINGECKO_IDS.items()}
            for cg_id, price_info in crypto_data.items():
                symbol = id_to_symbol.get(cg_id)
                if symbol and "usd" in price_info:
                    price_usd = BigDecimal(str(price_info["usd"]))
                    if price_usd.value() != 0:
                        # Taxa = 1 / preço (quantas moedas por 1 USD)
                        rates[symbol] = BigDecimal("1").divide(price_usd)  # type: ignore[assignment]

        # ── Preenche criptos ausentes com fallback ────────────────────────
        for symbol in _CRYPTO_SYMBOLS:
            if symbol not in rates and symbol in _FALLBACK_RATES_FROM_USD:
                rates[symbol] = BigDecimal(_FALLBACK_RATES_FROM_USD[symbol])

        if not rates:
            raise ValueError("Não foi possível obter taxas de nenhuma fonte.")

        rates["USD"] = BigDecimal("1")
        return rates

    @classmethod
    def _http_get_json(cls, url: str) -> Optional[Dict[str, Any]]:
        """
        Faz GET em *url* e retorna o JSON parseado.

        Ordem de preferência dos clientes HTTP:
          1. Fetcher manual (Money.set_fetcher)
          2. NestifyPy Net (arkhe.net.request)
          3. requests      (pip install requests)
          4. urllib        (stdlib)

        Tenta até _HTTP_RETRIES vezes antes de desistir.
        """
        # ── 1. Fetcher manual ou NestifyPy Net ────────────────────────────
        net_fetcher = cls._fetcher or (_net_request if _HAS_NET else None)
        if net_fetcher is not None:
            for attempt in range(max(1, cls._HTTP_RETRIES)):
                try:
                    response = net_fetcher(url).get()
                    if response.success:
                        return response.json
                except Exception:
                    pass
            return None

        # ── 2. requests ───────────────────────────────────────────────────
        if _HAS_REQUESTS:
            for attempt in range(max(1, cls._HTTP_RETRIES)):
                try:
                    resp = _requests.get(
                        url,
                        timeout=cls._HTTP_TIMEOUT,
                        headers={"Accept": "application/json"},
                    )
                    resp.raise_for_status()
                    return resp.json()
                except Exception:
                    if attempt < cls._HTTP_RETRIES - 1:
                        time.sleep(0.5 * (attempt + 1))
            return None

        # ── 3. urllib (stdlib) ────────────────────────────────────────────
        import urllib.request as _urllib

        for attempt in range(max(1, cls._HTTP_RETRIES)):
            try:
                req = _urllib.Request(url, headers={"Accept": "application/json"})
                with _urllib.urlopen(req, timeout=cls._HTTP_TIMEOUT) as resp:
                    return json.loads(resp.read().decode())
            except Exception:
                if attempt < cls._HTTP_RETRIES - 1:
                    time.sleep(0.5 * (attempt + 1))
        return None


# ---------------------------------------------------------------------------
# CryptoPrice — cotações e market data de criptoativos
# ---------------------------------------------------------------------------

class CryptoPrice:
    """
    Cotação e dados de mercado de um criptoativo.

    ::

        btc = CryptoPrice.of("BTC")
        print(btc.symbol)       # "BTC"
        print(btc.price_usd)    # BigDecimal("105432.22")
        print(btc.updated_at)   # timestamp float

        # Market data (quando disponível via CoinGecko)
        print(btc.market_cap)
        print(btc.volume_24h)
        print(btc.change_24h)
    """

    _DETAIL_URL = "https://api.coingecko.com/api/v3/coins/markets"

    def __init__(
        self,
        symbol:     str,
        price_usd:  BigDecimal,
        market_cap: Optional[BigDecimal] = None,
        volume_24h: Optional[BigDecimal] = None,
        change_24h: Optional[BigDecimal] = None,
        updated_at: Optional[float] = None,
    ) -> None:
        self._symbol     = symbol.upper()
        self._price_usd  = price_usd
        self._market_cap = market_cap
        self._volume_24h = volume_24h
        self._change_24h = change_24h
        self._updated_at = updated_at or time.time()

    @classmethod
    def of(cls, symbol: str) -> "CryptoPrice":
        """
        Obtém a cotação atual de um criptoativo.

        ::

            CryptoPrice.of("BTC")
            CryptoPrice.of("ETH")
        """
        symbol = symbol.upper()
        cg_id  = Money._COINGECKO_IDS.get(symbol)
        if cg_id is None:
            raise ValueError(
                f"Criptoativo não suportado: {symbol!r}. "
                f"Suportados: {sorted(Money._COINGECKO_IDS)}"
            )

        url  = f"{cls._DETAIL_URL}?vs_currency=usd&ids={cg_id}"
        data = Money._http_get_json(url)

        if data and isinstance(data, list) and len(data) > 0:
            coin      = data[0]
            price     = BigDecimal(str(coin.get("current_price",  0)))
            mkt_cap   = BigDecimal(str(coin.get("market_cap",     0))) if coin.get("market_cap")   else None
            vol       = BigDecimal(str(coin.get("total_volume",   0))) if coin.get("total_volume") else None
            change    = BigDecimal(str(coin.get("price_change_percentage_24h", 0)))
            return cls(symbol, price, mkt_cap, vol, change)

        # Fallback via taxas em cache
        rates = Money._get_rates()
        rate  = rates.get(symbol)
        if rate is None:
            raise ValueError(f"Não foi possível obter cotação para {symbol!r}.")
        price_usd: Any = BigDecimal("1").divide(rate)
        return cls(
            symbol,
            price_usd if not isinstance(price_usd, FailureResult) else BigDecimal("0"),
        )

    # ── propriedades ──────────────────────────────────────────────────────

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def price_usd(self) -> BigDecimal:
        return self._price_usd

    @property
    def market_cap(self) -> Optional[BigDecimal]:
        return self._market_cap

    @property
    def volume_24h(self) -> Optional[BigDecimal]:
        return self._volume_24h

    @property
    def change_24h(self) -> Optional[BigDecimal]:
        return self._change_24h

    @property
    def updated_at(self) -> float:
        return self._updated_at

    def as_money(self) -> Money:
        """Retorna a cotação como Money(price_usd, 'USD')."""
        return Money(self._price_usd, "USD")

    def __repr__(self) -> str:
        return (
            f"CryptoPrice(symbol={self._symbol!r}, "
            f"price_usd={self._price_usd!r})"
        )

    def __str__(self) -> str:
        return f"{self._symbol}: ${self._price_usd.round(2)} USD"


# ---------------------------------------------------------------------------
# Portfolio — carteira de ativos multi-moeda
# ---------------------------------------------------------------------------

class Portfolio:
    """
    Carteira de ativos com suporte a múltiplas moedas e criptoativos.

    ::

        portfolio = Portfolio()
        portfolio.add(Money("0.5",  "BTC"))
        portfolio.add(Money("10",   "ETH"))
        portfolio.add(Money("1000", "USDT"))

        portfolio.total("USD")   # Money total em USD
        portfolio.total("BRL")   # Money total em BRL
    """

    def __init__(self) -> None:
        self._positions: List[Money] = []

    def add(self, money: Money) -> "Portfolio":
        """Adiciona uma posição ao portfolio. Retorna self para encadeamento."""
        self._positions.append(money)
        return self

    def remove(self, money: Money) -> "Portfolio":
        """Remove uma posição do portfolio (primeira ocorrência igual)."""
        for i, pos in enumerate(self._positions):
            if pos.currency() == money.currency() and pos.amount() == money.amount():
                self._positions.pop(i)
                break
        return self

    def total(self, target_currency: str = "USD") -> Money:
        """
        Retorna o valor total do portfolio convertido para a moeda alvo.

        ::

            portfolio.total("USD")
            portfolio.total("BRL")
        """
        target = target_currency.upper()
        accumulator = Money("0", target)
        for position in self._positions:
            converted = position.to(target)
            accumulator = accumulator.add(converted)
        return accumulator

    def positions(self) -> List[Money]:
        """Lista todas as posições."""
        return list(self._positions)

    def summary(self, target_currency: str = "USD") -> str:
        """Retorna um resumo textual do portfolio."""
        lines = ["Portfolio:"]
        for pos in self._positions:
            converted = pos.to(target_currency)
            lines.append(
                f"  {pos.amount().round(8)} {pos.currency()} "
                f"≈ {converted.round(2)}"
            )
        lines.append(f"  Total: {self.total(target_currency).round(2)}")
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._positions)

    def __repr__(self) -> str:
        return f"Portfolio({len(self._positions)} posições)"


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = [
    "Money",
    "Currency",
    "CryptoPrice",
    "Portfolio",
]
