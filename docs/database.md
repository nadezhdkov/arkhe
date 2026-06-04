# arkhe.database

> Um toolkit SQLite fluente, leve e isolado por domínio para Python.

O módulo `arkhe.database` oferece uma API de query builder estilo fluente sobre SQLite, com mapeamento de entidades via decorators, transações explícitas e resultados tipados que nunca levantam exceção inesperada.

**Engine:** SQLite via `sqlite3` (stdlib)  
**Python:** 3.10+  
**Dependencies:** nenhuma (stdlib only)

---

## Índice

- [Instalação](#instalação)
- [Quickstart](#quickstart)
- [Conexão](#conexão)
- [Mapeamento de Entidades](#mapeamento-de-entidades)
  - [@db_entity](#db_entity)
  - [db_column()](#db_column)
- [Schema](#schema)
  - [DB.create_table()](#dbcreate_table)
- [Queries](#queries)
  - [SELECT](#select)
  - [INSERT](#insert)
  - [UPDATE](#update)
  - [DELETE](#delete)
- [Transações](#transações)
- [DBResult — Execução Segura](#dbresult--execução-segura)
- [SQL Direto](#sql-direto)
- [Referência da API](#referência-da-api)
- [Arquitetura Interna](#arquitetura-interna)
- [Notas Técnicas](#notas-técnicas)

---

## Instalação

O módulo faz parte da biblioteca `arkhe`:

```
arkhe/
└── database/
    ├── __init__.py
    ├── _connection.py   # singleton de conexão SQLite
    ├── _db.py           # facade pública DB
    ├── _meta.py         # decorators @db_entity e db_column()
    ├── _schema.py       # geração de CREATE TABLE
    ├── _select.py       # SelectQuery
    ├── _insert.py       # InsertQuery
    ├── _update.py       # UpdateQuery
    ├── _delete.py       # DeleteQuery
    └── _result.py       # DBResult
```

Importação:

```python
from arkhe.database import DB, db_entity, db_column, DBResult
```

---

## Quickstart

```python
from dataclasses import dataclass
from arkhe.database import DB, db_entity, db_column

# 1. Conectar
DB.connect("app.db")

# 2. Definir entidade
@db_entity("users")
@dataclass
class User:
    id:    int = db_column(primary_key=True)
    email: str = db_column(unique=True)
    name:  str = db_column()

# 3. Criar tabela
DB.create_table(User)

# 4. Inserir
DB.insert_into("users").values(name="Alice", email="alice@example.com").execute()

# 5. Consultar
users = DB.select("*").from_table("users").into(User)
print(users)  # [User(id=1, email='alice@example.com', name='Alice')]
```

---

## Conexão

### DB.connect()

```python
DB.connect(path: str, wal: bool = False) -> None
```

Abre (ou reabre) a conexão SQLite no caminho especificado.

```python
DB.connect("app.db")               # arquivo local
DB.connect(":memory:")             # banco em memória (testes)
DB.connect("app.db", wal=True)     # WAL mode para melhor concorrência
```

**`wal=True`**: ativa `PRAGMA journal_mode=WAL`. Recomendado para aplicações com múltiplas leituras concorrentes.

Internamente usa `isolation_level=None` — o controle de transações é totalmente explícito via `BEGIN`/`COMMIT`/`ROLLBACK`.

### DB.close()

```python
DB.close() -> None
```

Fecha a conexão atual. Após isso, qualquer operação levantará `RuntimeError` até que `DB.connect()` seja chamado novamente.

---

## Mapeamento de Entidades

### @db_entity

```python
@db_entity(table: str)
```

Marca uma classe como entidade mapeada para a tabela `table`. Não executa SQL — apenas registra metadados na classe.

```python
@db_entity("products")
class Product:
    ...
```

**Metadados definidos na classe:**

| Atributo | Valor |
|---|---|
| `__nestify_db_entity__` | `True` |
| `__nestify_db_table__` | Nome da tabela passado ao decorator |

Funciona com qualquer tipo de classe: `dataclass`, `@komodo.data`, classe simples, etc.

### db_column()

```python
db_column(
    primary_key: bool = False,
    unique:      bool = False,
    nullable:    bool = True,
) -> _ColumnMeta
```

Anota um campo com metadados de coluna. Deve ser usado como valor default do atributo anotado.

```python
@db_entity("users")
@dataclass
class User:
    id:    int = db_column(primary_key=True)
    email: str = db_column(unique=True)
    name:  str = db_column(nullable=False)
    bio:   str = db_column()               # nullable por default
```

**Parâmetros:**

| Parâmetro | Default | Efeito no DDL |
|---|---|---|
| `primary_key` | `False` | `PRIMARY KEY` |
| `unique` | `False` | `UNIQUE` |
| `nullable` | `True` | `NOT NULL` quando `False` (ignorado em PKs) |

O descriptor `_ColumnMeta` é transparente — não interfere em leituras e escritas normais do atributo.

**Campos sem `db_column()`:** campos anotados sem `db_column()` são incluídos na tabela com a afinidade SQLite correspondente ao tipo Python, sem constraints adicionais.

---

## Schema

### DB.create_table()

```python
DB.create_table(entity_cls: Type) -> None
```

Gera e executa um `CREATE TABLE IF NOT EXISTS` a partir dos metadados da entidade.

```python
DB.create_table(User)
```

**Mapeamento de tipos Python → SQLite:**

| Python | SQLite |
|---|---|
| `int` | `INTEGER` |
| `float` | `REAL` |
| `str` | `TEXT` |
| `bytes` | `BLOB` |
| `bool` | `INTEGER` |
| qualquer outro | `TEXT` |

**SQL gerado para o exemplo do Quickstart:**

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE,
    name TEXT
)
```

Levanta `RuntimeError` se a classe não tiver nenhuma coluna definida (nem via `db_column()` nem via anotações de tipo).

---

## Queries

Todas as queries são construídas de forma fluente e só executam SQL ao chamar um método terminal (`execute()`, `first()`, `into()` ou suas variantes `_safe`).

---

### SELECT

```python
DB.select(*columns: str) -> SelectQuery
```

Inicia uma query `SELECT`. Sem colunas, seleciona `*`.

#### Métodos de construção

```python
.from_table(table: str)              # obrigatório — define a tabela
.where(condition: str, *params)      # adiciona cláusula WHERE (AND entre múltiplas)
.order_by(column: str, dir: str)     # ORDER BY — dir: "ASC" ou "DESC"
.limit(n: int)                       # LIMIT
.offset(n: int)                      # OFFSET (requer LIMIT ou usa LIMIT -1)
```

#### Métodos terminais

| Método | Retorno | Descrição |
|---|---|---|
| `execute()` | `list[dict]` | Executa e retorna lista de dicts |
| `first()` | `dict \| None` | Retorna o primeiro resultado ou `None` |
| `into(cls)` | `list[T]` | Mapeia cada linha para `cls(**row)` |
| `execute_safe()` | `DBResult` | `execute()` sem levantar exceção |
| `first_safe()` | `DBResult` | `first()` sem levantar exceção |
| `into_safe(cls)` | `DBResult` | `into()` sem levantar exceção |

#### Exemplos

```python
# Todos os registros
rows = DB.select("*").from_table("users").execute()
# [{'id': 1, 'name': 'Alice', 'email': 'alice@example.com'}, ...]

# Com filtro e ordenação
rows = (
    DB.select("id", "name")
      .from_table("users")
      .where("active = ?", True)
      .order_by("name", "ASC")
      .limit(10)
      .offset(20)
      .execute()
)

# Primeiro resultado
user = DB.select("*").from_table("users").where("id = ?", 1).first()

# Mapeado para objeto
users: list[User] = DB.select("*").from_table("users").into(User)

# Múltiplas condições WHERE — combinadas com AND
rows = (
    DB.select("*")
      .from_table("orders")
      .where("status = ?", "pending")
      .where("total > ?", 100)
      .execute()
)
# WHERE (status = ?) AND (total > ?)
```

---

### INSERT

```python
DB.insert_into(table: str) -> InsertQuery
```

#### Métodos

```python
.values(**kwargs)   # colunas e valores a inserir
.execute()          # executa e retorna o rowid inserido (int)
.execute_safe()     # retorna DBResult
```

#### Exemplos

```python
# Inserção simples
row_id = (
    DB.insert_into("users")
      .values(name="Bob", email="bob@example.com")
      .execute()
)
print(row_id)  # 2

# Múltiplos campos
DB.insert_into("products").values(
    name="Widget",
    price=9.99,
    stock=100,
    active=True,
).execute()
```

Levanta `RuntimeError` se `values()` for chamado sem colunas.

---

### UPDATE

```python
DB.update(table: str) -> UpdateQuery
```

#### Métodos

```python
.set(**kwargs)                      # colunas e novos valores
.where(condition: str, *params)     # filtro (AND entre múltiplos)
.execute()                          # executa e retorna rowcount (int)
.execute_safe()                     # retorna DBResult
```

#### Exemplos

```python
# Atualização simples
affected = (
    DB.update("users")
      .set(name="Alice Smith")
      .where("id = ?", 1)
      .execute()
)
print(affected)  # 1

# Múltiplos campos
DB.update("products") \
  .set(price=7.99, stock=50) \
  .where("id = ?", 42) \
  .execute()

# Sem WHERE — atualiza todos os registros
DB.update("users").set(active=False).execute()
```

Levanta `RuntimeError` se `set()` for chamado sem colunas.

---

### DELETE

```python
DB.delete_from(table: str) -> DeleteQuery
```

#### Métodos

```python
.where(condition: str, *params)     # filtro (AND entre múltiplos)
.execute()                          # executa e retorna rowcount (int)
.execute_safe()                     # retorna DBResult
```

#### Exemplos

```python
# Deletar por ID
affected = DB.delete_from("users").where("id = ?", 1).execute()

# Deletar com múltiplas condições
DB.delete_from("logs") \
  .where("created_at < ?", "2024-01-01") \
  .where("level = ?", "debug") \
  .execute()

# Sem WHERE — apaga todos os registros
DB.delete_from("temp_data").execute()
```

---

## Transações

```python
with DB.transaction():
    ...
```

Envolve um bloco em uma transação `BEGIN` → `COMMIT`. Em caso de qualquer exceção, executa `ROLLBACK` automaticamente e re-levanta o erro.

```python
with DB.transaction():
    DB.update("accounts").set(balance=400).where("id = ?", 1).execute()
    DB.update("accounts").set(balance=1100).where("id = ?", 2).execute()
    # Se qualquer linha falhar: rollback automático
```

**Re-entrância:** transações aninhadas são seguras. Se um bloco `with DB.transaction()` for chamado dentro de outro que já está ativo, o bloco interno é um no-op — o controle permanece com o bloco externo.

```python
def transfer(from_id, to_id, amount):
    with DB.transaction():             # abre transação
        debit(from_id, amount)
        credit(to_id, amount)          # mesmo que credit() use DB.transaction() internamente, não conflita

with DB.transaction():
    transfer(1, 2, 100)                # re-entrância segura
    transfer(3, 4, 200)
```

---

## DBResult — Execução Segura

Todos os métodos de query possuem uma variante `_safe` que retorna um `DBResult` em vez de levantar exceções. Ideal para fluxos onde a falha é esperada e deve ser tratada programaticamente.

```python
result = DB.insert_into("users").values(email="dup@example.com").execute_safe()

if result.is_success:
    print(f"Inserido com rowid {result.data}")
else:
    print(f"Erro: {result.error_message}")
```

### Atributos de DBResult

| Atributo | Tipo | Descrição |
|---|---|---|
| `is_success` | `bool` | `True` se a operação foi bem-sucedida |
| `data` | `Any` | Valor de retorno da operação (rowid, rowcount, lista de rows, etc.) |
| `error` | `Exception \| None` | A exceção original, se houver |
| `error_message` | `str \| None` | `str(error)` para exibição rápida |

### Variantes _safe disponíveis

| Query | Método _safe | `data` em sucesso |
|---|---|---|
| SELECT | `execute_safe()` | `list[dict]` |
| SELECT | `first_safe()` | `dict \| None` |
| SELECT | `into_safe(cls)` | `list[T]` |
| INSERT | `execute_safe()` | `int` (rowid) |
| UPDATE | `execute_safe()` | `int` (rowcount) |
| DELETE | `execute_safe()` | `int` (rowcount) |

### Exemplo completo

```python
result = (
    DB.select("*")
      .from_table("users")
      .where("id = ?", 999)
      .first_safe()
)

if result.is_success:
    user = result.data  # None se não encontrado
else:
    print(result.error_message)
```

---

## SQL Direto

Para casos onde o query builder não expressa o necessário:

```python
DB.execute_raw(sql: str, *params) -> list[dict]
```

```python
rows = DB.execute_raw(
    "SELECT u.name, COUNT(o.id) as total "
    "FROM users u LEFT JOIN orders o ON o.user_id = u.id "
    "GROUP BY u.id "
    "HAVING total > ?",
    5
)
```

Retorna lista de `dict`. Não possui variante `_safe` — trate exceções manualmente se necessário.

---

## Referência da API

### DB (facade principal)

| Método | Retorno | Descrição |
|---|---|---|
| `DB.connect(path, wal=False)` | `None` | Abre conexão SQLite |
| `DB.close()` | `None` | Fecha conexão |
| `DB.transaction()` | context manager | Bloco de transação |
| `DB.select(*columns)` | `SelectQuery` | Inicia SELECT |
| `DB.insert_into(table)` | `InsertQuery` | Inicia INSERT |
| `DB.update(table)` | `UpdateQuery` | Inicia UPDATE |
| `DB.delete_from(table)` | `DeleteQuery` | Inicia DELETE |
| `DB.create_table(cls)` | `None` | Cria tabela a partir de entidade |
| `DB.execute_raw(sql, *params)` | `list[dict]` | SQL arbitrário |

### SelectQuery

| Método | Retorno | Tipo |
|---|---|---|
| `.from_table(table)` | `SelectQuery` | builder |
| `.where(condition, *params)` | `SelectQuery` | builder |
| `.order_by(column, dir)` | `SelectQuery` | builder |
| `.limit(n)` | `SelectQuery` | builder |
| `.offset(n)` | `SelectQuery` | builder |
| `.execute()` | `list[dict]` | terminal |
| `.first()` | `dict \| None` | terminal |
| `.into(cls)` | `list[T]` | terminal |
| `.execute_safe()` | `DBResult` | terminal |
| `.first_safe()` | `DBResult` | terminal |
| `.into_safe(cls)` | `DBResult` | terminal |

### InsertQuery

| Método | Retorno | Tipo |
|---|---|---|
| `.values(**kwargs)` | `InsertQuery` | builder |
| `.execute()` | `int` (rowid) | terminal |
| `.execute_safe()` | `DBResult` | terminal |

### UpdateQuery

| Método | Retorno | Tipo |
|---|---|---|
| `.set(**kwargs)` | `UpdateQuery` | builder |
| `.where(condition, *params)` | `UpdateQuery` | builder |
| `.execute()` | `int` (rowcount) | terminal |
| `.execute_safe()` | `DBResult` | terminal |

### DeleteQuery

| Método | Retorno | Tipo |
|---|---|---|
| `.where(condition, *params)` | `DeleteQuery` | builder |
| `.execute()` | `int` (rowcount) | terminal |
| `.execute_safe()` | `DBResult` | terminal |

---

## Arquitetura Interna

```
┌────────────────────────────────────────────────────────┐
│                   arkhe.database                    │
│                                                        │
│   DB (facade)                                          │
│     ├── DB.connect() / DB.close()                      │
│     ├── DB.transaction()                               │
│     ├── DB.select()    → SelectQuery                   │
│     ├── DB.insert_into() → InsertQuery                 │
│     ├── DB.update()    → UpdateQuery                   │
│     ├── DB.delete_from() → DeleteQuery                 │
│     ├── DB.create_table() → _schema.create_table()     │
│     └── DB.execute_raw()                               │
│                                                        │
│   _Connection (singleton interno)                      │
│     ├── connect() / close()                            │
│     ├── cursor() / commit() / rollback()               │
│     └── transaction() — context manager re-entrante    │
│                                                        │
│   _meta                                                │
│     ├── @db_entity(table)  → __nestify_db_table__      │
│     └── db_column(...)     → _ColumnMeta descriptor    │
│                                                        │
│   _schema                                              │
│     └── _build_create_table_sql() → CREATE TABLE DDL   │
│                                                        │
│   DBResult                                             │
│     ├── DBResult.success(data)                         │
│     └── DBResult.failure(exc)                          │
└────────────────────────────────────────────────────────┘
```

### _Connection

Singleton interno — nunca instanciado diretamente. Acessível via `_connection()`. Usa `isolation_level=None` para ter controle total sobre transações. O método `transaction()` detecta re-entrância via `conn.in_transaction` e age como no-op quando já há uma transação ativa.

### Query Builders

Cada classe de query (`SelectQuery`, `InsertQuery`, etc.) acumula estado internamente e só toca o banco ao chamar um método terminal. Todos os parâmetros são passados via `?` placeholders para prevenir SQL injection.

---

## Notas Técnicas

### Parameterização — SQL Injection

Todos os valores passados via `.where()`, `.values()`, `.set()` e `execute_raw()` são enviados como parâmetros posicionais `?` ao `sqlite3`, nunca interpolados na string SQL. Nomes de tabelas e colunas não são parametrizados — use apenas valores confiáveis nesses campos.

```python
# Seguro — valor parametrizado
DB.select("*").from_table("users").where("email = ?", user_input).execute()

# Não faça — tabela/coluna nunca deve vir de input não confiável
DB.select("*").from_table(user_input)  # evitar
```

### WAL Mode

```python
DB.connect("app.db", wal=True)
```

Ativa `PRAGMA journal_mode=WAL`. Recomendado para aplicações que realizam leituras e escritas concorrentes — permite múltiplos leitores simultâneos com um escritor sem bloqueio.

### Banco em Memória (testes)

```python
DB.connect(":memory:")
DB.create_table(User)
# banco descartado ao fechar ou ao final do processo
```

Ideal para testes unitários isolados — sem arquivos temporários.

### .into(cls) e compatibilidade

O método `.into(cls)` faz `cls(**row)` para cada linha retornada. A classe precisa aceitar os campos como kwargs. Funciona nativamente com `@dataclass`, `@komodo.data`, `@komodo.all_args_constructor` e qualquer classe com `__init__` compatível.

```python
@db_entity("points")
@dataclass
class Point:
    x: float
    y: float

points: list[Point] = DB.select("x", "y").from_table("points").into(Point)
```

### Campos sem db_column()

Campos anotados na classe que não usam `db_column()` são incluídos no `CREATE TABLE` com a afinidade correspondente ao tipo, sem nenhuma constraint. Útil para campos simples onde PRIMARY KEY, UNIQUE ou NOT NULL não são necessários.

```python
@db_entity("logs")
@dataclass
class Log:
    id:      int = db_column(primary_key=True)
    message: str   # incluído como TEXT sem constraints
    level:   str   # incluído como TEXT sem constraints
```

---

*`arkhe.database` — SQLite fluente com zero dependencies.*
