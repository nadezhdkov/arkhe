# nestifypy.komodo

> Um verdadeiro Lombok para Python — metaprogramação via AST com zero overhead em runtime.

O Komodo transforma classes Python em tempo de importação utilizando manipulação direta da **Abstract Syntax Tree (AST)**. Os métodos gerados são bytecode nativo — equivalentes a código escrito manualmente pelo programador. Sem wrappers, sem monkey-patching, sem metaclasses.

**Engine:** AST nativa (ast.parse → transform → compile → exec)  
**Python:** 3.10+  
**Dependencies:** nenhuma (stdlib only)  
**Versão:** 0.2.1

---

## Índice

- [Instalação](#instalação)
- [Visão Geral](#visão-geral)
- [Como Funciona — AST Engine](#como-funciona--ast-engine)
- [Referência de Decorators](#referência-de-decorators)
  - [@komodo.constructor](#komodoconstructor)
  - [@komodo.data](#komododata)
  - [@komodo.value](#komodovalue)
  - [@komodo.record](#komodorecord)
  - [@komodo.builder](#komodobuilder)
  - [@komodo.singular()](#komodosingular)
  - [@komodo.immutable](#komodoimmutable)
  - [@komodo.logger](#komodologger)
  - [@komodo.non_null](#komodonon_null)
  - [@komodo.validated](#komodovalidated)
  - [@komodo.copyable](#komodocopyable)
  - [@komodo.accessors()](#komodoaccessors)
  - [@komodo.getter / @komodo.setter / @komodo.withers](#komodogetter--komodosetter--komodowithers)
  - [@komodo.to_dict / @komodo.from_dict / @komodo.json](#komodoto_dict--komodofrom_dict--komodojson)
  - [@komodo.equals_and_hashcode / @komodo.to_string](#komodoequals_and_hashcode--komodoto_string)
- [Design by Contract](#design-by-contract)
  - [@contract](#contract)
  - [requires()](#requires)
  - [ensures()](#ensures)
  - [invariant()](#invariant)
  - [ContractViolationError](#contractviolationerror)
- [KomodoInspector](#komodoinspector)
- [Composição de Decorators](#composição-de-decorators)
- [Comparação com Lombok](#comparação-com-lombok)
- [Arquitectura Interna](#arquitectura-interna)
- [Notas Técnicas](#notas-técnicas)

---

## Instalação

O package `komodo` faz parte da biblioteca `nestifypy`:

```
nestifypy/
├── __init__.py
├── komodo/
│   ├── __init__.py
│   ├── core.py              # namespace de decorators
│   ├── ast_engine.py         # motor AST central
│   ├── ast_builders.py       # helpers para construção de nós AST
│   ├── contract.py           # Design by Contract
│   ├── inspect.py            # KomodoInspector
│   └── ast_generators/       # geradores por feature
│       ├── __init__.py
│       ├── constructor.py
│       ├── repr.py
│       ├── eq_hash.py
│       ├── record.py
│       ├── immutable.py
│       ├── builder.py
│       ├── accessors.py
│       ├── validation.py
│       ├── logger.py
│       ├── copyable.py
│       ├── serialization.py
│       └── utils.py
```

Importação:

```python
from nestifypy.komodo import komodo, contract, KomodoInspector
from nestifypy.komodo.contract import requires, ensures, invariant, ContractViolationError
```

---

## Visão Geral

`komodo` é um namespace de decorators de classe que reescreve a classe **em tempo de definição** via manipulação da AST. Cada decorator é independente e composável — empilhar múltiplos decorators acumula transformações na mesma árvore antes da compilação final.

```python
from nestifypy.komodo import komodo

@komodo.logger
@komodo.copyable
@komodo.data
class User:
    name: str
    email: str
    role: str = "user"

# Tudo gerado nativamente via AST:
u = User("Alice", "alice@example.com")
print(u)                          # User(name='Alice', email='alice@example.com', role='user')
u2 = u.copy_with(role="admin")
User.logger.info("User created")
```

---

## Como Funciona — AST Engine

O Komodo **não** usa closures, `setattr`, ou wrappers dinâmicos. O fluxo é:

```
Classe Original (source code)
        ↓
   ast.parse()          → Árvore Sintática (ast.Module)
        ↓
   Generators           → Mutação da AST (inserção de FunctionDef, ClassDef, etc.)
        ↓
   compile()            → Code object (bytecode nativo)
        ↓
   exec()               → Classe final no namespace do módulo
```

**Consequências práticas:**

- O `dis.dis(MyClass.__init__)` mostra bytecode idêntico a uma classe escrita à mão
- Não há frames extras na stack trace
- `inspect.getsource()` continua funcional
- Performance de instanciação é O(1) — sem interceptações
- Decorators são removidos automaticamente da AST para evitar recursão infinita

**Stacking de decorators:** Quando múltiplos decorators são empilhados, a AST é preservada entre chamadas via `cls.__komodo_ast__`. Cada gerador opera na mesma árvore, e a compilação ocorre uma vez por decorator aplicado.

---

## Referência de Decorators

### @komodo.constructor

Gera `__init__` a partir de `__annotations__`. Campos sem default são argumentos obrigatórios; campos com default são opcionais.

Equivalente Lombok: `@AllArgsConstructor` / `@RequiredArgsConstructor`

```python
@komodo.constructor
class Server:
    host: str
    port: int = 8080
    debug: bool = False

s = Server("localhost")           # port=8080, debug=False
s2 = Server("0.0.0.0", 443)
s3 = Server(host="api.example.com", port=443, debug=True)
```

**`__post_init__`**: se definires este método, é chamado automaticamente no final do `__init__` gerado:

```python
@komodo.constructor
class Config:
    host: str
    port: int = 5432

    def __post_init__(self):
        self.url = f"postgresql://{self.host}:{self.port}"

c = Config("db.prod.com")
print(c.url)  # postgresql://db.prod.com:5432
```

**Variantes:**

| Decorator | Comportamento |
|---|---|
| `@komodo.constructor` / `@komodo.all_args_constructor` | Todos os campos anotados como parâmetros |
| `@komodo.required_args_constructor` | Apenas campos sem default como parâmetros |
| `@komodo.no_args_constructor` | `__init__` sem parâmetros (usa defaults) |

---

### @komodo.data

Atalho que aplica `constructor` + `to_str` + `eq` numa só anotação.

Gera: `__init__`, `__repr__`, `__str__`, `__eq__`, `__hash__`.

```python
@komodo.data
class Point:
    x: float
    y: float

p1 = Point(1.0, 2.0)
p2 = Point(1.0, 2.0)

print(p1)           # Point(x=1.0, y=2.0)
print(p1 == p2)     # True
points = {p1, p2}   # funciona como chave de set/dict
print(len(points))  # 1
```

Marca a classe com `__komodo_meta__ = {'data', 'all_constructor', 'to_str', 'eq'}`.

---

### @komodo.value

Cria um **objeto de valor imutável**. Aplica: `data` + `immutable`. Qualquer mutação após construção levanta `AttributeError`.

```python
@komodo.value
class Money:
    amount: float
    currency: str

m = Money(9.99, "USD")
m.amount = 0.0  # AttributeError: Money is immutable — cannot modify attribute 'amount'

m2 = m.copy_with(amount=19.99)  # funciona, retorna nova instância
```

**Internamente:**
- No final do `__init__`, injeta `object.__setattr__(self, "_frozen", True)`
- Sobrescreve `__setattr__` e `__delattr__` para bloquear mutações após congelamento

---

### @komodo.record

Gerador mestre que aplica num só passo: `constructor` + `repr` + `eq/hash` + `immutable` + `to_dict` + `from_dict` + `to_json` + `from_json`.

Ideal para modelos de dados completos:

```python
@komodo.record
class Person:
    name: str
    age: int

p = Person("Alice", 30)
print(p)                        # Person(name='Alice', age=30)
print(p.to_dict())              # {'name': 'Alice', 'age': 30}
p2 = Person.from_dict(p.to_dict())
assert p == p2

# Serialização JSON
json_str = p.to_json()          # '{"name": "Alice", "age": 30}'
p3 = Person.from_json(json_str)

p.name = "Bob"                  # AttributeError: Person is immutable
```

Marks `__komodo_meta__` com todas as features acumuladas.

---

### @komodo.builder

Injeta uma inner class `Builder` com API fluente na AST da classe. Cada campo ganha um método `with_<campo>()`. O `.build()` valida campos obrigatórios.

```python
@komodo.builder
@komodo.constructor
class HttpRequest:
    url: str
    method: str = "GET"
    timeout: float = 30.0

req = (
    HttpRequest.builder()
        .with_url("https://api.example.com")
        .with_method("POST")
        .with_timeout(10.0)
        .build()
)

# Campo obrigatório faltando:
HttpRequest.builder().build()
# ValueError: HttpRequest.Builder: required field 'url' was not set
```

**Inner class Builder:**
- `Builder.__init__()`: inicializa campos com defaults ou `_UNSET`
- `with_<field>(value)`: setter fluente que retorna `self`
- `build()`: cria a instância, validando campos obrigatórios

---

### @komodo.singular()

Usado em conjunto com `@komodo.builder`. Gera um método singular (append) para campos do tipo lista.

```python
@komodo.builder
@komodo.singular("members")
@komodo.record
class Team:
    name: str
    members: list[str]

team = (
    Team.builder()
        .with_name("Guardians")
        .member("Alice")
        .member("Bob")
        .member("Charlie")
        .build()
)

print(team.members)  # ['Alice', 'Bob', 'Charlie']
```

**O que gera:**
- Método singular `member(item)` que faz `.append(item)` e retorna `self`
- Mantém também o setter regular `members(value)`

---

### @komodo.immutable

Torna a classe imutável após construção. Qualquer tentativa de mudar atributos levanta `AttributeError`.

```python
@komodo.immutable
@komodo.data
class Coordinate:
    lat: float
    lon: float

c = Coordinate(40.7128, -74.0060)
c.lat = 0.0  # AttributeError: Coordinate is immutable — cannot modify attribute 'lat'
```

**Mecanismo:**
- Injeta no fim do `__init__`: `object.__setattr__(self, "_frozen", True)`
- Sobrescreve `__setattr__` e `__delattr__` para verificar `self._frozen`

---

### @komodo.logger

Injeta um logger nativo da stdlib `logging` como atributo de classe.

```python
@komodo.logger
@komodo.data
class Application:
    name: str
    version: str

app = Application("MyApp", "1.0.0")
Application.logger.info("Starting application")
Application.logger.warning(f"App {app.name} v{app.version}")
```

**Gerado:**
```python
logger = logging.getLogger(f"{__name__}.Application")
```

O nome do logger é `<module_name>.<ClassName>`.

---

### @komodo.non_null

Valida que nenhum campo obrigatório é `None`. Levanta `ValueError` no `__init__` se algum campo for `None`.

```python
@komodo.non_null
@komodo.constructor
class User:
    name: str
    email: str
    age: int = 18

User("Alice", None, 25)  
# ValueError: User: field 'email' must not be None
```

**Nota:** Funciona apenas com campos obrigatórios (sem default). Insere checks no início do `__init__`.

---

### @komodo.validated

Valida tipos básicos em tempo de construção. Levanta `TypeError` se o tipo não corresponder.

```python
@komodo.validated
@komodo.constructor
class Product:
    name: str
    price: float
    stock: int

Product("Widget", "9.99", 100)
# TypeError: Product: field 'price' expected float
```

**Suporta tipos simples:**
- `str`, `int`, `float`, `bool`
- Tipos complexos (`list[str]`, `Optional[int]`) são ignorados (requer análise mais elaborada)

---

### @komodo.copyable

Adiciona `copy()` e `copy_with(**overrides)` para clonagem superficial e com modificações.

```python
@komodo.copyable
@komodo.data
class Point:
    x: float
    y: float

p1 = Point(1.0, 2.0)
p2 = p1.copy()           # clone superficial
p3 = p1.copy_with(x=5.0) # clone com mudança

print(p1 == p2)          # True
print(p2 == p3)          # False
print(p3)                # Point(x=5.0, y=2.0)
```

**Métodos gerados:**
- `copy()`: retorna `copy.copy(self)`
- `copy_with(**overrides)`: retorna nova instância com campos sobrescrevados

---

### @komodo.accessors()

Gera getters, setters e withers (métodos tipo `.with_field(value)`) para campos.

```python
@komodo.accessors(getter=True, setter=True, withers=False)
@komodo.data
class Temperature:
    celsius: float

t = Temperature(25.0)
print(t.celsius)        # getter: 25.0
t.celsius = 30.0        # setter
t2 = t.with_celsius(35.0)  # wither (quando ativado)
```

**Parâmetros:**
- `fluent=False`: se `True`, método único que funciona como getter/setter conforme argumentos
- `getter=True`: gera `@property` para leitura
- `setter=True`: gera `@<field>.setter` para escrita
- `withers=False`: gera `with_<field>(value)` que retorna `self` (para chaining)

**Variantes rápidas:**
- `@komodo.getter`: apenas getters
- `@komodo.setter`: apenas setters
- `@komodo.withers`: apenas withers

---

### @komodo.to_dict / @komodo.from_dict / @komodo.json

Serialização bidirecional para dict e JSON.

```python
@komodo.data
class Event:
    name: str
    timestamp: int

e = Event("click", 1717300000)

# to_dict()
d = e.to_dict()                  # {'name': 'click', 'timestamp': 1717300000}

# from_dict() — classmethod
e2 = Event.from_dict(d)
assert e == e2

# to_json()
json_str = e.to_json()           # '{"name": "click", "timestamp": 1717300000}'

# from_json() — classmethod
e3 = Event.from_json(json_str)
assert e == e3
```

**Métodos:**
- `to_dict() -> dict`: retorna `{field: value, ...}`
- `from_dict(data: dict) -> cls`: classmethod que faz `cls(**data)`
- `to_json() -> str`: retorna `json.dumps(self.to_dict())`
- `from_json(data: str) -> cls`: classmethod que faz `cls.from_dict(json.loads(data))`

---

### @komodo.equals_and_hashcode / @komodo.to_string

Aliases para `@komodo.eq` e `@komodo.to_str`, inspirados em Lombok:

```python
@komodo.equals_and_hashcode
@komodo.to_string
@komodo.constructor
class Item:
    id: int
    name: str

i1 = Item(1, "Widget")
i2 = Item(1, "Widget")

print(i1)           # Item(id=1, name='Widget')
print(i1 == i2)     # True
print(hash(i1) == hash(i2))  # True
```

Equivalem exatamente a `@komodo.eq` e `@komodo.to_str`.

---

## Design by Contract

Inspirado no modelo Hoare-triple (pré-condição / pós-condição / invariante).

```python
from nestifypy.komodo import contract
from nestifypy.komodo.contract import requires, ensures, invariant, ContractViolationError
```

### @contract

Aplica condições declarativas a funções e métodos.

```python
@contract(
    requires(lambda x, y: y != 0, "divisor must not be zero"),
    ensures(lambda result: result >= 0, "result must be non-negative"),
)
def safe_divide(x: float, y: float) -> float:
    return abs(x / y)

safe_divide(10.0, 0.0)
# ContractViolationError: [komodo.contract] precondition violated in 'safe_divide': 
#                         divisor must not be zero
```

**Ordem de execução:**
1. Pré-condições (`requires`)
2. Invariantes (antes) — `invariant`
3. Execução da função
4. Pós-condições (`ensures`)
5. Invariantes (depois) — `invariant`

Qualquer violação levanta `ContractViolationError` e interrompe a execução.

### requires()

**Pré-condição** — verificada antes da execução. Recebe os mesmos argumentos que a função.

```python
@contract(
    requires(lambda x: x >= 0, "x must be non-negative"),
)
def sqrt(x: float) -> float:
    return x ** 0.5

sqrt(-1.0)
# ContractViolationError: precondition violated in 'sqrt': x must be non-negative
```

### ensures()

**Pós-condição** — verificada após a execução. Recebe o valor de retorno.

```python
@contract(
    ensures(lambda result: result > 0, "absolute value must be positive"),
)
def absolute(x: float) -> float:
    if x == 0.0:
        return 0.1  # violaria se x era 0
    return abs(x)
```

### invariant()

**Invariante** — verificado antes e depois. Útil para manter estado consistente em métodos:

```python
class BankAccount:
    def __init__(self, balance: float):
        self.balance = balance

    @contract(
        invariant(lambda self: self.balance >= 0, "balance must never be negative"),
    )
    def withdraw(self, amount: float) -> None:
        self.balance -= amount

acct = BankAccount(100.0)
acct.withdraw(200.0)  
# ContractViolationError: invariant violated in 'withdraw' (after call): 
#                         balance must never be negative
```

### ContractViolationError

Exceção levantada quando qualquer contrato é violado.

```python
from nestifypy.komodo.contract import ContractViolationError

try:
    safe_divide(10.0, 0.0)
except ContractViolationError as e:
    print(e.kind)       # "precondition"
    print(e.func)       # "safe_divide"
    print(e.message)    # "divisor must not be zero"
    print(str(e))       # "[komodo.contract] precondition violated in ..."
```

**Atributos:**
- `kind`: um de `"precondition"`, `"postcondition"`, `"invariant"`
- `func`: nome qualificado da função (`__qualname__`)
- `message`: mensagem do contrato

---

## KomodoInspector

Ferramenta de introspecção para classes decoradas com `komodo`. Permite inspecionar quais features foram aplicadas, listar campos, e gerar resumos legíveis.

```python
from nestifypy.komodo import KomodoInspector

@komodo.logger
@komodo.builder
@komodo.data
class Order:
    id: int
    product: str
    quantity: int = 1

info = KomodoInspector(Order)
```

### Propriedades

**`features`** → `set[str]`  
Conjunto de features komodo aplicadas à classe.

```python
print(info.features)
# {'data', 'all_constructor', 'to_str', 'eq', 'builder', 'logger'}
```

**`fields`** → `dict[str, type]`  
Campos anotados diretamente na classe (exclui campos privados).

```python
print(info.fields)
# {'id': <class 'int'>, 'product': <class 'str'>, 'quantity': <class 'int'>}
```

**`defaults`** → `dict[str, Any]`  
Campos que possuem valores padrão no escopo da classe.

```python
print(info.defaults)
# {'quantity': 1}
```

**`generated_methods`** → `list[str]`  
Lista de métodos dunder e helpers conhecidos que foram adicionados por komodo.

```python
print(info.generated_methods)
# ['__init__', '__repr__', '__str__', '__eq__', '__hash__', 'Builder', 'builder', 'logger']
```

**`has_builder`** → `bool`  
`True` se `@komodo.builder` foi aplicado.

```python
print(info.has_builder)  # True
```

**`is_immutable`** → `bool`  
`True` se `@komodo.immutable` ou `@komodo.value` foi aplicada.

```python
print(info.is_immutable)  # False (a menos que @value tenha sido usado)
```

**`is_record`** → `bool`  
`True` se `@komodo.record` foi aplicado.

```python
print(info.is_record)  # False
```

### Métodos

**`contract_info(method_name: str) -> dict | None`**  
Retorna metadados de contrato para um método decorado com `@contract`.

```python
@komodo.data
class Calculator:
    @contract(requires(lambda x: x >= 0, "x must be non-negative"))
    def sqrt(self, x: float) -> float:
        return x ** 0.5

info = KomodoInspector(Calculator)
contracts = info.contract_info("sqrt")
# {'preconditions': [...], 'postconditions': [...], 'invariants': [...]}
```

**`summary() -> str`**  
Retorna um resumo formatado legível em tabela ASCII.

```python
print(info.summary())
```

Saída exemplo:

```
┌──────────────────────────────────────────────┐
│  komodo.inspect  →  Order                    │
├──────────────────────────────────────────────┤
│  Features   : builder, data, logger, ...     │
│  Fields     : id: int, product: str, ...     │
│  Defaults   : quantity=1                     │
│  Generated  : __init__, __repr__, ...        │
│  Immutable  : No                             │
│  Record     : No                             │
│  Has Builder: Yes                            │
└──────────────────────────────────────────────┘
```

---

## Composição de Decorators

Todos os decorators são composáveis. A ordem segue a regra do Python: **de baixo para cima** (bottom-up), ou seja, o decorator mais próximo ao nome da classe é aplicado primeiro.

**Ordem recomendada** (de cima para baixo na definição):

```python
@komodo.logger             # 5. último a aplicar
@komodo.copyable           # 4.
@komodo.builder            # 3.
@komodo.validated          # 2.
@komodo.data               # 1. aplicado primeiro (gera __init__ base)
class MyClass:
    field: type
```

**Por quê essa ordem?**
- `@komodo.data` deve ser base — gera `__init__`, `__repr__`, etc.
- `@komodo.validated` valida no `__init__`, então vem logo após
- `@komodo.builder` e `@komodo.copyable` operam sobre a estrutura gerada
- `@komodo.logger` é independente e vem no topo

### Exemplos práticos

**Entidade de domínio rica:**

```python
@komodo.logger
@komodo.copyable
@komodo.data
class Product:
    id: int
    name: str
    price: float
    active: bool = True

p = Product(1, "Widget", 9.99)
p2 = p.copy_with(price=7.99)
Product.logger.info("Price updated")
```

**Record com builder fluente e singulares:**

```python
@komodo.builder
@komodo.singular("tags")
@komodo.record
class Article:
    title: str
    author: str
    tags: list[str]

article = (
    Article.builder()
        .with_title("AST Metaprogramming in Python")
        .with_author("Alice")
        .tag("python")
        .tag("ast")
        .tag("metaprogramming")
        .build()
)

print(article.to_json())
# {"title": "AST Metaprogramming in Python", "author": "Alice", 
#  "tags": ["python", "ast", "metaprogramming"]}
```

**Value object imutável com contrato:**

```python
@komodo.value
class Currency:
    code: str
    symbol: str
    
    @contract(
        requires(lambda self: len(self.code) == 3, "code must be 3 chars"),
    )
    def __post_init__(self):
        pass

USD = Currency("USD", "$")
EUR = Currency("EUR", "€")

USD.code = "GBP"  # AttributeError: Currency is immutable
```

**Record com validação e builder:**

```python
@komodo.builder
@komodo.non_null
@komodo.record
class User:
    username: str
    email: str
    age: int = 18

user = (
    User.builder()
        .with_username("alice")
        .with_email("alice@example.com")
        .with_age(25)
        .build()
)

# Falha: campo obrigatório faltando
User.builder().with_email("bob@example.com").build()
# ValueError: User.Builder: required field 'username' was not set
```

---

## Comparação com Lombok

| Lombok (Java) | komodo (Python) | Notas |
|---|---|---|
| `@Data` | `@komodo.data` | `__init__`, `__repr__`, `__eq__`, `__hash__` |
| `@Value` | `@komodo.value` | Imutável + todos os métodos de `@data` |
| `@Builder` | `@komodo.builder` | Inner class `Builder` com API fluente |
| `@Singular` | `@komodo.singular("field")` | Append individual em campos lista |
| `@AllArgsConstructor` | `@komodo.constructor` | `__init__` gerado por anotações |
| `@RequiredArgsConstructor` | `@komodo.required_args_constructor` | Apenas campos obrigatórios |
| `@NoArgsConstructor` | `@komodo.no_args_constructor` | `__init__` sem argumentos |
| `@ToString` | `@komodo.to_string` | `__repr__` e `__str__` |
| `@EqualsAndHashCode` | `@komodo.equals_and_hashcode` | `__eq__` + `__hash__` |
| `@Slf4j` | `@komodo.logger` | Logger via stdlib `logging` |
| `@NonNull` | `@komodo.non_null` | Valida `None` em todos os args |
| `@With` | `@komodo.copyable` / `@komodo.withers` | `.copy_with()` e `.with_field()` |
| `@Getter` / `@Setter` | `@komodo.getter` / `@komodo.setter` | Python `@property` nativo |
| `@Accessors` | `@komodo.accessors()` | Getters, setters, withers configuráveis |
| `sealed` (Java 17) | Movido para `nestifypy.patterns` | — |
| IntelliJ `@Contract` | `@contract(requires, ensures, invariant)` | Pré/pós condições + invariantes |
| — | `@komodo.record` | All-in-one: data + immutable + serialization |
| — | `@komodo.copyable` | Clonagem superficial com sobrescrita |
| — | `@komodo.validated` | Type checking automático |

---

## Arquitectura Interna

```
┌─────────────────────────────────────────────────────────┐
│                    @komodo.decorator                     │
│                         ↓                                │
│   ┌─────────────────────────────────────────────────┐   │
│   │              ast_engine.py                       │   │
│   │  1. apply_generator(cls, generator)             │   │
│   │  2. Recupera cls.__komodo_ast__ se existir      │   │
│   │  3. Senão: inspect.getsource(cls) → ast.parse() │   │
│   │  4. Strip @komodo.* decorators da AST           │   │
│   │  5. generator(class_def, cls)  ← plugin         │   │
│   │  6. inject_logger_imports(tree)  ← se logger    │   │
│   │  7. ast.fix_missing_locations(tree)             │   │
│   │  8. compile(tree, "<komodo_ast>", "exec")       │   │
│   │  9. exec(code, module_namespace)                │   │
│   │ 10. cls.__komodo_ast__ = tree  (para stacking)  │   │
│   │ 11. cls.__komodo_meta__ = features              │   │
│   └─────────────────────────────────────────────────┘   │
│                         ↓                                │
│   ┌─────────────────────────────────────────────────┐   │
│   │          ast_generators/*.py                     │   │
│   │  • constructor.py   → __init__ (modes: all/req) │   │
│   │  • repr.py          → __repr__, __str__         │   │
│   │  • eq_hash.py       → __eq__, __hash__          │   │
│   │  • immutable.py     → __setattr__, __delattr__  │   │
│   │  • builder.py       → Builder inner class       │   │
│   │  • accessors.py     → @property, withers       │   │
│   │  • validation.py    → type checks, null checks  │   │
│   │  • logger.py        → logging.getLogger        │   │
│   │  • copyable.py      → copy(), copy_with()      │   │
│   │  • serialization.py → to_dict, from_dict, json │   │
│   │  • record.py        → all-in-one orchestrator   │   │
│   │  • utils.py         → helpers, metadata        │   │
│   └─────────────────────────────────────────────────┘   │
│                         ↓                                │
│              Classe Final (bytecode nativo)               │
│           c.__komodo_ast__ = AST preservada              │
│           c.__komodo_meta__ = features aplicadas         │
└─────────────────────────────────────────────────────────┘
```

### ast_builders.py

Helpers para construção de nós AST comuns:

- `make_arg(name, annotation)`: cria `ast.arg`
- `make_arguments(args, defaults)`: cria `ast.arguments`
- `make_function(name, args, body, returns)`: cria `ast.FunctionDef`
- `make_assign(target, value)`: cria `ast.Assign` simples
- `make_attribute_assign(obj, attr, value)`: cria `ast.Assign` com atributo
- `make_return(value)`: cria `ast.Return`
- `make_call(func_name, args, kwargs)`: cria `ast.Call`
- `make_raise(exc_name, msg)`: cria `ast.Raise`
- `make_if(test, body, orelse)`: cria `ast.If`

### ast_generators/utils.py

Utilidades compartilhadas:

- `get_fields_from_ast(class_def)`: extrai campos anotados
- `get_defaults_from_ast(class_def)`: extrai valores padrão
- `has_method(class_def, name)`: verifica se método existe
- `add_method(class_def, method_def)`: adiciona método respeitando overrides
- `get_komodo_meta(cls)`: lê `__komodo_meta__`
- `mark_komodo_meta(cls, feature)`: marca feature em `__komodo_meta__`

---

## Notas Técnicas

### Performance — Zero Overhead

Todas as transformações ocorrem uma única vez em tempo de importação (`import time`). As classes resultantes são bytecode puro — sem proxies, sem `__getattr__` dinâmico, sem metaclasses, sem wrappers. A performance de instanciação e acesso é idêntica a uma classe escrita manualmente.

```python
# Bytecode gerado é nativo:
import dis
@komodo.data
class Point:
    x: float
    y: float

dis.dis(Point.__init__)  # Idêntico a código escrito manualmente
```

### Metadados de komodo

Cada decorator marca a classe com features em `cls.__komodo_meta__`:

```python
@komodo.data
class Foo:
    x: int

print(Foo.__komodo_meta__)  # {'data', 'all_constructor', 'to_str', 'eq'}

@komodo.builder
@komodo.logger
class Bar:
    x: int

print(Bar.__komodo_meta__)  # {'all_constructor', 'builder', 'logger'}
```

Permite introspecção em runtime via `KomodoInspector`.

### Hash resiliente

O gerador de `__hash__` inclui fallback para `id(self)` quando os campos contêm tipos mutáveis (ex: `list`), evitando `TypeError: unhashable type`:

```python
@komodo.data
class Config:
    name: str
    options: list  # mutável!

c = Config("app", [1, 2, 3])
print(hash(c))  # funciona: usa id(self) como fallback
```

### PEP 563 — Anotações como strings

Quando um ficheiro usa `from __future__ import annotations`, o Komodo resolve anotações via `typing.get_type_hints()` (futura mejora).

### AST Stacking

Quando múltiplos decorators são empilhados, cada um herda e modifica a mesma AST:

```python
@komodo.logger      # ← recebe AST de @komodo.copyable
@komodo.copyable    # ← recebe AST de @komodo.data
@komodo.data        # ← gera AST inicial
class User:
    name: str
```

A AST é preservada em `cls.__komodo_ast__` entre decorators, evitando re-parsing do source (mais eficiente).

### Remoção de decorators

Durante o parse, todos os decorators `@komodo.*` são removidos da AST para evitar recursão infinita ao compilar:

```python
# Original:
@komodo.data
class Foo:
    x: int

# AST após strip:
class Foo:
    x: int
# (sem @komodo.data)
```

### Design by Contract — Erro Reporting

Os erros de contrato incluem stack trace limpo:

```python
ContractViolationError: [komodo.contract] precondition violated in 'safe_divide': 
                        divisor must not be zero
```

O `kind`, `func`, e `message` estão disponíveis como atributos para programação.

### Patterns Removidos

Os decorators `singleton`, `observable`, `delegate`, `mixin`, `sealed` e `deprecated` foram migrados para o pacote `nestifypy.patterns`. O Komodo foca exclusivamente em eliminação de boilerplate de modelagem de dados.

```python
from nestifypy.patterns import singleton, observable, sealed, deprecated
```

---

## Roadmap Futuro

- [ ] Resolução de PEP 563 (anotações como strings)
- [ ] Suporte a `typing.Generic` em builders
- [ ] Contrato pré/pós em properties
- [ ] Cache de AST para performance extrema
- [ ] Plugin system para geradores custom

---

*`nestifypy.komodo` — Lombok para Python com zero runtime overhead.*  
*Versão 0.2.1 — Setembro 2024*
