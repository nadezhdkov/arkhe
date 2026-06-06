# arkhe.modifier

Modificadores de acesso estilo Java para Python — `@private`, `@protected` e `@public` — aplicados via decoradores e aplicados em tempo de execução através de descritores e inspeção de call stack.

---

## Índice

- [Motivação](#motivação)
- [Instalação e Estrutura](#instalação-e-estrutura)
- [Início Rápido](#início-rápido)
- [Regras de Visibilidade](#regras-de-visibilidade)
- [Referência da API](#referência-da-api)
  - [@modifier](#modifier)
  - [@private](#private)
  - [@protected](#protected)
  - [@public](#public)
  - [private.field / protected.field / public.field](#field-markers)
  - [ModifierInspector](#modifierinspector)
- [Exceções](#exceções)
- [Herança](#herança)
- [Como Funciona](#como-funciona)
- [Limitações e Considerações](#limitações-e-considerações)
- [Exemplos Completos](#exemplos-completos)

---

## Motivação

Python adota a convenção `_` (underscore) para sinalizar membros "internos", mas não há qualquer enforcement — qualquer código pode ler e escrever qualquer atributo. O `arkhe.modifier` vai além da convenção e **levanta erros reais** quando código fora do escopo permitido tenta acessar um membro protegido ou privado.

```python
# Sem arkhe.modifier — apenas convenção, sem proteção real
class BankAccount:
    def __init__(self):
        self._balance = 0.0   # "privado" por convenção, mas acessível

acc = BankAccount()
acc._balance = 9999.0   # ninguém impede isso

# Com arkhe.modifier — enforcement real
@modifier
class BankAccount:
    balance: float = private.field(0.0)

acc = BankAccount()
acc.balance = 9999.0   # PrivateAccessError
```

---

## Instalação e Estrutura

O módulo faz parte da biblioteca **arkhe** e não possui dependências externas além da stdlib do Python (≥ 3.10).

```
arkhe/modifier/
├── __init__.py       # API pública
├── exceptions.py     # AccessViolationError, PrivateAccessError, ProtectedAccessError
├── _caller.py        # inspeção de call stack
├── descriptors.py    # descritores de visibilidade para campos
├── core.py           # @modifier, @private, @protected, @public
└── inspect.py        # ModifierInspector
```

```python
from arkhe.modifier import modifier, private, protected, public
from arkhe.modifier import AccessViolationError, PrivateAccessError, ProtectedAccessError
from arkhe.modifier import ModifierInspector
```

---

## Início Rápido

```python
from arkhe.modifier import modifier, private, protected, public

@modifier
class BankAccount:
    owner:   str                           # público por padrão
    balance: float = private.field(0.0)   # privado — só a própria classe acessa
    limit:   float = protected.field(500.0)  # protegido — classe e subclasses

    def __init__(self, owner: str) -> None:
        self.owner = owner
        self.balance = 0.0
        self.limit = 500.0

    @private
    def _validate(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")

    @protected
    def _apply(self, amount: float) -> None:
        self._validate(amount)   # OK — mesma classe
        self.balance += amount   # OK — mesma classe

    def deposit(self, amount: float) -> None:
        self._apply(amount)      # OK — chama método protegido de dentro

    def get_balance(self) -> float:
        return self.balance      # OK — acesso privado de dentro


acc = BankAccount("Alice")
acc.deposit(100.0)
print(acc.get_balance())   # 100.0
print(acc.owner)           # "Alice"  — campo público

acc.balance                # PrivateAccessError
acc.limit                  # ProtectedAccessError
acc._validate(10.0)        # PrivateAccessError
acc._apply(10.0)           # ProtectedAccessError
```

---

## Regras de Visibilidade

| Modificador   | Quem pode acessar                                  | Equivalente Java |
|---------------|----------------------------------------------------|------------------|
| `@public`     | Qualquer código                                    | `public`         |
| `@protected`  | A classe declarante **e suas subclasses**          | `protected`      |
| `@private`    | **Apenas** a classe declarante (subclasses negadas) | `private`       |

> **Diferença importante em relação ao Python convencional:** o prefixo `_` é apenas uma convenção — `@private` e `@protected` do arkhe levantam erros reais em tempo de execução.

---

## Referência da API

### `@modifier`

Decorador de classe que ativa o enforcement de visibilidade. Deve ser aplicado a qualquer classe que use `@private`, `@protected`, `@public` em seus membros.

```python
@modifier
class MinhaClasse:
    ...
```

**O que `@modifier` faz:**

1. Varre `__annotations__` e instala descritores para campos marcados com `.field()`.
2. Varre `__dict__` e envolve métodos marcados com `@private` / `@protected` em closures de enforcement.
3. Armazena o mapa de visibilidade em `cls.__arkhe_visibility_map__`.
4. Patcha `__init_subclass__` para que subclasses herdem o enforcement automaticamente.

**Alias funciona normalmente** — `@modifier` é uma função Python simples:

```python
from arkhe.modifier import modifier as access, private

@access
class Config:
    secret: str = private.field("s3cr3t")
```

---

### `@private`

Restringe o acesso ao membro **apenas à classe declarante**. Subclasses são negadas — espelhando exatamente a semântica `private` do Java.

**Em métodos:**

```python
@modifier
class Foo:
    @private
    def _internal(self) -> None:
        ...   # só Foo pode chamar
```

**Em campos** — via `private.field()`:

```python
@modifier
class Foo:
    secret: str = private.field("valor_padrão")
```

---

### `@protected`

Permite acesso à classe declarante **e a qualquer subclasse** dela.

**Em métodos:**

```python
@modifier
class Animal:
    @protected
    def _breathe(self) -> None:
        ...

class Dog(Animal):
    def live(self):
        self._breathe()   # OK — Dog é subclasse de Animal
```

**Em campos** — via `protected.field()`:

```python
@modifier
class Animal:
    energy: int = protected.field(100)
```

---

### `@public`

Declara explicitamente que um membro é público. Equivalente ao comportamento padrão do Python — sem qualquer restrição. Útil para tornar a intenção explícita no código.

```python
@modifier
class Produto:
    nome:  str   = public.field("sem nome")   # explicitamente público
    preco: float = private.field(0.0)         # privado
```

Campos **sem nenhum marcador** também são tratados como públicos por padrão.

---

### Field Markers

A forma de declarar visibilidade em **campos** (atributos de classe) é através dos métodos `.field()`:

```python
nome_campo: Tipo = <modificador>.field(valor_padrão)
nome_campo: Tipo = <modificador>.field()           # sem default
```

| Sintaxe                        | Resultado                              |
|--------------------------------|----------------------------------------|
| `x: int = private.field(0)`   | campo privado com default `0`          |
| `x: int = private.field()`    | campo privado sem default              |
| `x: int = protected.field(5)` | campo protegido com default `5`        |
| `x: int = public.field("hi")` | campo público com default `"hi"`       |
| `x: int`                      | campo público sem default (padrão Python) |

> **Por que `.field()` e não apenas a annotation?**
> Annotations em Python são avaliadas de forma lazy e não carregam metadados de runtime por si só. O `.field()` cria um objeto sentinela (`_FieldMarker`) que `@modifier` detecta ao varrer `cls.__dict__`, instalando o descriptor apropriado.

---

### `ModifierInspector`

Ferramenta de introspecção em runtime para classes decoradas com `@modifier`.

```python
from arkhe.modifier import ModifierInspector

info = ModifierInspector(BankAccount)
```

**Propriedades e métodos:**

```python
info.is_modifier_applied          # True/False
info.visibility_of("balance")     # "private" | "protected" | "public" | None
info.all_members                  # dict[str, str] — todos os membros rastreados
info.private_members              # set[str]
info.protected_members            # set[str]
info.public_members               # set[str]
info.inherited_from               # list[Type] — bases que também têm @modifier
info.summary()                    # tabela formatada (ver abaixo)
```

**Exemplo de `summary()`:**

```
┌────────────────────────────────────────────────────┐
│  arkhe.modifier  →  BankAccount                    │
├────────────────────────────────────────────────────┤
│  Member             Visibility                     │
│  ──────────────     ─────────                     │
│  owner              🟢 public                     │
│  balance            🔴 private                    │
│  limit              🟡 protected                  │
│  _validate          🔴 private                    │
│  _apply             🟡 protected                  │
│  deposit            🟢 public                     │
├────────────────────────────────────────────────────┤
│  Inherited from: (none)                            │
└────────────────────────────────────────────────────┘
```

---

## Exceções

Todas as exceções de violação de acesso herdam de `AccessViolationError`.

```
AccessViolationError (Exception)
├── PrivateAccessError
└── ProtectedAccessError
```

**Atributos comuns:**

| Atributo     | Tipo  | Descrição                                        |
|--------------|-------|--------------------------------------------------|
| `member`     | `str` | Nome do campo ou método acessado ilegalmente     |
| `visibility` | `str` | `"private"` ou `"protected"`                    |
| `caller`     | `str` | Nome qualificado de quem tentou o acesso         |
| `owner`      | `str` | Nome qualificado da classe dona do membro        |

**Exemplo de captura:**

```python
try:
    print(acc.balance)
except PrivateAccessError as e:
    print(e.member)      # "balance"
    print(e.visibility)  # "private"
    print(e.owner)       # "BankAccount"
    print(e.caller)      # "<module 'main'>" ou "Foo.bar_method"
    print(e)             # [arkhe.modifier] private member 'balance' of 'BankAccount'
                         #   cannot be accessed from '<module ...>'
```

---

## Herança

O `@modifier` propaga automaticamente o enforcement para subclasses via `__init_subclass__` — subclasses **não precisam** do decorador `@modifier` explicitamente (embora possam tê-lo para declarar seus próprios membros).

```python
@modifier
class Animal:
    energy: int    = protected.field(100)
    dna:    str    = private.field("ATCG")

    @protected
    def _metabolize(self, amount: int) -> None:
        self.energy += amount

    def eat(self, amount: int) -> None:
        self._metabolize(amount)


class Dog(Animal):
    """Subclasse — herda o enforcement automaticamente."""

    def run(self) -> None:
        self._metabolize(-10)   # ✅ protegido: subclasse pode chamar
        print(self.energy)      # ✅ protegido: subclasse pode ler

    def check_dna(self) -> str:
        return self.dna         # ❌ PrivateAccessError — privado ao Animal


@modifier
class Robô(Animal):
    """Subclasse com seus próprios membros @modifier."""
    battery: float = private.field(100.0)

    def status(self) -> float:
        return self.battery     # ✅ privado ao Robô — acesso interno OK
```

**Regras de herança resumidas:**

- `@protected` → subclasses têm acesso ✅
- `@private` → apenas a classe declarante tem acesso, subclasses são negadas ❌
- Subclasses podem ter seus próprios campos `private` independentes
- Herança múltipla é suportada — o MRO do Python é respeitado

---

## Como Funciona

### 1. Inspeção de Call Stack (`_caller.py`)

A peça central do módulo. A cada acesso a um campo ou chamada a um método guardado, `get_caller_class()` percorre `inspect.stack()`, ignora frames internos do próprio `arkhe.modifier`, e retorna o tipo (`type`) do primeiro frame de código do usuário encontrado.

```
Pilha de chamadas quando acc.balance é lido:
  frame 0: get_caller_class()         ← ignorado (interno)
  frame 1: PrivateDescriptor.__get__  ← ignorado (interno)
  frame 2: test_private_field()       ← ESTE — sem 'self' → None → negado
```

Se o frame tiver `self` → retorna `type(self)`. Se tiver `cls` (classmethod) → retorna `cls`. Se nenhum → código de módulo → `None` → acesso negado para private/protected.

### 2. Descritores Python (`descriptors.py`)

Campos marcados são substituídos por objetos que implementam o [protocolo de descritores](https://docs.python.org/3/howto/descriptor.html) do Python (`__get__`, `__set__`, `__delete__`). O valor real fica em `instance.__dict__["_arkhe__<nome>"]` — nunca exposto diretamente.

```
acc.balance          →  PrivateDescriptor.__get__(acc, BankAccount)
                         → get_caller_class() → None (módulo) → PrivateAccessError
acc.balance = 100    →  PrivateDescriptor.__set__(acc, 100)
                         → get_caller_class() → None → PrivateAccessError
```

### 3. Wrappers de Método (`descriptors.py`)

Métodos decorados com `@private` / `@protected` recebem um wrapper `functools.wraps` que executa a mesma checagem de caller antes de delegar para a função original. O `owner_ref` é uma lista de um elemento preenchida após a classe ser totalmente construída, evitando referências circulares.

### 4. `@modifier` (orquestrador)

Varre a classe, instala descritores nos campos e wrappers nos métodos, depois patcha `__init_subclass__` para propagar o enforcement automaticamente para qualquer subclasse futura.

---

## Limitações e Considerações

**Performance:** cada acesso a um campo ou método guardado invoca `inspect.stack()`. Isso tem custo — não use `@private`/`@protected` em caminhos de código extremamente hot (loops de milhões de iterações). Para uso normal em lógica de negócio o overhead é imperceptível.

**`__init__` manual:** se sua classe tem `__init__` manual, escreva `self.campo = valor` normalmente — o descriptor intercepta e valida quem está escrevendo. Como o frame de `__init__` tem `self` da própria classe, o acesso é permitido.

```python
@modifier
class Foo:
    x: int = private.field()

    def __init__(self, x: int) -> None:
        self.x = x    # ✅ __init__ é método da própria classe
```

**Combinação com `@komodo`:** os módulos são independentes. Aplique `@modifier` por último (mais externo na pilha de decoradores), depois `@komodo.*`:

```python
@modifier          # externo — aplicado por último
@komodo.data       # interno — aplicado primeiro
class Produto:
    nome:  str
    preco: float = private.field(0.0)
```

**`inspect.getsource()` e geração de AST:** o `@modifier` trabalha no nível de instância/runtime e não altera o código-fonte nem o AST da classe. É totalmente compatível com o engine AST do `arkhe.komodo`.

**Pickling:** objetos com campos gerenciados por descritores `_arkhe__*` podem ser serializados com `pickle` normalmente, pois os valores ficam em `instance.__dict__`.

---

## Exemplos Completos

### Sistema bancário com herança

```python
from arkhe.modifier import modifier, private, protected, public

@modifier
class Conta:
    titular: str
    _saldo:  float = private.field(0.0)
    _limite: float = protected.field(1000.0)

    def __init__(self, titular: str) -> None:
        self.titular = titular
        self._saldo = 0.0
        self._limite = 1000.0

    @private
    def _checar_limite(self, valor: float) -> None:
        if self._saldo - valor < -self._limite:
            raise ValueError("Limite excedido")

    @protected
    def _debitar(self, valor: float) -> None:
        self._checar_limite(valor)
        self._saldo -= valor

    def sacar(self, valor: float) -> None:
        self._debitar(valor)

    def saldo(self) -> float:
        return self._saldo


class ContaPoupanca(Conta):
    taxa: float = public.field(0.05)

    def __init__(self, titular: str, taxa: float = 0.05) -> None:
        super().__init__(titular)
        self.taxa = taxa

    def render(self) -> None:
        juros = self.saldo() * self.taxa
        self._debitar(-juros)   # protegido — subclasse pode chamar


c = ContaPoupanca("Maria")
c.sacar(100.0)
c.render()
print(c.saldo())     # -95.0
print(c.titular)     # "Maria"
c._saldo             # PrivateAccessError
c._limite            # ProtectedAccessError
```

### Introspecção com ModifierInspector

```python
from arkhe.modifier import ModifierInspector

info = ModifierInspector(Conta)

print(info.visibility_of("_saldo"))    # "private"
print(info.visibility_of("titular"))   # "public"
print(info.private_members)           # {"_saldo", "_checar_limite"}
print(info.protected_members)         # {"_limite", "_debitar"}

print(info.summary())
```

### Captura de erros de acesso

```python
from arkhe.modifier import PrivateAccessError, ProtectedAccessError

conta = Conta("João")

try:
    valor = conta._saldo
except PrivateAccessError as e:
    print(f"Bloqueado: '{e.member}' é {e.visibility} de '{e.owner}'")
    # Bloqueado: '_saldo' é private de 'Conta'

try:
    conta._limite = 5000.0
except ProtectedAccessError as e:
    print(f"Bloqueado: {e}")
    # [arkhe.modifier] protected member '_limite' of 'Conta'
    #   cannot be accessed from '<module ...>'
```
