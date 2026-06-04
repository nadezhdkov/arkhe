"""
tests/test_net.py
-----------------
Suite de testes para arkhe.net.

Cobre:
  - Response (todas as propriedades)
  - Request builder (headers, auth, params, body)
  - Métodos HTTP (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
  - Timeout e hook on_timeout
  - Retry (fixo e exponencial)
  - Cache em memória e em disco
  - Hooks (on_success, on_error, if_status)
  - .expect() e UnexpectedStatusError
  - .no_redirect()
  - .download() / .save()
  - .raise_for_status()
  - API session
  - async_get() → Promise
  - Integração com Try

Execução
--------
::

    pytest tests/test_net.py -v
    pytest tests/test_net.py -v -k "test_get"
    pytest tests/test_net.py --tb=short
"""

from __future__ import annotations

import base64
import json
import os
import tempfile
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

import pytest

# ── importação do módulo ──────────────────────────────────────────────────────
# Suporta tanto o layout de pacote (arkhe.net) como ficheiro solto (net.py)
try:
    from arkhe.net import (
        API,
        Request,
        Response,
        clear_cache,
        request,
    )
    from arkhe.net import (
        DownloadError,
        NetError,
        RequestError,
        UnexpectedStatusError,
    )
    from arkhe.net import TimeoutError as NetTimeoutError
except ModuleNotFoundError:
    from net import (  # type: ignore[no-redef]
        API,
        Request,
        Response,
        clear_cache,
        request,
    )
    from net import (  # type: ignore[no-redef]
        DownloadError,
        NetError,
        RequestError,
        UnexpectedStatusError,
    )
    from net import TimeoutError as NetTimeoutError  # type: ignore[no-redef]


# ─────────────────────────────────────────────────────────────────────────────
#  Servidor HTTP de teste (fixture de sessão)
# ─────────────────────────────────────────────────────────────────────────────

_CALL_COUNTS: Dict[str, int] = {}
_CALL_LOCK = threading.Lock()


def _inc(path: str) -> int:
    with _CALL_LOCK:
        _CALL_COUNTS[path] = _CALL_COUNTS.get(path, 0) + 1
        return _CALL_COUNTS[path]


def _reset_calls() -> None:
    with _CALL_LOCK:
        _CALL_COUNTS.clear()


class _TestHandler(BaseHTTPRequestHandler):
    """Handler HTTP que cobre todos os cenários de teste."""

    def log_message(self, *_: Any) -> None:
        pass  # silencia output no terminal durante os testes

    # ── helpers ───────────────────────────────────────────────────────────────

    def _send(
        self,
        status: int,
        body: bytes | str,
        content_type: str = "application/json",
        extra_headers: Dict[str, str] | None = None,
    ) -> None:
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length)

    def _qs(self) -> Dict[str, str]:
        raw = self.path.split("?", 1)[1] if "?" in self.path else ""
        return {k: v[0] for k, v in urllib.parse.parse_qs(raw).items()}

    def _path(self) -> str:
        return self.path.split("?")[0]

    # ── GET ───────────────────────────────────────────────────────────────────

    def do_GET(self) -> None:
        p = self._path()

        if p == "/ok":
            self._send(200, json.dumps({"status": "ok", "message": "hello"}))

        elif p == "/text":
            self._send(200, "plain text response", "text/plain")

        elif p == "/empty":
            self._send(200, b"", "application/json")

        elif p == "/params":
            self._send(200, json.dumps(self._qs()))

        elif p == "/auth":
            self._send(200, json.dumps({"auth": self.headers.get("Authorization", "")}))

        elif p == "/headers-echo":
            self._send(200, json.dumps({
                "user-agent": self.headers.get("User-Agent", ""),
                "x-custom":   self.headers.get("X-Custom", ""),
                "accept":     self.headers.get("Accept", ""),
            }))

        elif p == "/cookie":
            self._send(200, json.dumps({"ok": True}),
                       extra_headers={"Set-Cookie": "session=abc123; Path=/"})

        elif p == "/204":
            self._send(204, b"")

        elif p == "/400":
            self._send(400, json.dumps({"error": "bad request"}))

        elif p == "/401":
            self._send(401, json.dumps({"error": "unauthorized"}))

        elif p == "/403":
            self._send(403, json.dumps({"error": "forbidden"}))

        elif p == "/404":
            self._send(404, json.dumps({"error": "not found"}))

        elif p == "/500":
            self._send(500, json.dumps({"error": "server error"}))

        elif p == "/503":
            self._send(503, json.dumps({"error": "service unavailable"}))

        elif p == "/slow":
            time.sleep(10)
            self._send(200, json.dumps({"late": True}))

        elif p == "/redirect-target":
            self._send(200, json.dumps({"landed": True}))

        elif p == "/redirect":
            self.send_response(302)
            host = self.headers.get("Host", "localhost:19876")
            self.send_header("Location", f"http://{host}/redirect-target")
            self.end_headers()

        elif p == "/binary":
            self._send(200, b"\x00\x01\x02\x03\xff", "application/octet-stream")

        elif p == "/timestamp":
            # Resposta com timestamp crescente — útil para testar cache
            self._send(200, json.dumps({"ts": time.time()}))

        elif p.startswith("/flaky-500"):
            # Falha nas primeiras N chamadas, depois retorna 200
            n = int(p.split("/flaky-500/")[1]) if "/flaky-500/" in p else 2
            count = _inc(p)
            if count <= n:
                self._send(500, json.dumps({"attempt": count}))
            else:
                self._send(200, json.dumps({"ok": True, "attempts": count}))

        elif p.startswith("/flaky-net"):
            # Fecha a conexão abruptamente nas primeiras chamadas
            count = _inc(p)
            if count <= 1:
                self.connection.close()
                return
            self._send(200, json.dumps({"ok": True}))

        else:
            self._send(404, json.dumps({"error": f"unknown path: {p}"}))

    # ── POST ──────────────────────────────────────────────────────────────────

    def do_POST(self) -> None:
        body = self._read_body()
        ct   = self.headers.get("Content-Type", "")
        p    = self._path()

        if p == "/users":
            try:
                data = json.loads(body)
                name = data.get("name") or (data.get("user") or {}).get("name")
                self._send(201, json.dumps({"created": True, "name": name}))
            except json.JSONDecodeError:
                self._send(400, json.dumps({"error": "invalid JSON"}))

        elif p == "/form":
            parsed = urllib.parse.parse_qs(body.decode())
            self._send(200, json.dumps({k: v[0] for k, v in parsed.items()}))

        elif p == "/echo-body":
            self._send(200, json.dumps({
                "body":         body.decode("utf-8", errors="replace"),
                "content-type": ct,
            }))

        elif p == "/conflict":
            self._send(409, json.dumps({"error": "conflict"}))

        else:
            self._send(200, json.dumps({"received": len(body)}))

    # ── PUT / PATCH / DELETE / HEAD / OPTIONS ─────────────────────────────────

    def do_PUT(self) -> None:
        body = self._read_body()
        self._send(200, json.dumps({"updated": True, "body": body.decode("utf-8", errors="replace")}))

    def do_PATCH(self) -> None:
        body = self._read_body()
        self._send(200, json.dumps({"patched": True, "body": body.decode("utf-8", errors="replace")}))

    def do_DELETE(self) -> None:
        self._send(200, json.dumps({"deleted": True}))

    def do_HEAD(self) -> None:
        self._send(200, b"")

    def do_OPTIONS(self) -> None:
        self._send(200, b"",
                   extra_headers={"Allow": "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS"})


# ─────────────────────────────────────────────────────────────────────────────
#  Fixture: servidor partilhado por toda a sessão de testes
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def server():
    """Inicia o servidor HTTP de teste uma única vez para toda a sessão."""
    srv = ThreadingHTTPServer(("localhost", 19876), _TestHandler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield "http://localhost:19876"
    srv.shutdown()


@pytest.fixture(autouse=True)
def reset_state():
    """Limpa cache e contadores antes de cada teste."""
    clear_cache()
    _reset_calls()
    yield


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers de teste
# ─────────────────────────────────────────────────────────────────────────────

def url(server: str, path: str) -> str:
    return f"{server}{path}"


# ─────────────────────────────────────────────────────────────────────────────
#  TestResponse — propriedades do objeto Response
# ─────────────────────────────────────────────────────────────────────────────

class TestResponse:
    """Testa todas as propriedades do objeto Response."""

    def test_status_200(self, server):
        r = request(url(server, "/ok")).get()
        assert r.status == 200

    def test_success_true_on_2xx(self, server):
        r = request(url(server, "/ok")).get()
        assert r.success is True
        assert r.ok is True
        assert bool(r) is True

    def test_success_false_on_4xx(self, server):
        r = request(url(server, "/404")).get()
        assert r.success is False
        assert r.ok is False
        assert bool(r) is False

    def test_success_false_on_5xx(self, server):
        r = request(url(server, "/500")).get()
        assert r.success is False

    def test_json_property(self, server):
        r = request(url(server, "/ok")).get()
        assert r.json == {"status": "ok", "message": "hello"}

    def test_text_property(self, server):
        r = request(url(server, "/text")).get()
        assert r.text == "plain text response"

    def test_bytes_property(self, server):
        r = request(url(server, "/binary")).get()
        assert r.bytes == b"\x00\x01\x02\x03\xff"

    def test_json_returns_none_on_invalid_body(self, server):
        r = request(url(server, "/text")).get()
        assert r.json is None

    def test_json_returns_none_on_empty_body(self, server):
        r = request(url(server, "/empty")).get()
        assert r.json is None

    def test_headers_property(self, server):
        r = request(url(server, "/ok")).get()
        assert isinstance(r.headers, dict)
        assert "content-type" in {k.lower() for k in r.headers}

    def test_cookies_property(self, server):
        r = request(url(server, "/cookie")).get()
        assert r.cookies.get("session") == "abc123"

    def test_url_property(self, server):
        r = request(url(server, "/ok")).get()
        assert "localhost:19876" in r.url

    def test_elapsed_ms_is_positive(self, server):
        r = request(url(server, "/ok")).get()
        assert r.elapsed_ms > 0

    def test_error_false_on_success(self, server):
        r = request(url(server, "/ok")).get()
        assert r.error is False
        assert r.exception is None

    def test_error_true_on_network_failure(self):
        # Porta não existe — força erro de rede
        r = request("http://localhost:19999/").timeout(1).get()
        assert r.error is True
        assert r.exception is not None

    def test_raise_for_status_on_4xx(self, server):
        with pytest.raises(NetError):
            request(url(server, "/404")).get().raise_for_status()

    def test_raise_for_status_on_5xx(self, server):
        with pytest.raises(NetError):
            request(url(server, "/500")).get().raise_for_status()

    def test_raise_for_status_passes_on_2xx(self, server):
        r = request(url(server, "/ok")).get().raise_for_status()
        assert r.success

    def test_repr_success(self, server):
        r = request(url(server, "/ok")).get()
        assert "200" in repr(r)
        assert "✓" in repr(r)

    def test_repr_failure(self, server):
        r = request(url(server, "/404")).get()
        assert "404" in repr(r)
        assert "✗" in repr(r)


# ─────────────────────────────────────────────────────────────────────────────
#  TestHttpMethods — todos os verbos HTTP
# ─────────────────────────────────────────────────────────────────────────────

class TestHttpMethods:
    """Verifica que cada verbo HTTP é enviado correctamente."""

    def test_get(self, server):
        r = request(url(server, "/ok")).get()
        assert r.status == 200
        assert r.json["status"] == "ok"

    def test_post(self, server):
        r = request(url(server, "/users")).json({"name": "Alice"}).post()
        assert r.status == 201
        assert r.json["name"] == "Alice"
        assert r.json["created"] is True

    def test_put(self, server):
        r = request(url(server, "/item")).json({"x": 1}).put()
        assert r.status == 200
        assert r.json["updated"] is True

    def test_patch(self, server):
        r = request(url(server, "/item")).json({"y": 2}).patch()
        assert r.status == 200
        assert r.json["patched"] is True

    def test_delete(self, server):
        r = request(url(server, "/item")).delete()
        assert r.status == 200
        assert r.json["deleted"] is True

    def test_head(self, server):
        r = request(url(server, "/ok")).head()
        assert r.status == 200
        # HEAD não tem corpo
        assert r.bytes == b""

    def test_options(self, server):
        r = request(url(server, "/ok")).options()
        assert r.status == 200

    def test_204_no_content(self, server):
        r = request(url(server, "/204")).get()
        assert r.status == 204
        assert r.success

    def test_400_not_success(self, server):
        r = request(url(server, "/400")).get()
        assert r.status == 400
        assert not r.success


# ─────────────────────────────────────────────────────────────────────────────
#  TestHeaders — cabeçalhos de pedido
# ─────────────────────────────────────────────────────────────────────────────

class TestHeaders:
    """Verifica adição e envio de headers."""

    def test_single_header(self, server):
        r = request(url(server, "/headers-echo")).header("X-Custom", "arkhe").get()
        assert r.json["x-custom"] == "arkhe"

    def test_multiple_headers_dict(self, server):
        r = (
            request(url(server, "/headers-echo"))
            .headers({"X-Custom": "abc", "User-Agent": "TestSuite/1.0"})
            .get()
        )
        assert r.json["x-custom"] == "abc"
        assert r.json["user-agent"] == "TestSuite/1.0"

    def test_header_overwrite(self, server):
        r = (
            request(url(server, "/headers-echo"))
            .header("X-Custom", "first")
            .header("X-Custom", "second")
            .get()
        )
        assert r.json["x-custom"] == "second"

    def test_default_accept_header_is_sent(self, server):
        r = request(url(server, "/headers-echo")).get()
        assert r.json["accept"] != ""


# ─────────────────────────────────────────────────────────────────────────────
#  TestAuthentication — autenticação
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthentication:
    """Verifica os três mecanismos de autenticação."""

    def test_auth_bearer(self, server):
        r = request(url(server, "/auth")).auth_bearer("my-secret-token").get()
        assert r.json["auth"] == "Bearer my-secret-token"

    def test_auth_basic(self, server):
        r = request(url(server, "/auth")).auth_basic("user", "pass").get()
        expected = "Basic " + base64.b64encode(b"user:pass").decode()
        assert r.json["auth"] == expected

    def test_auth_basic_special_chars(self, server):
        r = request(url(server, "/auth")).auth_basic("u$er", "p@ss!").get()
        expected = "Basic " + base64.b64encode(b"u$er:p@ss!").decode()
        assert r.json["auth"] == expected

    def test_api_key_header(self, server):
        r = request(url(server, "/headers-echo")).api_key("X-Custom", "key-123").get()
        assert r.json["x-custom"] == "key-123"


# ─────────────────────────────────────────────────────────────────────────────
#  TestQueryParams — parâmetros de URL
# ─────────────────────────────────────────────────────────────────────────────

class TestQueryParams:
    """Verifica construção de query string."""

    def test_single_param(self, server):
        r = request(url(server, "/params")).param("page", 1).get()
        assert r.json["page"] == "1"

    def test_multiple_params_chained(self, server):
        r = request(url(server, "/params")).param("page", 2).param("limit", 50).get()
        assert r.json["page"] == "2"
        assert r.json["limit"] == "50"

    def test_params_dict(self, server):
        r = request(url(server, "/params")).params({"a": "x", "b": "y"}).get()
        assert r.json["a"] == "x"
        assert r.json["b"] == "y"

    def test_param_with_string_value(self, server):
        r = request(url(server, "/params")).param("search", "alice jones").get()
        assert r.json["search"] == "alice jones"

    def test_url_already_has_query_string(self, server):
        r = request(url(server, "/params?existing=1")).param("extra", "2").get()
        assert r.json.get("existing") == "1"
        assert r.json.get("extra") == "2"


# ─────────────────────────────────────────────────────────────────────────────
#  TestRequestBody — corpo do pedido
# ─────────────────────────────────────────────────────────────────────────────

class TestRequestBody:
    """Verifica os três tipos de corpo: JSON, form e raw."""

    def test_json_body_sets_content_type(self, server):
        r = request(url(server, "/echo-body")).json({"key": "val"}).post()
        assert "application/json" in r.json["content-type"]
        assert '"key": "val"' in r.json["body"] or '"key":"val"' in r.json["body"]

    def test_json_body_nested(self, server):
        payload = {"user": {"name": "Bob", "age": 30}, "active": True}
        r = request(url(server, "/users")).json(payload).post()
        assert r.status == 201
        assert r.json["name"] == "Bob"

    def test_form_body(self, server):
        r = request(url(server, "/form")).form({"username": "alice", "role": "admin"}).post()
        assert r.json["username"] == "alice"
        assert r.json["role"] == "admin"

    def test_raw_body_string(self, server):
        r = request(url(server, "/echo-body")).body("raw text content", "text/plain").post()
        assert r.json["body"] == "raw text content"
        assert r.json["content-type"] == "text/plain"

    def test_raw_body_bytes(self, server):
        r = (
            request(url(server, "/echo-body"))
            .body(b"binary\x00data", "application/octet-stream")
            .post()
        )
        assert r.status == 200


# ─────────────────────────────────────────────────────────────────────────────
#  TestTimeout — mecanismo de timeout
# ─────────────────────────────────────────────────────────────────────────────

class TestTimeout:
    """Verifica comportamento de timeout."""

    def test_timeout_returns_error_response(self, server):
        r = request(url(server, "/slow")).timeout(0.2).get()
        assert r.error is True
        assert isinstance(r.exception, NetTimeoutError)

    def test_timeout_message_contains_seconds(self, server):
        r = request(url(server, "/slow")).timeout(0.2).get()
        assert "0.2" in str(r.exception)

    def test_timeout_hook_fires(self, server):
        fired = []
        request(url(server, "/slow")).timeout(0.2).on_timeout(lambda: fired.append(True)).get()
        assert fired == [True]

    def test_timeout_hook_fires_only_once(self, server):
        fired = []
        request(url(server, "/slow")).timeout(0.2).on_timeout(lambda: fired.append(1)).get()
        assert len(fired) == 1

    def test_no_timeout_on_fast_response(self, server):
        r = request(url(server, "/ok")).timeout(5).get()
        assert r.error is False
        assert r.success


# ─────────────────────────────────────────────────────────────────────────────
#  TestRetry — sistema de retry
# ─────────────────────────────────────────────────────────────────────────────

class TestRetry:
    """Verifica retry automático em falhas de rede e status 5xx."""

    def test_retry_on_500_eventually_succeeds(self, server):
        # /flaky-500/2 falha 2 vezes, depois retorna 200
        path = "/flaky-500/2"
        _reset_calls()
        r = request(url(server, path)).retry(attempts=3, delay=0.05).get()
        assert r.success
        assert r.json["ok"] is True

    def test_retry_call_count(self, server):
        path = "/flaky-500/2"
        _reset_calls()
        request(url(server, path)).retry(attempts=3, delay=0.05).get()
        with _CALL_LOCK:
            assert _CALL_COUNTS.get(path, 0) == 3

    def test_retry_exhausted_returns_last_response(self, server):
        # /flaky-500/99 nunca terá sucesso em 3 tentativas
        path = "/flaky-500/99"
        _reset_calls()
        r = request(url(server, path)).retry(attempts=3, delay=0.02).get()
        assert r.status == 500

    def test_no_retry_by_default_on_500(self, server):
        path = "/flaky-500/1"
        _reset_calls()
        request(url(server, path)).get()
        with _CALL_LOCK:
            assert _CALL_COUNTS.get(path, 0) == 1

    def test_retry_exponential_delay(self, server):
        path = "/flaky-500/2"
        _reset_calls()
        t0 = time.time()
        request(url(server, path)).retry(attempts=3, delay=0.1, exponential=True).get()
        elapsed = time.time() - t0
        # Mínimo esperado: 0.1s + 0.2s = 0.3s
        assert elapsed >= 0.25

    def test_retry_does_not_retry_on_4xx(self, server):
        # 4xx não deve provocar retry
        path = "/404"
        _reset_calls()
        r = request(url(server, path)).retry(attempts=3, delay=0.02).get()
        assert r.status == 404
        with _CALL_LOCK:
            # Só 1 chamada — 4xx não faz retry
            assert _CALL_COUNTS.get(path, 0) <= 1


# ─────────────────────────────────────────────────────────────────────────────
#  TestCache — cache em memória e em disco
# ─────────────────────────────────────────────────────────────────────────────

class TestCache:
    """Verifica cache em memória e em disco."""

    def test_memory_cache_returns_same_result(self, server):
        r1 = request(url(server, "/timestamp")).cache(minutes=1).get()
        r2 = request(url(server, "/timestamp")).cache(minutes=1).get()
        assert r1.json["ts"] == r2.json["ts"]

    def test_memory_cache_hit_has_zero_elapsed(self, server):
        request(url(server, "/timestamp")).cache(minutes=1).get()
        r2 = request(url(server, "/timestamp")).cache(minutes=1).get()
        assert r2.elapsed_ms == 0.0

    def test_memory_cache_respects_ttl(self, server):
        r1 = request(url(server, "/timestamp")).cache(minutes=0.0001).get()
        time.sleep(0.02)
        r2 = request(url(server, "/timestamp")).cache(minutes=0.0001).get()
        # TTL expirado — deve ter chamado o servidor de novo
        assert r2.elapsed_ms > 0.0

    def test_cache_only_applies_to_get(self, server):
        # POST não deve ser cacheado
        r1 = request(url(server, "/timestamp")).cache(minutes=1).post()
        r2 = request(url(server, "/timestamp")).cache(minutes=1).post()
        # Sem cache: elapsed > 0 em ambos
        assert r2.elapsed_ms > 0.0

    def test_disk_cache_persists(self, server):
        r1 = request(url(server, "/timestamp")).cache(minutes=5, persistent=True).get()
        # Instância nova (cache disk é global, não por instância)
        r2 = request(url(server, "/timestamp")).cache(minutes=5, persistent=True).get()
        assert r1.json["ts"] == r2.json["ts"]

    def test_clear_cache_invalidates_memory(self, server):
        r1 = request(url(server, "/timestamp")).cache(minutes=5).get()
        clear_cache()
        r2 = request(url(server, "/timestamp")).cache(minutes=5).get()
        # Após clear, novo pedido ao servidor
        assert r2.elapsed_ms > 0.0

    def test_different_urls_cached_independently(self, server):
        r1 = request(url(server, "/ok")).cache(minutes=5).get()
        r2 = request(url(server, "/timestamp")).cache(minutes=5).get()
        assert r1.json != r2.json


# ─────────────────────────────────────────────────────────────────────────────
#  TestHooks — callbacks e hooks
# ─────────────────────────────────────────────────────────────────────────────

class TestHooks:
    """Verifica todos os hooks: on_success, on_error, on_timeout, if_status."""

    def test_on_success_fires_on_2xx(self, server):
        log = []
        request(url(server, "/ok")).on_success(lambda r: log.append(r.status)).get()
        assert log == [200]

    def test_on_success_does_not_fire_on_4xx(self, server):
        log = []
        request(url(server, "/404")).on_success(lambda r: log.append(r.status)).get()
        assert log == []

    def test_on_error_fires_on_network_failure(self):
        log = []
        request("http://localhost:19999/").timeout(0.5).on_error(log.append).get()
        assert len(log) == 1

    def test_on_error_does_not_fire_on_http_errors(self, server):
        # 4xx e 5xx são respostas HTTP válidas, não erros de rede
        log = []
        request(url(server, "/500")).on_error(log.append).get()
        assert log == []

    def test_on_timeout_fires_on_slow_response(self, server):
        log = []
        request(url(server, "/slow")).timeout(0.2).on_timeout(lambda: log.append("t")).get()
        assert log == ["t"]

    def test_multiple_on_success_callbacks(self, server):
        log = []
        (
            request(url(server, "/ok"))
            .on_success(lambda r: log.append("a"))
            .on_success(lambda r: log.append("b"))
            .get()
        )
        assert log == ["a", "b"]

    def test_if_status_fires_on_matching_status(self, server):
        log = []
        request(url(server, "/ok")).if_status(200, lambda r: log.append("ok")).get()
        assert log == ["ok"]

    def test_if_status_does_not_fire_on_wrong_status(self, server):
        log = []
        request(url(server, "/404")).if_status(200, lambda r: log.append("ok")).get()
        assert log == []

    def test_if_status_404_fires_on_404(self, server):
        log = []
        request(url(server, "/404")).if_status(404, lambda r: log.append("missing")).get()
        assert log == ["missing"]

    def test_multiple_if_status_hooks(self, server):
        s200, s404 = [], []
        (
            request(url(server, "/404"))
            .if_status(200, lambda r: s200.append(True))
            .if_status(404, lambda r: s404.append(True))
            .get()
        )
        assert s200 == [] and s404 == [True]

    def test_hook_exception_does_not_propagate(self, server):
        # Um hook que lança exceção não deve derrubar o pedido
        def bad_hook(r):
            raise RuntimeError("hook error")

        r = request(url(server, "/ok")).on_success(bad_hook).get()
        assert r.success  # pedido completo mesmo com hook quebrado


# ─────────────────────────────────────────────────────────────────────────────
#  TestExpect — validação de status
# ─────────────────────────────────────────────────────────────────────────────

class TestExpect:
    """Verifica o mecanismo .expect() de validação de status."""

    def test_expect_passes_on_matching_status(self, server):
        r = request(url(server, "/ok")).expect(200).get()
        assert r.success

    def test_expect_raises_on_wrong_status(self, server):
        with pytest.raises(UnexpectedStatusError) as exc_info:
            request(url(server, "/404")).expect(200).get()
        assert exc_info.value.response.status == 404
        assert exc_info.value.expected == (200,)

    def test_expect_multiple_statuses(self, server):
        r = request(url(server, "/users")).json({"name": "X"}).expect(200, 201).post()
        assert r.status == 201

    def test_expect_raises_with_response_accessible(self, server):
        with pytest.raises(UnexpectedStatusError) as exc_info:
            request(url(server, "/conflict")).json({}).expect(200, 201).post()
        err = exc_info.value
        assert err.response.status == 409
        assert 409 not in err.expected

    def test_unexpected_status_error_message(self, server):
        with pytest.raises(UnexpectedStatusError) as exc_info:
            request(url(server, "/404")).expect(200).get()
        assert "404" in str(exc_info.value)
        assert "200" in str(exc_info.value)

    def test_expect_on_5xx_raises(self, server):
        with pytest.raises(UnexpectedStatusError):
            request(url(server, "/500")).expect(200).get()


# ─────────────────────────────────────────────────────────────────────────────
#  TestRedirect — gestão de redirects
# ─────────────────────────────────────────────────────────────────────────────

class TestRedirect:
    """Verifica comportamento de redirect."""

    def test_follows_redirect_by_default(self, server):
        r = request(url(server, "/redirect")).get()
        assert r.success
        assert r.json.get("landed") is True

    def test_no_redirect_returns_3xx(self, server):
        r = request(url(server, "/redirect")).no_redirect().get()
        assert r.status == 302


# ─────────────────────────────────────────────────────────────────────────────
#  TestDownload — download de ficheiros
# ─────────────────────────────────────────────────────────────────────────────

class TestDownload:
    """Verifica .download() e .save()."""

    def test_download_saves_file(self, server):
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "output.json")
            r = request(url(server, "/ok")).download(dest)
            assert r.success
            assert os.path.exists(dest)
            with open(dest) as f:
                data = json.load(f)
            assert data["status"] == "ok"

    def test_save_is_alias_of_download(self, server):
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "output.json")
            r = request(url(server, "/ok")).save(dest)
            assert os.path.exists(dest)

    def test_download_binary_file(self, server):
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "data.bin")
            r = request(url(server, "/binary")).download(dest)
            assert r.success
            with open(dest, "rb") as f:
                assert f.read() == b"\x00\x01\x02\x03\xff"

    def test_download_creates_parent_dirs(self, server):
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "nested", "dir", "file.json")
            request(url(server, "/ok")).download(dest)
            assert os.path.exists(dest)


# ─────────────────────────────────────────────────────────────────────────────
#  TestAPI — sessão reutilizável
# ─────────────────────────────────────────────────────────────────────────────

class TestAPI:
    """Verifica o objeto API (sessão com base URL partilhada)."""

    def test_api_get(self, server):
        api = API(server)
        r   = api.get("/ok")
        assert r.success
        assert r.json["status"] == "ok"

    def test_api_post_json(self, server):
        api = API(server)
        r   = api.post("/users", json={"name": "Charlie"})
        assert r.status == 201
        assert r.json["name"] == "Charlie"

    def test_api_put(self, server):
        api = API(server)
        r   = api.put("/item", json={"x": 42})
        assert r.json["updated"] is True

    def test_api_patch(self, server):
        api = API(server)
        r   = api.patch("/item", json={"y": 1})
        assert r.json["patched"] is True

    def test_api_delete(self, server):
        api = API(server)
        r   = api.delete("/item")
        assert r.json["deleted"] is True

    def test_api_bearer_auth_applied_to_all_requests(self, server):
        api = API(server).auth_bearer("session-token")
        r   = api.get("/auth")
        assert r.json["auth"] == "Bearer session-token"

    def test_api_basic_auth_applied_to_all_requests(self, server):
        api = API(server).auth_basic("admin", "secret")
        r   = api.get("/auth")
        expected = "Basic " + base64.b64encode(b"admin:secret").decode()
        assert r.json["auth"] == expected

    def test_api_header_applied_to_all_requests(self, server):
        api = API(server).header("X-Custom", "shared-header")
        r   = api.get("/headers-echo")
        assert r.json["x-custom"] == "shared-header"

    def test_api_headers_dict(self, server):
        api = API(server).headers({"X-Custom": "val", "User-Agent": "API-Test"})
        r   = api.get("/headers-echo")
        assert r.json["x-custom"] == "val"
        assert r.json["user-agent"] == "API-Test"

    def test_api_timeout_applied(self, server):
        api = API(server).timeout(0.2)
        r   = api.get("/slow")
        assert r.error
        assert isinstance(r.exception, NetTimeoutError)

    def test_api_request_builder_returns_request(self, server):
        api = API(server)
        req = api.request("/params")
        assert isinstance(req, Request)

    def test_api_request_builder_inherits_defaults(self, server):
        api = API(server).auth_bearer("tok")
        r   = api.request("/auth").get()
        assert "Bearer tok" in r.json["auth"]

    def test_api_get_with_params(self, server):
        api = API(server)
        r   = api.get("/params", params={"page": "3"})
        assert r.json["page"] == "3"

    def test_api_trailing_slash_handled(self, server):
        # base URL com trailing slash não deve gerar double-slash
        api = API(server + "/")
        r   = api.get("/ok")
        assert r.success

    def test_api_repr(self, server):
        api = API(server)
        assert "localhost" in repr(api)


# ─────────────────────────────────────────────────────────────────────────────
#  TestAsync — integração com Promise
# ─────────────────────────────────────────────────────────────────────────────

class TestAsync:
    """Verifica pedidos assíncronos com async_get() → Promise."""

    def test_async_get_returns_promise(self, server):
        try:
            from arkhe.promise import Promise
        except ImportError:
            from promise import Promise  # type: ignore[import]

        p = request(url(server, "/ok")).async_get()
        assert hasattr(p, "join")

    def test_async_get_resolves_with_response(self, server):
        try:
            from arkhe.promise import Promise
        except ImportError:
            from promise import Promise  # type: ignore[import]

        r = request(url(server, "/ok")).async_get().join(timeout=5)
        assert isinstance(r, Response)
        assert r.success

    def test_async_get_then_callback(self, server):
        try:
            from arkhe.promise import Promise
        except ImportError:
            from promise import Promise  # type: ignore[import]

        results = []
        request(url(server, "/ok")).async_get() \
            .then(lambda r: results.append(r.json)) \
            .join(timeout=5)
        assert results[0]["status"] == "ok"

    def test_async_post(self, server):
        try:
            from arkhe.promise import Promise
        except ImportError:
            from promise import Promise  # type: ignore[import]

        r = (
            request(url(server, "/users"))
            .json({"name": "Async"})
            .async_post()
            .join(timeout=5)
        )
        assert r.status == 201
        assert r.json["name"] == "Async"


# ─────────────────────────────────────────────────────────────────────────────
#  TestTryIntegration — integração com arkhe.trying
# ─────────────────────────────────────────────────────────────────────────────

class TestTryIntegration:
    """Verifica que request() compõe naturalmente com Try."""

    def test_try_of_success(self, server):
        try:
            from arkhe.trying import Try
        except ImportError:
            from trying import Try  # type: ignore[import]

        val = (
            Try.of(lambda: request(url(server, "/ok")).expect(200).get())
               .map(lambda r: r.json["status"])
               .or_else("fallback")
        )
        assert val == "ok"

    def test_try_recovers_on_unexpected_status(self, server):
        try:
            from arkhe.trying import Try
        except ImportError:
            from trying import Try  # type: ignore[import]

        val = (
            Try.of(lambda: request(url(server, "/404")).expect(200).get())
               .map(lambda r: r.json)
               .recover(lambda ex: {"recovered": True})
               .or_else({})
        )
        assert val["recovered"] is True

    def test_try_maps_response_json(self, server):
        try:
            from arkhe.trying import Try
        except ImportError:
            from trying import Try  # type: ignore[import]

        name = (
            Try.of(lambda: request(url(server, "/users")).json({"name": "Try"}).post())
               .filter(lambda r: r.success, "Request failed")
               .map(lambda r: r.json["name"])
               .or_else("unknown")
        )
        assert name == "Try"


# ─────────────────────────────────────────────────────────────────────────────
#  TestExceptions — hierarquia de excepções
# ─────────────────────────────────────────────────────────────────────────────

class TestExceptions:
    """Verifica a hierarquia e atributos das excepções."""

    def test_all_exceptions_inherit_from_neterror(self):
        assert issubclass(RequestError, NetError)
        assert issubclass(NetTimeoutError, NetError)
        assert issubclass(UnexpectedStatusError, NetError)
        assert issubclass(DownloadError, NetError)

    def test_request_error_has_cause(self):
        cause = ValueError("original")
        err   = RequestError("wrapped", cause=cause)
        assert err.cause is cause

    def test_unexpected_status_error_has_response(self, server):
        with pytest.raises(UnexpectedStatusError) as exc_info:
            request(url(server, "/404")).expect(200).get()
        assert isinstance(exc_info.value.response, Response)

    def test_unexpected_status_error_has_expected_tuple(self, server):
        with pytest.raises(UnexpectedStatusError) as exc_info:
            request(url(server, "/404")).expect(200, 201).get()
        assert exc_info.value.expected == (200, 201)

    def test_neterror_is_exception(self):
        assert issubclass(NetError, Exception)


# ─────────────────────────────────────────────────────────────────────────────
#  TestRequestBuilder — fluência do builder
# ─────────────────────────────────────────────────────────────────────────────

class TestRequestBuilder:
    """Verifica que o builder é correctamente fluente (todos os métodos retornam self)."""

    def test_header_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.header("X", "y") is req

    def test_headers_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.headers({"X": "y"}) is req

    def test_auth_bearer_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.auth_bearer("tok") is req

    def test_auth_basic_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.auth_basic("u", "p") is req

    def test_param_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.param("k", "v") is req

    def test_json_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.json({"a": 1}) is req

    def test_form_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.form({"a": "b"}) is req

    def test_body_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.body("raw") is req

    def test_timeout_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.timeout(5) is req

    def test_retry_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.retry(3) is req

    def test_cache_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.cache(minutes=1) is req

    def test_expect_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.expect(200) is req

    def test_on_success_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.on_success(lambda r: None) is req

    def test_on_error_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.on_error(lambda e: None) is req

    def test_on_timeout_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.on_timeout(lambda: None) is req

    def test_if_status_returns_request(self, server):
        req = request(url(server, "/ok"))
        assert req.if_status(200, lambda r: None) is req

    def test_full_chain_executes(self, server):
        """Verifica que uma chain completa não quebra."""
        r = (
            request(url(server, "/ok"))
            .header("X-Test", "1")
            .auth_bearer("tok")
            .param("q", "test")
            .timeout(10)
            .retry(1)
            .on_success(lambda r: None)
            .on_error(lambda e: None)
            .if_status(200, lambda r: None)
            .get()
        )
        assert r.success
