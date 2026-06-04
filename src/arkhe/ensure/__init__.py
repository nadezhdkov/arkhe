"""
arkhe.ensure
-----------------
Validações reutilizáveis, tipadas e encadeáveis.

Substitui blocos repetitivos de ``if ... raise ...`` por uma API
declarativa, consistente e sem dependências externas.

Uso rápido
----------
::

    from arkhe.ensure import Ensure

    # Estático — retorna o valor validado
    name  = Ensure.not_blank(name)
    age   = Ensure.positive(age)
    users = Ensure.not_empty(users)

    # Fluente — cadeia encadeável
    username = (
        Ensure.that(username)
            .not_none()
            .not_blank()
            .min_length(3)
            .max_length(20)
            .map(str.strip)
            .map(str.lower)
            .unwrap()
    )

    # Captura qualquer falha de validação
    try:
        Ensure.positive(value)
    except EnsureError:
        ...
"""

from arkhe.ensure.exceptions import EnsureError, EnsureValueError, EnsureTypeError
from arkhe.ensure.chain import EnsureChain
from arkhe.ensure.core import Ensure

__all__ = [
    "Ensure",
    "EnsureChain",
    "EnsureError",
    "EnsureValueError",
    "EnsureTypeError",
]
