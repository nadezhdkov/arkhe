# Net (`nestifypy.net`)

> Cliente HTTP fluente para o ecossistema Nestifypy.  
> Sem dependências externas — usa apenas a stdlib Python (`urllib`).

---

## Importação

```python
from nestifypy.net import request, API
```

---

## Filosofia

**Antes (Python tradicional):**

```python
import urllib.request, json

req = urllib.request.Request(
    "https://api.github.com/users/octocat",
    headers={"Authorization": "Bearer token"},
)
with urllib.request.urlopen(req, timeout=5) as r:
    data = json.loads(r.read())
print(data)
```

**Depois (Nestifypy Net):**

```python
r = (
    request("https://api.github.com/users/octocat")
    .auth_bearer(token)
    .timeout(5)
    .get()
)
if r.success:
    print(r.json)
```

---

## Métodos HTTP

```python
request(url).get()
request(url).post()
request(url).put()
request(url).patch()
request(url).delete()
request(url).head()
request(url).options()
```

---

## Headers

```python
# Individual
request(url).header("X-Custom", "value").get()

# Múltiplos de uma vez
request(url).headers({
    "Authorization": token,
    "Accept": "application/json",
    "X-App-Version": "2.0",
}).get()
```

---

## Autenticação

```python
# Bearer Token
request(url).auth_bearer(token).get()

# Basic Auth
request(url).auth_basic("username", "password").get()

# API Key num header personalizado
request(url).api_key("X-API-Key", key).get()
```

---

## Query Parameters

```python
request(url).param("page", 1).param("limit", 10).get()
# → url?page=1&limit=10

request(url).params({"search": "alice", "active": True}).get()
```

---

## Corpo do pedido

```python
# JSON (define Content-Type: application/json automaticamente)
request(url).json({"name": "Alice", "role": "admin"}).post()

# Form URL-encoded
request(url).form({"username": "alice", "password": "secret"}).post()

# Texto ou bytes brutos
request(url).body("raw content", content_type="text/plain").post()
request(url).body(b"\x00\x01\x02", content_type="application/octet-stream").put()
```

---

## Timeout

```python
request(url).timeout(10).get()   # 10 segundos (default: 30)
```

---

## Retry

```python
# 3 tentativas com 0.5s entre cada uma
request(url).retry(3).get()

# Backoff exponencial: 1s → 2s → 4s
request(url).retry(attempts=5, delay=1, exponential=True).get()
```

O retry activa automaticamente para erros de rede **e** status >= 500.

---

## Cache

```python
# Cache em memória (vida do processo)
request(url).cache(minutes=5).get()

# Cache persistente em disco (entre sessões)
request(url).cache(minutes=60, persistent=True).get()

# Limpar toda a cache
from nestifypy.net import clear_cache
clear_cache()
```

A cache aplica-se apenas a pedidos GET.

---

## Response

```python
r = request(url).get()

r.status       # int — código HTTP (200, 404, 500…)
r.success      # bool — True se 200 ≤ status < 300
r.ok           # alias de success
r.error        # bool — True se houve excepção de rede
r.exception    # BaseException | None
r.json         # Any — corpo deserializado como JSON
r.text         # str — corpo como texto UTF-8
r.bytes        # bytes — corpo em bytes brutos
r.headers      # Dict[str, str]
r.cookies      # Dict[str, str] — cookies do Set-Cookie
r.url          # str — URL final (após redirects)
r.elapsed_ms   # float — tempo de execução em ms
bool(r)        # True se success

r.raise_for_status()  # lança NetError se status >= 400
```

---

## Tratamento de erros

```python
# Verificação manual
r = request(url).get()
if r.error:
    print(type(r.exception).__name__, r.exception)

# Validação de status com expect()
try:
    request(url).expect(200, 201).post()
except UnexpectedStatusError as e:
    print(e.response.status, e.expected)

# raise_for_status()
request(url).get().raise_for_status()  # lança se >= 400
```

---

## Hooks e callbacks

```python
request(url) \
    .on_success(lambda r: print("OK:", r.status)) \
    .on_error(lambda e: print("ERR:", e)) \
    .on_timeout(lambda: print("Timeout!")) \
    .get()
```

### Acções por status

```python
request(url) \
    .if_status(200, lambda r: process(r.json)) \
    .if_status(401, lambda r: refresh_token()) \
    .if_status(404, lambda r: log_missing(r.url)) \
    .get()
```

---

## Download de ficheiros

```python
r = request("https://example.com/report.pdf").download("reports/report.pdf")
# ou
r = request("https://example.com/image.png").save("static/image.png")

if r.success:
    print("Guardado com sucesso")
```

---

## Async (integração Promise)

```python
from nestifypy.net import request

# Retorna Promise[Response]
request(url).async_get() \
            .then(lambda r: print(r.json)) \
            .catch(lambda e: print("Erro:", e))

# Todos os métodos têm versão async
request(url).async_post()
request(url).async_put()
request(url).async_delete()
request(url).async_patch()
```

---

## Integração com Try

```python
from nestifypy.trying import Try
from nestifypy.net import request, UnexpectedStatusError

user = (
    Try.of(lambda: request(url).expect(200).get())
       .map(lambda r: r.json)
       .recover(lambda ex: {"name": "Guest"})
       .or_else({})
)
```

---

## Integração com Scheduler

```python
from nestifypy.scheduler import Scheduler
from nestifypy.net import request

Scheduler.every(5).minutes(
    lambda: request("https://api.example.com/health").get()
).log()
```

---

## API — Sessão reutilizável

Para comunicar repetidamente com a mesma base URL:

```python
from nestifypy.net import API

api = (
    API("https://api.github.com")
    .auth_bearer(token)
    .header("Accept", "application/vnd.github.v3+json")
    .timeout(10)
    .retry(3)
)

# Todos os pedidos herdam a configuração da sessão
octocat = api.get("/users/octocat").json
repos   = api.get("/users/octocat/repos").json
issues  = api.get("/repos/octocat/hello-world/issues", params={"state": "open"}).json

# POST com JSON
api.post("/repos", json={"name": "my-new-repo", "private": False})

# Acesso ao builder completo (para opções avançadas)
api.request("/search/repositories") \
   .param("q", "nestifypy") \
   .param("sort", "stars") \
   .expect(200) \
   .get()
```

---

## Exemplo completo

```python
from nestifypy.net import request, API, UnexpectedStatusError

def log_error(ex):
    print(f"[ERROR] {type(ex).__name__}: {ex}")

# GET com retry, cache e hooks
result = (
    request("https://api.example.com/users/42")
    .auth_bearer("my-token")
    .timeout(10)
    .retry(attempts=3, delay=1, exponential=True)
    .cache(minutes=5)
    .expect(200)
    .on_success(lambda r: print(f"Loaded in {r.elapsed_ms:.0f}ms"))
    .on_error(log_error)
    .get()
)

if result.success:
    user = result.json
    print(f"Name: {user['name']}")

# POST com JSON
r = (
    request("https://api.example.com/users")
    .auth_bearer("my-token")
    .json({"name": "Alice", "email": "alice@example.com"})
    .expect(200, 201)
    .post()
)
print(r.status, r.json)
```

---

## Excepções

| Excepção | Quando é lançada |
|---|---|
| `NetError` | Base de todas as excepções do módulo |
| `RequestError` | Erro de rede (DNS, conexão recusada…) |
| `TimeoutError` | Pedido excedeu o timeout |
| `UnexpectedStatusError` | Status não está nos esperados por `.expect()` |
| `DownloadError` | Erro ao guardar ficheiro em disco |

---

## Resumo da API — Request

| Método | Descrição |
|---|---|
| `.header(k, v)` / `.headers({})` | Adiciona headers |
| `.auth_bearer(token)` | Authorization: Bearer |
| `.auth_basic(u, p)` | Authorization: Basic |
| `.api_key(header, key)` | Header personalizado de API key |
| `.param(k, v)` / `.params({})` | Query parameters |
| `.json(data)` | Corpo JSON |
| `.form(data)` | Corpo form URL-encoded |
| `.body(raw, ct)` | Corpo bruto (str ou bytes) |
| `.timeout(s)` | Timeout em segundos |
| `.retry(n, delay, exponential)` | Retry automático |
| `.cache(minutes, persistent)` | Cache GET |
| `.expect(*statuses)` | Validação de status |
| `.on_success(fn)` | Hook de sucesso |
| `.on_error(fn)` | Hook de erro |
| `.on_timeout(fn)` | Hook de timeout |
| `.if_status(code, fn)` | Acção por código HTTP |
| `.no_redirect()` | Desactiva redirects |
| `.no_ssl_verify()` | Desactiva verificação SSL |
| `.get()` / `.post()` / `.put()` / … | Executa o pedido |
| `.async_get()` / `.async_post()` / … | Executa assincronamente → Promise |
| `.download(dest)` / `.save(dest)` | Download para ficheiro |
| `.raise_for_status()` | Lança se status >= 400 |
