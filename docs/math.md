# arkhe.math

Framework matemático avançado do ecossistema NestifyPy. Unifica aritmética de precisão arbitrária, matemática simbólica, álgebra linear, geometria, estatística, conversão de unidades e moedas em uma única API consistente e fluente.

## Instalação de dependências opcionais

O módulo funciona sem dependências externas, mas algumas funcionalidades requerem pacotes adicionais:

```
pip install sympy    # matemática simbólica (Symbol, Expr)
pip install mpmath   # Pi e sqrt de altíssima precisão
```

## Importação

```python
from arkhe.math import *
```

---

## Tipos Numéricos

Todos os tipos numéricos compartilham uma API fluente encadeável e retornam `FailureResult` em operações inválidas — sem lançar exceções.

### API comum a todos os tipos

```python
# Aritmética fluente
.add(other)         # adição
.subtract(other)    # subtração
.multiply(other)    # multiplicação
.divide(other)      # divisão segura — retorna FailureResult se divisor == 0
.mod(other)         # módulo seguro
.pow(exp)           # potenciação
.negate()           # negação
.abs()              # valor absoluto

# Precisão local
.precision(digits)  # retorna o valor como Decimal com N dígitos de precisão

# Extração
.value()            # valor Python nativo subjacente (int, Decimal, Fraction...)
.to_int()           # converte para int
.to_float()         # converte para float
.to_decimal()       # converte para Decimal

# Estado
.is_success()       # True para todos os tipos válidos
.is_failure()       # True apenas para FailureResult

# Operadores nativos também funcionam
a + b   a - b   a * b   a / b   a % b   a ** b   -a   abs(a)
```

---

### `Number`

Tipo numérico universal. Seleciona automaticamente a melhor representação interna (`int`, `Decimal` ou `Fraction`) de acordo com o valor fornecido.

```python
Number(10)                        # int
Number(0.5)                       # Decimal (evita imprecisão de float)
Number("0.1")                     # Decimal
Number("1/3")                     # Fraction
Number("999999999999999999999")   # int grande
```

Encadeamento:

```python
result = (
    Number(100)
    .add(50)
    .multiply(2)
    .divide(5)
)
# Number(60.0)
```

---

### `BigNumber`

Otimizado para inteiros arbitrariamente grandes. Inclui operações extras de teoria dos números.

```python
n = BigNumber("999999999999999999999999999999")
n.pow(1000)
```

Métodos exclusivos:

```python
.factorial()        # n!
.gcd(other)         # máximo divisor comum
.lcm(other)         # mínimo múltiplo comum
.is_prime()         # teste de primalidade
.digits()           # número de dígitos decimais
```

---

### `BigDecimal`

Decimais de alta precisão baseados em `decimal.Decimal`. Ideal para cálculos financeiros e científicos que exigem controle fino de arredondamento.

```python
price = BigDecimal("19.99")
tax   = BigDecimal("0.17")

price.multiply(tax)   # BigDecimal("3.3983")
```

Métodos exclusivos:

```python
.round(places)   # arredonda para N casas decimais
.floor()         # arredonda para baixo
.ceil()          # arredonda para cima
```

---

### `Fraction`

Aritmética racional exata, sem nenhum arredondamento de ponto flutuante.

```python
Fraction("1/3").add("1/6")   # Fraction(1/2)
Fraction("5/7").multiply(7)  # Fraction(5)
```

Propriedades e métodos exclusivos:

```python
.numerator           # numerador (int)
.denominator         # denominador (int)
.simplify()          # fração simplificada
.to_mixed()          # retorna (parte_inteira, fracao_propria)
```

---

### `Complex`

Números complexos com API fluente.

```python
c = Complex(2, 5)   # 2 + 5j
```

Propriedades e métodos exclusivos:

```python
.real               # parte real (float)
.imag               # parte imaginária (float)
.conjugate()        # conjugado complexo
.magnitude()        # módulo |z| — retorna Number
.phase()            # argumento em radianos — retorna Number
```

---

### `FailureResult`

Retornado por operações que seriam inválidas (divisão por zero, módulo por zero). Compatível com o módulo `Try`.

```python
result = Number(10).divide(0)

result.is_failure()   # True
result.is_success()   # False
result.get_error()    # DivisionByZeroError("Division by zero")
```

Qualquer operação encadeada num `FailureResult` continua retornando o mesmo `FailureResult`, propagando o erro silenciosamente pela cadeia.

Integração com `Try`:

```python
from arkhe.trying import Try

result = (
    Try.of(lambda: Number("abc"))
       .map(lambda n: n.add(10))
       .or_else(Number(0))
)
```

---

## Precisão Global

Define a precisão padrão para todas as operações `Decimal` do processo:

```python
Math.precision(1000)
```

Precisão local (afeta apenas o valor em questão):

```python
Number("1").divide(7).precision(500)
```

---

## `Math` — Motor Matemático

Ponto de entrada para avaliação de expressões, estatística, computação científica, finanças e probabilidade. Todos os métodos são `classmethod`.

### Avaliação de Expressões

`Math.eval()` analisa e avalia expressões matemáticas de forma **segura** via análise AST — nenhum `eval()` nativo é usado, de modo que código arbitrário não pode ser executado.

```python
Math.eval("10 + 5")                          # 15
Math.eval("(15 + 8) * sqrt(144)")            # 276
Math.eval("2 ** 10")                         # 1024
Math.eval("20 % 3")                          # 2
Math.eval("x * y + 10", x=5, y=3)           # 25
Math.eval("pi * 2")                          # 6.283185307179586
```

Operadores suportados: `+` `-` `*` `/` `%` `**` `//`

Funções disponíveis nas expressões:

| Função | Descrição |
|---|---|
| `sqrt(x)` | raiz quadrada |
| `pow(x, y)` | potenciação |
| `abs(x)` | valor absoluto |
| `round(x)` | arredondamento |
| `floor(x)` / `ceil(x)` | piso / teto |
| `sin(x)` / `cos(x)` / `tan(x)` | trigonometria |
| `asin(x)` / `acos(x)` / `atan(x)` / `atan2(y, x)` | trigonometria inversa |
| `log(x)` / `log2(x)` / `log10(x)` | logaritmos |
| `exp(x)` | exponencial natural |
| `min(a, b)` / `max(a, b)` | mínimo / máximo |
| `factorial(n)` | fatorial |
| `gcd(a, b)` | máximo divisor comum |
| `hypot(x, y)` | hipotenusa |
| `degrees(r)` / `radians(d)` | conversão de ângulos |

Constantes disponíveis nas expressões:

| Constante | Valor |
|---|---|
| `pi` | 3.14159… |
| `e` | 2.71828… |
| `tau` | 6.28318… |
| `phi` | 1.61803… (razão áurea) |
| `inf` | infinito |

---

### Estatística

```python
data = [10, 20, 30, 40, 50]

Math.mean(data)       # média aritmética
Math.median(data)     # mediana
Math.mode(data)       # moda
Math.variance(data)   # variância amostral
Math.std(data)        # desvio padrão amostral
Math.pvariance(data)  # variância populacional
Math.pstd(data)       # desvio padrão populacional
Math.quantiles(data, n=4)  # quartis (n=4) ou percentis (n=100)
```

---

### Computação Científica

```python
Math.pi(precision=100)       # Pi com 100 dígitos decimais (Decimal)
Math.sqrt(2, precision=50)   # √2 com 50 dígitos (Decimal)
```

Métodos numéricos para encontrar raízes de funções:

```python
# Método de Newton-Raphson
Math.newton(
    f=lambda x: x**2 - 2,
    x0=1.0,
    tol=1e-9,
    max_iter=1000,
)
# → 1.4142135623730951

# Método da Bisseção
Math.bisection(
    f=lambda x: x**2 - 2,
    a=1.0,
    b=2.0,
)

# Método da Secante
Math.secant(
    f=lambda x: x**2 - 2,
    x0=1.0,
    x1=2.0,
)
```

---

### Matemática Financeira

```python
# Juros compostos — retorna montante final
Math.compound_interest(
    principal=1000,
    rate=0.05,      # 5% ao ano
    periods=10,     # anos
    n=1,            # capitalizações por ano (padrão: 1)
)
# → 1628.89

# Juros simples — retorna montante total
Math.simple_interest(principal=1000, rate=0.05, time=3)
# → 1150.0

# Prestação de empréstimo (sistema Price)
result = Math.loan(
    principal=10000,
    annual_rate=0.12,
    months=12,
)
result["monthly_payment"]   # prestação mensal
result["total_paid"]        # total pago
result["total_interest"]    # total de juros

# Valor presente / futuro
Math.present_value(future_value=1000, rate=0.05, periods=5)
Math.future_value(present_value=1000, rate=0.05, periods=5)
```

---

### Probabilidade e Combinatória

```python
Math.combinations(10, 3)      # C(10,3) = 120
Math.permutations(10, 3)      # P(10,3) = 720
Math.probability(3, 10)       # 3/10 = 0.3
Math.factorial(10)            # 3628800
Math.gcd(48, 18)              # 6
Math.lcm(4, 6, 10)            # 60
```

---

## Matemática Simbólica

Requer `sympy` instalado. Se não estiver, as operações lançam `ImportError` com mensagem clara.

### `Symbol`

```python
x = Symbol("x")
y = Symbol("y")
```

Suporta todos os operadores aritméticos para construção de expressões: `+`, `-`, `*`, `/`, `**`.

### `Expr`

Expressão simbólica construída a partir de `Symbol`.

```python
x = Symbol("x")
expr = x**2 + 5*x + 6
```

Métodos disponíveis:

```python
expr.solve()                   # raízes da equação expr = 0  →  [-3, -2]
expr.derivative()              # derivada primeira  →  2*x + 5
expr.derivative(order=2)       # derivada segunda   →  2
expr.integrate()               # integral indefinida
expr.integrate(lower=0, upper=1)  # integral definida

expr.simplify()                # simplifica
expr.expand()                  # expande
expr.factor()                  # fatoriza  →  (x + 2)*(x + 3)
expr.collect(x)                # agrupa termos por símbolo

expr.substitute(x=2)          # substitui e retorna valor numérico
expr.evaluate(precision=15)   # avaliação numérica em float
```

Exemplo completo:

```python
x = Symbol("x")

quadratica = x**2 + 5*x + 6
print(quadratica.solve())       # [-3, -2]
print(quadratica.factor())      # (x + 2)*(x + 3)
print(quadratica.derivative())  # 2*x + 5

cubica = x**3 - 6*x**2 + 11*x - 6
print(cubica.solve())           # [1, 2, 3]
```

---

## Álgebra Linear

### `Vector`

Vetor n-dimensional.

```python
v = Vector(1, 2, 3)
w = Vector(4, 5, 6)
```

```python
v.length()              # norma euclidiana (magnitude)
v.normalize()           # vetor unitário na mesma direção
v.dot(w)                # produto escalar  →  32.0
v.cross(w)              # produto vetorial 3D  →  Vector(-3, 6, -3)
v.angle_with(w)         # ângulo entre os vetores (radianos)
v.project_onto(w)       # projeção de v sobre w

v + w                   # soma
v - w                   # subtração
v * 2.0                 # escala
v / 2.0                 # divisão por escalar

v.dimensions            # número de dimensões
v.to_list()             # converte para lista Python
v[0]                    # acesso por índice
```

---

### `Matrix`

Matriz n×m.

```python
m = Matrix([
    [1, 2],
    [3, 4],
])
```

```python
m.determinant()         # determinante  →  -2.0
m.inverse()             # matriz inversa
m.transpose()           # transposta
m.trace()               # traço (soma da diagonal)
m.is_square()           # True se n == m

m + other               # soma de matrizes
m - other               # subtração
m * other               # multiplicação matricial
m * 2.0                 # escala

m.rows                  # número de linhas
m.cols                  # número de colunas
m[0]                    # acesso à linha por índice
m.to_list()             # converte para lista de listas

Matrix.identity(3)      # matriz identidade 3×3
Matrix.zeros(3, 4)      # matriz de zeros 3×4
```

---

## Geometria

### `Circle`

```python
c = Circle(radius=5)

c.area()           # π r²  →  78.539...
c.circumference()  # 2πr   →  31.415...
c.diameter()       # 2r    →  10.0
c.scale(2)         # Circle(radius=10)
c.radius           # 5.0
```

### `Rectangle`

```python
r = Rectangle(10, 20)

r.area()           # 200.0
r.perimeter()      # 60.0
r.diagonal()       # √(w² + h²)
r.is_square()      # False
r.scale(1.5)       # Rectangle(15, 30)
r.width            # 10.0
r.height           # 20.0
```

### `Triangle`

Pode ser criado por **base + altura** ou pelos **três lados** (fórmula de Heron):

```python
# Por base e altura
Triangle(base=10, height=5).area()      # 25.0

# Pelos três lados
Triangle(a=3, b=4, c=5).area()         # 6.0
Triangle(a=3, b=4, c=5).perimeter()    # 12.0
Triangle(a=3, b=4, c=5).is_right()     # True
Triangle(a=3, b=4, c=5).hypotenuse()   # 5.0
```

### `Sphere`

```python
s = Sphere(radius=3)

s.volume()        # (4/3)πr³
s.surface_area()  # 4πr²
```

### `Cylinder`

```python
c = Cylinder(radius=3, height=10)

c.volume()        # πr²h
c.surface_area()  # 2πr(r + h)
```

---

## Conversão de Unidades

Todas as classes de unidade aceitam o valor como string com a unidade embutida (`"10km"`) ou como número com a unidade separada (`Distance(10, "km")`).

### `Distance`

```python
d = Distance("10km")

d.to("m")    # 10000.0
d.to("mi")   # 6.213...
d.to("ft")   # 32808.3...
d.to("cm")   # 1000000.0
```

Unidades suportadas: `m`, `km`, `cm`, `mm`, `mi`, `ft`, `in`, `yd`, `nm` (milha náutica), `ly` (ano-luz), `au` (unidade astronômica).

### `Weight`

```python
w = Weight("70kg")

w.to("lb")    # 154.323...
w.to("oz")    # 2469.17...
w.to("g")     # 70000.0
w.to("stone") # 11.023...
```

Unidades suportadas: `kg`, `g`, `mg`, `lb`, `oz`, `t` (tonelada), `st` (stone).

### `Temperature`

```python
Temperature("100C").to("F")    # 212.0
Temperature("32F").to("C")     # 0.0
Temperature("0K").to("C")      # -273.15
Temperature("373.15K").to("F") # 212.0
```

Escalas suportadas: `C` (Celsius), `F` (Fahrenheit), `K` (Kelvin), `R` (Rankine).

### `Duration`

Aceita formato composto com múltiplos componentes:

```python
Duration("2h 30m").to("s")          # 9000.0
Duration("1d 4h 30m 15s").to("h")   # 28.504...
Duration("90min").to("h")            # 1.5
Duration(3600, "s").to("h")          # 1.0
```

Unidades suportadas: `ms`, `s`, `m` / `min`, `h` / `hr`, `d`, `w` / `week`.

---

## Moeda

### `Money`

```python
Money(100, "USD").to("BRL")    # Money(500.0, "BRL")  (taxa do dia)
Money(1000, "JPY").to("EUR")
Money(50, "BRL").to("USD")
```

Por padrão, usa `urllib` para buscar taxas em tempo real de `open.er-api.com`. Se a rede não estiver disponível, recorre a uma tabela de taxas estáticas de fallback.

Operações aritméticas:

```python
a = Money(100, "USD")
b = Money(50, "USD")

a.add(b)          # Money(150.0, "USD")
a.subtract(b)     # Money(50.0, "USD")
a.multiply(1.1)   # Money(110.0, "USD")
a.divide(4)       # Money(25.0, "USD")

# Soma entre moedas diferentes — converte automaticamente
Money(100, "USD").add(Money(500, "BRL"))

a.amount()        # 100.0
a.currency()      # "USD"
a.format(2)       # "100.00 USD"
```

Configuração de cache:

```python
# Define por quanto tempo as taxas buscadas ficam em cache (padrão: 1 hora)
Money.cache(hours=12)

# Força atualização descartando o cache
Money.refresh_rates()
```

Integração com NestifyPy Net:

```python
from arkhe.net import request

# Injeta o cliente HTTP do ecossistema
Money.set_fetcher(request)
```

---

## Tratamento de Erros

### Operações seguras

Operações que normalmente lançariam exceções retornam `FailureResult`:

```python
result = Number(10).divide(0)    # FailureResult — sem exceção

if result.is_failure():
    print(result.get_error())    # DivisionByZeroError
```

Cadeias com `FailureResult` propagam o erro silenciosamente:

```python
# Nenhuma exceção é lançada; o FailureResult atravessa toda a cadeia
Number(10).divide(0).add(5).multiply(3)   # ainda FailureResult
```

### Erros disponíveis

```python
from arkhe.math import MathError, DivisionByZeroError, PrecisionError
```

| Exceção | Quando ocorre |
|---|---|
| `MathError` | base de todos os erros do módulo |
| `DivisionByZeroError` | divisão ou módulo por zero |
| `PrecisionError` | precisão inválida |

### Integração com `Try`

```python
from arkhe.trying import Try
from arkhe.math import Number

result = (
    Try.of(lambda: Number(user_input))
       .map(lambda n: n.divide(10))
       .filter(lambda n: not n.is_failure(), "Math operation failed")
       .map(lambda n: n.multiply(2))
       .recover(lambda _: Number(0))
       .get()
)
```

---

## Seleção automática de backend

O módulo escolhe o backend mais eficiente de forma transparente:

| Operação | Backend |
|---|---|
| Aritmética inteira | `int` nativo do Python |
| Aritmética decimal | `decimal.Decimal` |
| Aritmética racional | `fractions.Fraction` |
| Alta precisão | `mpmath` (se instalado) |
| Matemática simbólica | `sympy` (se instalado) |

O utilizador nunca precisa escolher manualmente.
