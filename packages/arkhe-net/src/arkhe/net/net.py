"""
arkhe.net
-------------
NestifyPy Net – Cliente HTTP fluente para o ecossistema Arkhe.

API de alto nível inspirada em JavaScript fetch, Kotlin Ktor e Java OkHttp.
Sem dependências externas — usa apenas a stdlib Python (urllib).

Exemplo rápido
--------------
::

    from arkhe.net import request, API

    # GET simples
    r = request("https://api.github.com/users/octocat").get()
    if r.success:
        print(r.json)

    # POST com JSON
    r = (
        request("https://api.example.com/users")
        .auth_bearer(token)
        .json({"name": "Alice"})
        .timeout(10)
        .retry(3)
        .post()
    )

    # Sessão reutilizável
    api = API("https://api.example.com").auth_bearer(token)
    users  = api.get("/users").json
    orders = api.get("/orders").json

Integração com Promise
----------------------
::

    request(url).async_get() \\
                .then(lambda r: print(r.json)) \\
                .catch(print)

Integração com Try
------------------
::

    Try.of(lambda: request(url).expect(200).get()) \\
       .map(lambda r: r.json) \\
       .recover(lambda ex: {}) \\
       .on_success(print)
"""

from __future__ import annotations

import base64
import hashlib
import json as _json_mod
import mimetypes
import os
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from http.cookiejar import CookieJar
from pathlib import Path
from typing import (
    Any, Callable, Dict, List, Optional,
    Tuple, Type, Union, TypeVar
)

T = TypeVar("T")


# ─────────────────────────────────────────────────────────────────────────────
#  Excepções
# ─────────────────────────────────────────────────────────────────────────────

class NetError(Exception):
    """Base exception para erros do arkhe.net."""


class RequestError(NetError):
    """Erro de rede — conexão recusada, DNS, etc."""

    def __init__(self, message: str, cause: Optional[BaseException] = None) -> None:
        super().__init__(message)
        self.cause = cause


class TimeoutError(NetError):
    """Pedido excedeu o timeout configurado."""


class UnexpectedStatusError(NetError):
    """
    Lançado por ``.expect()`` quando o status não bate com os esperados.
    Contém a Response para inspeção.
    """

    def __init__(self, response: "Response", expected: Tuple[int, ...]) -> None:
        self.response = response
        self.expected = expected
        super().__init__(
            f"Expected status {expected}, got {response.status} — {response.url}"
        )


class DownloadError(NetError):
    """Erro durante download de ficheiro."""


class UploadError(NetError):
    """Erro durante upload de ficheiro."""


# ─────────────────────────────────────────────────────────────────────────────
#  Cache
# ─────────────────────────────────────────────────────────────────────────────

class _CacheEntry:
    __slots__ = ("data", "expires_at")

    def __init__(self, data: bytes, ttl_seconds: float) -> None:
        self.data       = data
        self.expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

    def is_valid(self) -> bool:
        return datetime.now() < self.expires_at


class _MemoryCache:
    """Cache em memória thread-safe por URL+método."""

    def __init__(self) -> None:
        self._store: Dict[str, _CacheEntry] = {}
        self._lock  = threading.Lock()

    def get(self, key: str) -> Optional[bytes]:
        with self._lock:
            entry = self._store.get(key)
            if entry and entry.is_valid():
                return entry.data
            if entry:
                del self._store[key]
        return None

    def set(self, key: str, data: bytes, ttl_seconds: float) -> None:
        with self._lock:
            self._store[key] = _CacheEntry(data, ttl_seconds)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


class _DiskCache:
    """Cache persistente em disco (ficheiros .cache)."""

    def __init__(self, directory: Union[str, Path] = ".arkhe/cache") -> None:
        self._dir = Path(directory)

    def _path(self, key: str) -> Path:
        h = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self._dir / f"{h}.cache"

    def get(self, key: str) -> Optional[bytes]:
        p = self._path(key)
        if not p.exists():
            return None
        try:
            with open(p, "rb") as fh:
                raw = fh.read()
            # Formato: 8 bytes big-endian timestamp + dados
            expires_ts = int.from_bytes(raw[:8], "big") / 1000.0
            if time.time() > expires_ts:
                p.unlink(missing_ok=True)
                return None
            return raw[8:]
        except (OSError, ValueError):
            return None

    def set(self, key: str, data: bytes, ttl_seconds: float) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        p = self._path(key)
        expires_ms = int((time.time() + ttl_seconds) * 1000)
        try:
            with open(p, "wb") as fh:
                fh.write(expires_ms.to_bytes(8, "big") + data)
        except OSError:
            pass

    def clear(self) -> None:
        for f in self._dir.glob("*.cache"):
            f.unlink(missing_ok=True)


# Instâncias globais
_mem_cache  = _MemoryCache()
_disk_cache = _DiskCache()


# ─────────────────────────────────────────────────────────────────────────────
#  Response
# ─────────────────────────────────────────────────────────────────────────────

class Response:
    """
    Representa a resposta HTTP de um pedido.

    Atributos
    ---------
    status : int
        Código HTTP (200, 404, 500 …).
    success : bool
        True se 200 ≤ status < 300.
    ok : bool
        Alias de ``success``.
    error : bool
        True se o pedido falhou com uma excepção (sem chegar ao servidor).
    exception : Optional[BaseException]
        Excepção capturada, se ``error`` for True.
    json : Any
        Corpo deserializado como JSON (None se inválido).
    text : str
        Corpo como texto UTF-8.
    bytes : bytes
        Corpo em bytes brutos.
    headers : Dict[str, str]
        Headers da resposta.
    cookies : Dict[str, str]
        Cookies extraídos dos headers.
    url : str
        URL final (após redirects).
    elapsed_ms : float
        Tempo de execução em milissegundos.
    """

    def __init__(
        self,
        status:     int,
        body:       bytes,
        headers:    Dict[str, str],
        url:        str,
        elapsed_ms: float,
        exception:  Optional[BaseException] = None,
    ) -> None:
        self._status    = status
        self._body      = body
        self._headers   = headers
        self._url       = url
        self._elapsed   = elapsed_ms
        self._exception = exception

    # ── propriedades ──────────────────────────────────────────────────────────

    @property
    def status(self) -> int:
        return self._status

    @property
    def success(self) -> bool:
        return self.is_success

    @property
    def is_success(self) -> bool:
        return 200 <= self._status < 300

    @property
    def is_redirect(self) -> bool:
        return 300 <= self._status < 400

    @property
    def is_client_error(self) -> bool:
        return 400 <= self._status < 500

    @property
    def is_server_error(self) -> bool:
        return 500 <= self._status < 600

    @property
    def ok(self) -> bool:
        return self.success

    @property
    def error(self) -> bool:
        return self._exception is not None

    @property
    def exception(self) -> Optional[BaseException]:
        return self._exception

    @property
    def json(self) -> Any:
        try:
            return _json_mod.loads(self._body.decode("utf-8", errors="replace"))
        except (_json_mod.JSONDecodeError, UnicodeDecodeError):
            return None

    @property
    def text(self) -> str:
        return self._body.decode("utf-8", errors="replace")

    @property
    def bytes(self) -> bytes:
        return self._body

    @property
    def headers(self) -> Dict[str, str]:
        return dict(self._headers)

    @property
    def cookies(self) -> Dict[str, str]:
        cookies: Dict[str, str] = {}
        for name, value in self._headers.items():
            if name.lower() == "set-cookie":
                parts = value.split(";")[0].strip()
                if "=" in parts:
                    k, v = parts.split("=", 1)
                    cookies[k.strip()] = v.strip()
        return cookies

    @property
    def url(self) -> str:
        return self._url

    @property
    def elapsed_ms(self) -> float:
        return self._elapsed

    # ── helpers ───────────────────────────────────────────────────────────────

    def raise_for_status(self) -> "Response":
        """Lança UnexpectedStatusError se status >= 400."""
        if self._status >= 400:
            raise UnexpectedStatusError(self, ())
        return self

    def into(self, cls: Type[T]) -> T:
        """
        Converte o corpo JSON diretamente num objecto Python tipado,
        usando a engine `arkhe.json`.
        """
        data = self.json
        if data is None:
            raise NetError(f"Cannot convert non-JSON response into {cls}")
            
        try:
            from arkhe.json import Json
            return Json.from_dict(data, cls)
        except ImportError:
            raise ImportError(
                "arkhe.json is required to use Response.into(). "
                "Ensure arkhe.json is available in your environment."
            )

    def __repr__(self) -> str:
        flag = "✓" if self.success else "✗"
        return f"Response({flag} {self._status}, url={self._url!r}, {self._elapsed:.0f}ms)"

    def __bool__(self) -> bool:
        return self.success


# ─────────────────────────────────────────────────────────────────────────────
#  Request builder
# ─────────────────────────────────────────────────────────────────────────────

class Request:
    """
    Builder fluente para construir e executar pedidos HTTP.

    Não instanciar directamente — use a função :func:`request`.

    ::

        r = (
            request("https://api.example.com/users")
            .auth_bearer(token)
            .json({"name": "Alice"})
            .timeout(10)
            .retry(3)
            .expect(200, 201)
            .post()
        )
    """

    def __init__(self, url: str) -> None:
        self._url              = url
        self._headers:         Dict[str, str]             = {}
        self._params:          Dict[str, Any]             = {}
        self._body:            Optional[bytes]            = None
        self._content_type:    Optional[str]              = None
        self._timeout_s:       float                      = 30.0
        self._retry_attempts:  int                        = 0
        self._retry_delay:     float                      = 0.5
        self._retry_exp:       bool                       = False
        self._cache_ttl:       Optional[float]            = None
        self._cache_disk:      bool                       = False
        self._expected_status: Optional[Tuple[int, ...]] = None
        self._follow_redirects: bool                      = True
        self._verify_ssl:      bool                       = True

        # Multipart
        self._is_multipart:    bool                       = False
        self._multipart_fields: Dict[str, str]            = {}
        self._multipart_files: Dict[str, Path]            = {}

        # Hooks
        self._on_success_cbs:  List[Callable[["Response"], Any]] = []
        self._on_error_cbs:    List[Callable[[BaseException], Any]] = []
        self._on_timeout_cbs:  List[Callable[[], Any]] = []
        self._status_hooks:    Dict[int, List[Callable[["Response"], Any]]] = {}

        # Interceptors
        self._req_interceptors: List[Callable[["Request"], None]] = []
        self._resp_interceptors: List[Callable[["Response"], None]] = []

    # ── headers ───────────────────────────────────────────────────────────────

    def header(self, name: str, value: str) -> "Request":
        """Adiciona um header individual."""
        self._headers[name] = value
        return self

    def headers(self, headers: Dict[str, str]) -> "Request":
        """Adiciona múltiplos headers de uma vez."""
        self._headers.update(headers)
        return self

    # ── autenticação ──────────────────────────────────────────────────────────

    def auth_bearer(self, token: str) -> "Request":
        """Adiciona header ``Authorization: Bearer <token>``."""
        return self.header("Authorization", f"Bearer {token}")

    def auth_basic(self, username: str, password: str) -> "Request":
        """Adiciona header de Basic Authentication."""
        encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
        return self.header("Authorization", f"Basic {encoded}")

    def api_key(self, header_name: str, key: str) -> "Request":
        """Adiciona uma chave de API como header personalizado."""
        return self.header(header_name, key)

    # ── parâmetros de query ───────────────────────────────────────────────────

    def param(self, name: str, value: Any) -> "Request":
        """Adiciona um query parameter."""
        self._params[name] = str(value)
        return self

    def params(self, params: Dict[str, Any]) -> "Request":
        """Adiciona múltiplos query parameters."""
        self._params.update({k: str(v) for k, v in params.items()})
        return self

    # ── corpo do pedido ───────────────────────────────────────────────────────

    def json(self, data: Any) -> "Request":
        """
        Define o corpo como JSON serializado.
        Adiciona automaticamente ``Content-Type: application/json``.
        """
        self._body         = _json_mod.dumps(data, ensure_ascii=False).encode("utf-8")
        self._content_type = "application/json"
        return self

    def form(self, data: Dict[str, Any]) -> "Request":
        """
        Define o corpo como form URL-encoded.
        Adiciona automaticamente ``Content-Type: application/x-www-form-urlencoded``.
        """
        self._body         = urllib.parse.urlencode(data).encode("utf-8")
        self._content_type = "application/x-www-form-urlencoded"
        return self

    def body(self, raw: Union[str, bytes], content_type: str = "text/plain") -> "Request":
        """Define o corpo como bytes ou string bruta."""
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        self._body         = raw
        self._content_type = content_type
        return self

    # ── multipart ─────────────────────────────────────────────────────────────

    def multipart(self) -> "Request":
        """Prepara o request para envio multipart/form-data."""
        self._is_multipart = True
        return self

    def field(self, name: str, value: Any) -> "Request":
        """Adiciona um campo de formulário multipart."""
        self.multipart()
        self._multipart_fields[name] = str(value)
        return self

    def file(self, name: str, path: Union[str, Path]) -> "Request":
        """Adiciona um ficheiro para upload multipart."""
        self.multipart()
        self._multipart_files[name] = Path(path)
        return self

    def _build_multipart_body(self) -> None:
        """Constrói o payload multipart internamente."""
        import secrets
        boundary = secrets.token_hex(16)
        lines: List[bytes] = []

        # Campos normais
        for name, value in self._multipart_fields.items():
            lines.append(f"--{boundary}".encode("utf-8"))
            lines.append(f'Content-Disposition: form-data; name="{name}"'.encode("utf-8"))
            lines.append(b"")
            lines.append(value.encode("utf-8"))

        # Ficheiros
        for name, path in self._multipart_files.items():
            if not path.exists():
                raise UploadError(f"File not found for upload: {path}")
            
            filename = path.name
            mime_type, _ = mimetypes.guess_type(str(path))
            if mime_type is None:
                mime_type = "application/octet-stream"

            lines.append(f"--{boundary}".encode("utf-8"))
            lines.append(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode("utf-8"))
            lines.append(f'Content-Type: {mime_type}'.encode("utf-8"))
            lines.append(b"")
            try:
                lines.append(path.read_bytes())
            except OSError as exc:
                raise UploadError(f"Failed to read file {path}: {exc}") from exc

        lines.append(f"--{boundary}--".encode("utf-8"))
        lines.append(b"")

        self._body = b"\r\n".join(lines)
        self._content_type = f"multipart/form-data; boundary={boundary}"

    # ── comportamento ─────────────────────────────────────────────────────────

    def timeout(self, seconds: float) -> "Request":
        """Define o timeout do pedido em segundos."""
        self._timeout_s = seconds
        return self

    def retry(
        self,
        attempts: int = 3,
        delay: float = 0.5,
        exponential: bool = False,
    ) -> "Request":
        """
        Repete o pedido em caso de falha de rede ou status >= 500.

        Parameters
        ----------
        attempts:
            Número máximo de tentativas (total, incluindo a primeira).
        delay:
            Segundos de espera entre tentativas.
        exponential:
            Se True, duplica o delay a cada tentativa (backoff exponencial).
        """
        self._retry_attempts = attempts
        self._retry_delay    = delay
        self._retry_exp      = exponential
        return self

    def cache(
        self,
        minutes: float = 5,
        persistent: bool = False,
    ) -> "Request":
        """
        Activa cache para este pedido GET.

        Parameters
        ----------
        minutes:
            TTL da cache em minutos.
        persistent:
            Se True, usa cache em disco entre sessões.
        """
        self._cache_ttl  = minutes * 60
        self._cache_disk = persistent
        return self

    def no_redirect(self) -> "Request":
        """Não segue redirects automaticamente."""
        self._follow_redirects = False
        return self

    def no_ssl_verify(self) -> "Request":
        """Desactiva verificação do certificado SSL (não usar em produção)."""
        self._verify_ssl = False
        return self

    def expect(self, *statuses: int) -> "Request":
        """
        Lança :exc:`UnexpectedStatusError` se o status não estiver em ``statuses``.

        ::

            request(url).expect(200, 201).post()
        """
        self._expected_status = statuses
        return self

    # ── hooks ─────────────────────────────────────────────────────────────────

    def on_success(self, fn: Callable[["Response"], Any]) -> "Request":
        """Callback executado se o pedido for bem-sucedido (2xx)."""
        self._on_success_cbs.append(fn)
        return self

    def on_error(self, fn: Callable[[BaseException], Any]) -> "Request":
        """Callback executado em caso de excepção de rede."""
        self._on_error_cbs.append(fn)
        return self

    def on_timeout(self, fn: Callable[[], Any]) -> "Request":
        """Callback executado especificamente em caso de timeout."""
        self._on_timeout_cbs.append(fn)
        return self

    def if_status(self, status: int, fn: Callable[["Response"], Any]) -> "Request":
        """
        Executa ``fn`` se o status da resposta for ``status``.

        ::

            request(url)
                .if_status(200, lambda r: process(r.json))
                .if_status(404, lambda r: log_missing())
                .get()
        """
        self._status_hooks.setdefault(status, []).append(fn)
        return self

    # ── execução ──────────────────────────────────────────────────────────────

    def get(self) -> Response:
        """Executa um pedido GET."""
        return self._execute("GET")

    def post(self) -> Response:
        """Executa um pedido POST."""
        return self._execute("POST")

    def put(self) -> Response:
        """Executa um pedido PUT."""
        return self._execute("PUT")

    def patch(self) -> Response:
        """Executa um pedido PATCH."""
        return self._execute("PATCH")

    def delete(self) -> Response:
        """Executa um pedido DELETE."""
        return self._execute("DELETE")

    def head(self) -> Response:
        """Executa um pedido HEAD."""
        return self._execute("HEAD")

    def options(self) -> Response:
        """Executa um pedido OPTIONS."""
        return self._execute("OPTIONS")

    # ── async (integração Promise) ────────────────────────────────────────────

    def async_get(self) -> Any:
        """Executa GET de forma assíncrona. Retorna ``Promise[Response]``."""
        return self._async_execute("GET")

    def async_post(self) -> Any:
        """Executa POST de forma assíncrona. Retorna ``Promise[Response]``."""
        return self._async_execute("POST")

    def async_put(self) -> Any:
        """Executa PUT de forma assíncrona. Retorna ``Promise[Response]``."""
        return self._async_execute("PUT")

    def async_delete(self) -> Any:
        """Executa DELETE de forma assíncrona. Retorna ``Promise[Response]``."""
        return self._async_execute("DELETE")

    def async_patch(self) -> Any:
        """Executa PATCH de forma assíncrona. Retorna ``Promise[Response]``."""
        return self._async_execute("PATCH")

    def _async_execute(self, method: str) -> Any:
        """Executa o pedido numa thread e retorna uma Promise."""
        try:
            from arkhe.promise import Promise  # type: ignore[import]
        except ImportError:
            try:
                import sys, os as _os
                sys.path.insert(0, _os.path.dirname(__file__))
                from promise import Promise  # type: ignore[import]
            except ImportError:
                raise ImportError(
                    "arkhe.promise não encontrado. "
                    "Coloque promise.py no mesmo diretório ou instale arkhe-promise."
                )
        return Promise.of(lambda m=method: self._execute(m))

    # ── download ──────────────────────────────────────────────────────────────

    def download(self, dest: Union[str, Path]) -> Response:
        """
        Faz GET e guarda o corpo em ``dest``.

        ::

            request("https://example.com/file.zip").download("file.zip")
        """
        r = self._execute("GET")
        if r.success:
            path = Path(dest)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(r.bytes)
        return r

    def save(self, dest: Union[str, Path]) -> Response:
        """Alias de :meth:`download`."""
        return self.download(dest)

    # ── internos ──────────────────────────────────────────────────────────────

    def _build_url(self) -> str:
        if not self._params:
            return self._url
        sep   = "&" if "?" in self._url else "?"
        query = urllib.parse.urlencode(self._params)
        return f"{self._url}{sep}{query}"

    def _cache_key(self, method: str) -> str:
        return hashlib.md5(f"{method}:{self._build_url()}".encode()).hexdigest()

    def _get_cached(self, method: str) -> Optional[bytes]:
        if self._cache_ttl is None or method != "GET":
            return None
        key = self._cache_key(method)
        if self._cache_disk:
            return _disk_cache.get(key)
        return _mem_cache.get(key)

    def _set_cached(self, method: str, data: bytes) -> None:
        if self._cache_ttl is None or method != "GET":
            return
        key = self._cache_key(method)
        if self._cache_disk:
            _disk_cache.set(key, data, self._cache_ttl)
        else:
            _mem_cache.set(key, data, self._cache_ttl)

    def _execute(self, method: str) -> Response:
        """Executa o pedido com retry, cache e hooks."""
        # Cache hit
        cached = self._get_cached(method)
        if cached is not None:
            # Recria uma Response a partir dos bytes cacheados
            cached_data = _json_mod.loads(cached)
            resp = Response(
                status     = cached_data["status"],
                body       = base64.b64decode(cached_data["body"]),
                headers    = cached_data["headers"],
                url        = cached_data["url"],
                elapsed_ms = 0.0,
            )
            self._fire_hooks(resp, None)
            return resp

        attempts = max(1, self._retry_attempts)
        delay    = self._retry_delay
        last_resp: Optional[Response] = None
        last_exc:  Optional[BaseException] = None

        for attempt in range(attempts):
            resp, exc = self._do_request(method)

            if exc is not None:
                last_exc = exc
                # Verifica se deve tentar novamente
                if attempt < attempts - 1:
                    if self._retry_exp:
                        time.sleep(delay)
                        delay *= 2
                    else:
                        time.sleep(delay)
                    continue
                # Esgotou tentativas com excepção
                err_resp = Response(
                    status=0, body=b"", headers={},
                    url=self._build_url(), elapsed_ms=0.0,
                    exception=exc,
                )
                self._fire_hooks(err_resp, exc)
                return err_resp

            last_resp = resp
            # Retry em 5xx
            if resp.status >= 500 and attempt < attempts - 1:
                if self._retry_exp:
                    time.sleep(delay); delay *= 2
                else:
                    time.sleep(delay)
                continue

            # Guarda em cache se bem-sucedido
            if resp.success:
                cache_payload = _json_mod.dumps({
                    "status":  resp.status,
                    "body":    base64.b64encode(resp.bytes).decode(),
                    "headers": resp.headers,
                    "url":     resp.url,
                }).encode()
                self._set_cached(method, cache_payload)

            # Validação de status esperado
            if self._expected_status and resp.status not in self._expected_status:
                exc = UnexpectedStatusError(resp, self._expected_status)
                for cb in self._on_error_cbs:
                    _safe_call(cb, exc)
                raise exc

            self._fire_hooks(resp, None)
            return resp

        # Se chegou aqui, esgotou tentativas com resp >= 500
        if last_resp is not None:
            if self._expected_status and last_resp.status not in self._expected_status:
                exc = UnexpectedStatusError(last_resp, self._expected_status)
                raise exc
            self._fire_hooks(last_resp, None)
            return last_resp

        err_resp = Response(
            status=0, body=b"", headers={},
            url=self._build_url(), elapsed_ms=0.0,
            exception=last_exc,
        )
        self._fire_hooks(err_resp, last_exc)
        return err_resp

    def _do_request(self, method: str) -> Tuple[Optional[Response], Optional[BaseException]]:
        """Executa uma única tentativa HTTP."""
        for interceptor in self._req_interceptors:
            interceptor(self)

        if self._is_multipart:
            self._build_multipart_body()

        url = self._build_url()
        t0  = time.perf_counter()

        # Monta headers
        hdrs = dict(self._headers)
        if self._content_type:
            hdrs["Content-Type"] = self._content_type
        if "Accept" not in hdrs:
            hdrs["Accept"] = "application/json, text/plain, */*"

        req = urllib.request.Request(
            url    = url,
            data   = self._body,
            headers= hdrs,
            method = method,
        )

        # SSL context
        ssl_ctx: Optional[ssl.SSLContext] = None
        if not self._verify_ssl:
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode    = ssl.CERT_NONE

        # Opener sem redirect automático se necessário
        if self._follow_redirects:
            opener = urllib.request.build_opener()
        else:
            class _NoRedirect(urllib.request.HTTPErrorProcessor):
                def http_response(self, request, response):  # type: ignore[override]
                    return response
                https_response = http_response
            opener = urllib.request.build_opener(_NoRedirect)

        try:
            kwargs: Dict[str, Any] = {"timeout": self._timeout_s}
            if ssl_ctx:
                kwargs["context"] = ssl_ctx

            with opener.open(req, **kwargs) as resp:  # type: ignore[arg-type]
                body    = resp.read()
                status  = resp.status
                raw_hdrs= dict(resp.headers)
                final_url = resp.url

            elapsed = (time.perf_counter() - t0) * 1000
            resp = Response(
                status     = status,
                body       = body,
                headers    = raw_hdrs,
                url        = final_url,
                elapsed_ms = elapsed,
            )
            for interceptor in self._resp_interceptors:
                interceptor(resp)
            return resp, None

        except urllib.error.HTTPError as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            try:
                body = exc.read()
            except Exception:
                body = b""
            resp = Response(
                status     = exc.code,
                body       = body,
                headers    = dict(exc.headers) if exc.headers else {},
                url        = url,
                elapsed_ms = elapsed,
            )
            for interceptor in self._resp_interceptors:
                interceptor(resp)
            return resp, None

        except urllib.error.URLError as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            reason  = exc.reason
            if isinstance(reason, (TimeoutError, OSError)) or "timed out" in str(reason).lower():
                to_exc = TimeoutError(f"Request timed out after {self._timeout_s}s — {url}")
                for cb in self._on_timeout_cbs:
                    _safe_call(cb)
                return None, to_exc  # type: ignore[return-value]
            net_exc = RequestError(f"Network error: {reason}", cause=exc)
            return None, net_exc  # type: ignore[return-value]

        except OSError as exc:
            if "timed out" in str(exc).lower():
                to_exc = TimeoutError(f"Request timed out after {self._timeout_s}s — {url}")
                for cb in self._on_timeout_cbs:
                    _safe_call(cb)
                return None, to_exc  # type: ignore[return-value]
            return None, RequestError(str(exc), cause=exc)  # type: ignore[return-value]

    def _fire_hooks(self, resp: Response, exc: Optional[BaseException]) -> None:
        if exc is not None:
            for cb in self._on_error_cbs:
                _safe_call(cb, exc)
        elif resp.success:
            for cb in self._on_success_cbs:
                _safe_call(cb, resp)
        # Status-based hooks
        if resp.status in self._status_hooks:
            for cb in self._status_hooks[resp.status]:
                _safe_call(cb, resp)


def _safe_call(fn: Callable, *args: Any) -> Any:
    try:
        return fn(*args)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  API  (sessão reutilizável)
# ─────────────────────────────────────────────────────────────────────────────

class API:
    """
    Sessão HTTP reutilizável com base URL e headers padrão partilhados.

    ::

        api = (
            API("https://api.github.com")
            .auth_bearer(token)
            .header("Accept", "application/vnd.github.v3+json")
            .timeout(10)
        )

        users = api.get("/users/octocat").json
        repos = api.get("/users/octocat/repos").json

        api.post("/repos", json={"name": "my-repo"})
    """

    def __init__(self, base_url: str) -> None:
        self._base_url     = base_url.rstrip("/")
        self._default_hdrs: Dict[str, str]  = {}
        self._default_to:   float           = 30.0
        self._default_retry: int            = 0
        self._default_retry_delay: float    = 0.5
        self._req_interceptors: List[Callable[["Request"], None]] = []
        self._resp_interceptors: List[Callable[["Response"], None]] = []

    # ── configuração da sessão ────────────────────────────────────────────────

    def header(self, name: str, value: str) -> "API":
        """Adiciona um header padrão a todos os pedidos desta sessão."""
        self._default_hdrs[name] = value
        return self

    def headers(self, headers: Dict[str, str]) -> "API":
        """Adiciona múltiplos headers padrão."""
        self._default_hdrs.update(headers)
        return self

    def auth_bearer(self, token: str) -> "API":
        """Define autenticação Bearer para toda a sessão."""
        return self.header("Authorization", f"Bearer {token}")

    def auth_basic(self, username: str, password: str) -> "API":
        """Define autenticação Basic para toda a sessão."""
        encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
        return self.header("Authorization", f"Basic {encoded}")

    def api_key(self, header_name: str, key: str) -> "API":
        return self.header(header_name, key)

    def timeout(self, seconds: float) -> "API":
        """Define timeout padrão para todos os pedidos."""
        self._default_to = seconds
        return self

    def retry(self, attempts: int, delay: float = 0.5) -> "API":
        """Define retry padrão para todos os pedidos."""
        self._default_retry       = attempts
        self._default_retry_delay = delay
        return self

    # ── interceptors ──────────────────────────────────────────────────────────

    def add_interceptor(self, fn: Callable[["Request"], None]) -> "API":
        """Adiciona um interceptor de request executado antes de cada pedido."""
        self._req_interceptors.append(fn)
        return self

    def add_response_interceptor(self, fn: Callable[["Response"], None]) -> "API":
        """Adiciona um interceptor de response executado após receber a resposta."""
        self._resp_interceptors.append(fn)
        return self

    # ── métodos HTTP ──────────────────────────────────────────────────────────

    def _build(self, path: str) -> Request:
        url = self._base_url + ("/" + path.lstrip("/") if path else "")
        req = Request(url)
        req._headers.update(self._default_hdrs)
        req._timeout_s      = self._default_to
        req._retry_attempts = self._default_retry
        req._retry_delay    = self._default_retry_delay
        req._req_interceptors = list(self._req_interceptors)
        req._resp_interceptors = list(self._resp_interceptors)
        return req

    def get(self, path: str = "", **kwargs: Any) -> Response:
        return self._build_with(path, kwargs).get()

    def post(self, path: str = "", json: Any = None, form: Any = None, **kwargs: Any) -> Response:
        req = self._build_with(path, kwargs)
        if json is not None:
            req.json(json)
        elif form is not None:
            req.form(form)
        return req.post()

    def put(self, path: str = "", json: Any = None, **kwargs: Any) -> Response:
        req = self._build_with(path, kwargs)
        if json is not None:
            req.json(json)
        return req.put()

    def patch(self, path: str = "", json: Any = None, **kwargs: Any) -> Response:
        req = self._build_with(path, kwargs)
        if json is not None:
            req.json(json)
        return req.patch()

    def delete(self, path: str = "", **kwargs: Any) -> Response:
        return self._build_with(path, kwargs).delete()

    def request(self, path: str = "") -> Request:
        """Retorna um Request builder com os defaults da sessão aplicados."""
        return self._build(path)

    def _build_with(self, path: str, kwargs: Dict[str, Any]) -> Request:
        req = self._build(path)
        if "params" in kwargs:
            req.params(kwargs["params"])
        if "headers" in kwargs:
            req.headers(kwargs["headers"])
        if "timeout" in kwargs:
            req.timeout(kwargs["timeout"])
        return req

    def __repr__(self) -> str:
        return f"API({self._base_url!r})"


# ─────────────────────────────────────────────────────────────────────────────
#  Função de entrada pública
# ─────────────────────────────────────────────────────────────────────────────

def request(url: str) -> Request:
    """
    Ponto de entrada principal do arkhe.net.

    Retorna um :class:`Request` builder fluente.

    ::

        from arkhe.net import request

        r = request("https://api.example.com/users").get()
        print(r.status, r.json)
    """
    return Request(url)


# ─────────────────────────────────────────────────────────────────────────────
#  Utilitários de cache global
# ─────────────────────────────────────────────────────────────────────────────

def clear_cache() -> None:
    """Limpa toda a cache em memória e em disco."""
    _mem_cache.clear()
    _disk_cache.clear()


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    "request",
    "Request",
    "Response",
    "API",
    "clear_cache",
    "NetError",
    "RequestError",
    "TimeoutError",
    "UnexpectedStatusError",
    "DownloadError",
]
