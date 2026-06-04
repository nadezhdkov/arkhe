# nestifypy.oop

Java-inspired Object-Oriented Programming utilities for Python.

`nestifypy.oop` fornece interfaces explícitas, classes abstratas, validação fail-fast de contratos e utilitários de herança que não existem nativamente no Python.

Ao contrário do módulo `abc` nativo, o nestifypy valida os contratos durante o **carregamento do módulo**, e não na instanciação — permitindo que erros de implementação sejam detectados na inicialização da aplicação.

---

## Instalação

```python
from nestifypy.oop import (
    interface,
    implements,
    abstract_class,
    abstract_method,
    override,
    final,
)
```

---

## Conceitos fundamentais

O módulo é construído em torno de dois conceitos:

**Interface** — define um contrato. Descreve o que uma classe deve fornecer, sem lógica de implementação ou estado.

**Classe abstrata** — define comportamento compartilhado. Pode conter métodos implementados, atributos e métodos abstratos que as subclasses devem sobrescrever.

---

## Referência da API

### `@interface`

Marca uma classe como interface.

Uma interface define um contrato de métodos e/ou atributos que qualquer classe implementadora deve fornecer. Interfaces podem herdar de outras interfaces, acumulando todos os requisitos.

```python
@interface
class ILogger:
    def log(self, message: str) -> None:
        pass
```

**Interfaces com atributos**

Além de métodos, interfaces podem exigir atributos anotados:

```python
@interface
class IUser:
    id: int
    username: str
```

**Herança de interfaces**

```python
@interface
class Entity:
    def get_id(self) -> int:
        pass

@interface
class IUser(Entity):
    def get_name(self) -> str:
        pass
```

Qualquer implementação de `IUser` deve implementar tanto `get_id` quanto `get_name`.

---

### `@implements(*interfaces)`

Declara que uma classe implementa uma ou mais interfaces.

A validação ocorre imediatamente na definição da classe. Se algum método ou atributo exigido estiver ausente, `InterfaceImplementationError` é levantada com uma mensagem descritiva.

```python
@implements(ILogger)
class ConsoleLogger:
    def log(self, message: str) -> None:
        print(message)
```

**Múltiplas interfaces**

```python
@interface
class Serializable:
    def serialize(self) -> str:
        pass

@interface
class Validatable:
    def validate(self) -> bool:
        pass

@implements(Serializable, Validatable)
class User:
    def serialize(self) -> str:
        return "{}"

    def validate(self) -> bool:
        return True
```

**Implementação inválida**

```python
@implements(ILogger)
class ConsoleLogger:
    pass
```

```
InterfaceImplementationError

Class ConsoleLogger does not implement:

 - log(message: str) -> None
```

A validação ocorre no carregamento do módulo, não na instanciação do objeto.

---

### `@abstract_class`

Marca uma classe como abstrata.

Classes abstratas:

- Não podem ser instanciadas diretamente.
- Podem conter métodos concretos, atributos e construtores.
- Devem declarar métodos abstratos com `@abstract_method`.

As subclasses são validadas na definição: se algum `@abstract_method` não for implementado, `AbstractMethodError` é levantada imediatamente.

```python
@abstract_class
class Repository:

    def __init__(self, table: str):
        self.table = table

    def connect(self):
        print(f"Connected to {self.table}")

    @abstract_method
    def save(self, data):
        pass
```

**Implementação válida**

```python
class UserRepository(Repository):

    def save(self, data):
        print(data)
```

**Implementação inválida**

```python
class UserRepository(Repository):
    pass
```

```
AbstractMethodError

Class UserRepository must implement:

 - save(data)
```

**Instanciação direta bloqueada**

```python
repo = Repository()
```

```
InstantiationError

Cannot instantiate abstract class Repository
```

---

### `@abstract_method`

Marca um método dentro de um `@abstract_class` como abstrato.

As subclasses devem sobrescrever esse método. A validação é feita na definição da classe via `__init_subclass__`.

```python
@abstract_class
class BaseService:

    @abstract_method
    def execute(self):
        pass
```

Se o método abstrato for chamado diretamente (ex: via `super()`), `NotImplementedError` é levantada em tempo de execução.

---

### `@override`

Marca um método como intencionalmente sobrescrevendo um método pai.

Se nenhuma classe pai definir um método com o mesmo nome, `OverrideError` é levantada na definição da classe.

```python
class UserRepository(Repository):

    @override
    def save(self, data):
        print(data)
```

**Método inexistente no pai**

```python
class UserRepository(Repository):

    @override
    def delete(self):
        pass
```

```
OverrideError

Method delete does not override any parent method
```

`@override` é validado automaticamente em subclasses de `@abstract_class`. Para hierarquias sem `@abstract_class`, utilize `_OverrideValidatingMeta` como metaclass.

---

### `@final`

Marca uma classe como não-herdável.

Qualquer tentativa de criar uma subclasse de uma classe `@final` levanta `FinalClassError` na definição.

```python
@final
class Config:
    pass
```

**Tentativa de herança**

```python
class ExtendedConfig(Config):
    pass
```

```
FinalClassError

Class Config cannot be extended
```

A classe `@final` pode ser normalmente instanciada.

---

## Exceções

| Exceção | Quando é levantada |
|---|---|
| `InterfaceImplementationError` | Método ou atributo exigido pela interface está ausente na implementação |
| `AbstractMethodError` | Subclasse não implementou um `@abstract_method` |
| `InstantiationError` | Tentativa de instanciar diretamente um `@abstract_class` |
| `OverrideError` | `@override` aplicado em método sem correspondente na classe pai |
| `FinalClassError` | Tentativa de herdar de uma classe `@final` |

Todas as exceções são levantadas em tempo de definição de classe (fail-fast), com exceção de `InstantiationError`, que ocorre na chamada do construtor.

---

## Comparação com Python nativo

| Recurso | nestifypy.oop | Python nativo (`abc`) |
|---|---|---|
| Interfaces explícitas | `@interface` | Não há equivalente |
| Validação de implementação | `@implements` — automático | Não há equivalente |
| Métodos abstratos | `@abstract_method` | `@abstractmethod` |
| Validação fail-fast | No carregamento do módulo | Apenas na instanciação |
| Mensagens de erro descritivas | Sim, com assinaturas | Básico |
| Herança de interfaces | Sim, acumulativa | Não há equivalente |
| Atributos de interface | Sim | Não há equivalente |
| `@override` com validação | Sim | Não há equivalente |
| `@final` | Sim | Não há equivalente |

---

## Exemplo completo

```python
from nestifypy.oop import (
    interface,
    implements,
    abstract_class,
    abstract_method,
    override,
    final,
)


@interface
class ILogger:
    def log(self, message: str) -> None:
        pass


@interface
class IHealthCheck:
    def is_healthy(self) -> bool:
        pass


@abstract_class
class BaseService:

    def startup(self):
        print("Service started")

    @abstract_method
    def execute(self):
        pass


@implements(ILogger)
class ConsoleLogger:

    def log(self, message: str) -> None:
        print(message)


@implements(ILogger, IHealthCheck)
class UserService(BaseService):

    def log(self, message: str) -> None:
        print(f"[UserService] {message}")

    def is_healthy(self) -> bool:
        return True

    @override
    def execute(self):
        print("Executing user logic")


@final
class AppConfig:
    debug: bool = False
    version: str = "1.0.0"
```

---

## Notas de implementação

**Registro de interfaces**

O `_INTERFACE_REGISTRY` é um dicionário global que persiste os requisitos de cada interface (métodos e atributos). A herança de interfaces acumula os requisitos dos pais antes de adicionar os próprios.

**Validação de `@override`**

A validação de `@override` é integrada ao `__init_subclass__` de `@abstract_class`. Para hierarquias que não usam `@abstract_class`, a metaclass `_OverrideValidatingMeta` pode ser usada diretamente.

**Compatibilidade**

O módulo é compatível com Python 3.10+ e não depende de frameworks externos. Pode ser usado independentemente ou em conjunto com outros módulos do nestifypy como Collections, Flow, Time, Money ou Ignite.
