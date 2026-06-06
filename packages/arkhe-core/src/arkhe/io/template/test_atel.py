"""
test_atel.py — ATEL feature test suite.
Run from the parent directory: python test_atel.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from arkhe.io import install, printf
from arkhe.io.template.engine import render
from arkhe.io.template.transformers import apply_transformer as tf, apply_chain as tc

install()

# ── Helper ─────────────────────────────────────────
def section(title):
    from arkhe.io.core import _original_print
    _original_print(f"\n\033[1;36m{'─'*4} {title} {'─'*4}\033[0m")

def ok(label, result, expected=None):
    from arkhe.io.core import _original_print
    if expected is not None:
        passed = str(result) == str(expected)
        status = "✓" if passed else "✗"
        hint   = f"  (expected: {expected!r})" if not passed else ""
        _original_print(f"  {status}  {label}: {result!r}{hint}")
    else:
        _original_print(f"  •  {label}: {result!r}")

# ── Context object ──────────────────────────────────
class Player:
    name      = "Samuel"
    coins     = 15000
    phone     = "88999999999"
    rank      = "ADMIN"
    online    = True
    vip       = True
    banned    = False
    nickname  = None
    username  = "samueldev"
    level     = 72
    ping      = 45
    tax       = 0.75
    price     = 10.5
    cpf       = "12345678901"
    tags      = ["arkhe", "python", "terminal"]

    class address:
        city    = "Quixadá"
        country = "Brazil"

    def display_name(self):
        return f"[{self.rank}] {self.name}"

player = Player()

# ────────────────────────────────────────────────────
section("1. Basic interpolation")
# ────────────────────────────────────────────────────
ok("positional {}",     render("Hello {}!", "World"),           "Hello World!")
ok("indexed {1}{0}",    render("{1} {0}", "World", "Hello"),    "Hello World")
ok("attribute",         render("{name}", player),               "Samuel")

# ────────────────────────────────────────────────────
section("2. Nested attribute & method")
# ────────────────────────────────────────────────────
ok("nested address.city",  render("{address.city}", player),    "Quixadá")
ok("method call",          render("{display_name()}", player),  "[ADMIN] Samuel")

# ────────────────────────────────────────────────────
section("3. Fallback ??")
# ────────────────────────────────────────────────────
ok("None → fallback",       render("{nickname ?? Anonymous}", player),              "Anonymous")
ok("chain fallback",        render("{nickname ?? username ?? guest}", player),      "samueldev")

# ────────────────────────────────────────────────────
section("4. String transformers")
# ────────────────────────────────────────────────────
ok("upper",         render("{name:upper}",       player), "SAMUEL")
ok("lower",         render("{name:lower}",       player), "samuel")
ok("capitalize",    render("{name:capitalize}",  player), "Samuel")
ok("title",         render("{name:title}",       player), "Samuel")
ok("reverse",       render("{name:reverse}",     player), "leumaS")
ok("trim (direct)", tf("  hi  ", "trim"),                 "hi")
ok("length",        render("{name:length}",      player), "6")
ok("repeat(3)",     render("{name:repeat(3)}",   player), "SamuelSamuelSamuel")
ok("substring(0,3)",render("{name:substring(0,3)}", player), "Sam")
ok("pad_left(10)",  render("{name:pad_left(10)}",   player), "    Samuel")
ok("pad_right(10)", render("{name:pad_right(10)}",  player), "Samuel    ")
ok("center(12)",    render("{name:center(12)}",     player), "   Samuel   ")

# ────────────────────────────────────────────────────
section("5. Case converters")
# ────────────────────────────────────────────────────
ok("camel_case",    tf("hello world",  "camel_case"),    "helloWorld")
ok("pascal_case",   tf("hello world",  "pascal_case"),   "HelloWorld")
ok("snake_case",    tf("Hello World",  "snake_case"),    "hello_world")
ok("kebab_case",    tf("Hello World",  "kebab_case"),    "hello-world")
ok("constant_case", tf("Hello World",  "constant_case"), "HELLO_WORLD")

# ────────────────────────────────────────────────────
section("6. Normalization & filters")
# ────────────────────────────────────────────────────
ok("normalize",  tf("João",               "normalize"),  "Joao")
ok("digits",     tf("+55 (88) 9999-9999", "digits"),    "558899999999")
ok("letters",    tf("abc123def",          "letters"),   "abcdef")

# ────────────────────────────────────────────────────
section("7. Numeric transformers")
# ────────────────────────────────────────────────────
ok("number",     render("{coins:number}",    player), "15,000")
ok("decimal(2)", render("{price:decimal(2)}",player), "10.50")
ok("percent",    render("{tax:percent}",     player), "75%")
ok("currency",   render("{price:currency}",  player), "$10.50")

# ────────────────────────────────────────────────────
section("8. Mask")
# ────────────────────────────────────────────────────
ok("cpf mask",   render("{cpf:mask(###.###.###-##)}",    player), "123.456.789-01")
ok("phone mask", render("{phone:mask((##) #####-####)}", player), "(88) 99999-9999")

# ────────────────────────────────────────────────────
section("9. Collection transformers")
# ────────────────────────────────────────────────────
ok("size",   render("{tags:size}",          player), "3")
ok("empty",  render("{tags:empty}",         player), "false")
ok("first",  render("{tags:first}",         player), "arkhe")
ok("last",   render("{tags:last}",          player), "terminal")
ok("join",   render("{tags:join(', ')}",    player), "arkhe, python, terminal")

# ────────────────────────────────────────────────────
section("10. Transformer chaining")
# ────────────────────────────────────────────────────
ok("trim|capitalize", tc("  samuel  ", "trim|capitalize"), "Samuel")
ok("upper|reverse",   tc("samuel",     "upper|reverse"),   "LEUMAS")

# ────────────────────────────────────────────────────
section("11. Conditionals")
# ────────────────────────────────────────────────────
ok("boolean",         render("{online?Online:Offline}",        player), "Online")
ok("comparison >",    render("{coins > 1000?Rich:Poor}",       player), "Rich")
ok("equality ==",     render("{rank == 'ADMIN'?Admin:Player}", player), "Admin")
ok("not equal !=",    render("{rank != 'MOD'?Not mod:Mod}",   player), "Not mod")
ok("level >= 50",     render("{level >= 50?Veteran:Beginner}", player), "Veteran")
ok("ping < 100",      render("{ping < 100?Stable:Unstable}",   player), "Stable")
ok("NOT !banned",     render("{!banned?Allowed:Blocked}",      player), "Allowed")

# ────────────────────────────────────────────────────
section("12. Compound conditions")
# ────────────────────────────────────────────────────
ok("AND &&",        render("{online && vip?VIP Online:Offline}",         player), "VIP Online")
ok("OR ||",         render("{banned || vip?Special:Normal}",             player), "Special")
ok("nested parens", render("{online && (vip || coins > 10000)?Premium:Normal}", player), "Premium")

# ────────────────────────────────────────────────────
section("13. Match")
# ────────────────────────────────────────────────────
ok("exact match",    render("{rank -> ADMIN:'👑 Admin', MOD:'🛡 Mod'}",              player), "👑 Admin")
ok("wildcard *",     render("{rank -> MOD:'🛡 Mod', *:'👤 User'}",                   player), "👤 User")
ok("with wildcard",  render("{rank -> ADMIN:'👑 Admin', MOD:'🛡 Mod', *:'👤 User'}", player), "👑 Admin")

# ────────────────────────────────────────────────────
section("14. System tokens")
# ────────────────────────────────────────────────────
from arkhe.io.template.tokens import resolve_system_token
ok("os",      type(resolve_system_token("os")).__name__,      "str")
ok("python",  resolve_system_token("python").count(".") >= 1, True)
ok("hostname",len(resolve_system_token("hostname")) > 0,      True)
ok("uuid",    len(resolve_system_token("uuid")),              36)

# ────────────────────────────────────────────────────
section("15. printf() — full showcase")
# ────────────────────────────────────────────────────
printf("""
{online?🟢 Online:🔴 Offline}

User     : {name:title}
Rank     : {rank -> ADMIN:'👑 Admin', MOD:'🛡 Moderator', *:'👤 User'}
Level    : {level}
Coins    : {coins:number}
Phone    : {phone:mask((##) #####-####)}
Tags     : {tags:join(', ')}
Status   : {!banned?Allowed:Blocked}
Tier     : {online && (vip || coins > 10000)?Premium Customer:Standard Customer}
City     : {address.city}
Nickname : {nickname ?? username ?? guest}
""", player)

from arkhe.io.core import _original_print
_original_print("\n✓ ATEL test suite complete")
