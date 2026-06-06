"""
test_text.py — arkhe.text test suite.
Run from the parent directory: python test_text.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from arkhe.text import (
    String, StringBuilder, StringMatcher,
    StringNormalizer, StringValidator,
)

_passed = 0
_failed = 0

def check(label: str, result, expected):
    global _passed, _failed
    if result == expected:
        print(f"  ✓  {label}")
        _passed += 1
    else:
        print(f"  ✗  {label}")
        print(f"       got:      {result!r}")
        print(f"       expected: {expected!r}")
        _failed += 1

def section(title: str):
    print(f"\n\033[1;36m──── {title} ────\033[0m")

# ═══════════════════════════════════════════════════════
# String
# ═══════════════════════════════════════════════════════

section("String — basic operations")
check("trim",           String("   hello   ").trim().get(),        "hello")
check("trim_start",     String("  hi").trim_start().get(),         "hi")
check("trim_end",       String("hi  ").trim_end().get(),           "hi")
check("upper",          String("hello").upper().get(),             "HELLO")
check("lower",          String("HELLO").lower().get(),             "hello")
check("capitalize",     String("hello world").capitalize().get(),  "Hello world")
check("title",          String("hello world").title().get(),       "Hello World")
check("reverse",        String("hello").reverse().get(),           "olleh")
check("repeat",         String("=").repeat(5).get(),               "=====")
check("pad_left",       String("hi").pad_left(5).get(),            "   hi")
check("pad_right",      String("hi").pad_right(5).get(),           "hi   ")
check("center",         String("hi").center(6).get(),              "  hi  ")

section("String — inspection")
check("is_blank true",      String("   ").is_blank(),              True)
check("is_blank false",     String("hi").is_blank(),               False)
check("is_empty true",      String("").is_empty(),                 True)
check("is_empty false",     String("x").is_empty(),                False)
check("length",             String("hello").length(),              5)
check("contains true",      String("Hello World").contains("World"), True)
check("contains false",     String("Hello World").contains("xyz"),   False)
check("starts_with",        String("Hello World").starts_with("Hello"), True)
check("ends_with",          String("Hello World").ends_with("World"),  True)
check("equals_ignore_case", String("Samuel").equals_ignore_case("SAMUEL"), True)
check("index_of",           String("hello world").index_of("world"),   6)
check("count_occurrences",  String("abcabc").count_occurrences("abc"),  2)

section("String — substring operations")
check("substring",           String("Hello World").substring(0, 5).get(),             "Hello")
check("substring_before",    String("user@email.com").substring_before("@").get(),    "user")
check("substring_after",     String("user@email.com").substring_after("@").get(),     "email.com")
check("substring_before_last", String("a.b.c").substring_before_last(".").get(),      "a.b")
check("substring_after_last",  String("a.b.c").substring_after_last(".").get(),       "c")
check("substring_between",   String("[value]").substring_between("[", "]").get(),     "value")

section("String — replacement operations")
check("replace",         String("Hello World").replace("World", "Arkhe").get(), "Hello Arkhe")
check("remove",          String("Hello World").remove("World").get(),           "Hello ")
check("remove_prefix",   String("Mr. Samuel").remove_prefix("Mr. ").get(),      "Samuel")
check("remove_suffix",   String("report.pdf").remove_suffix(".pdf").get(),      "report")
check("remove_whitespace", String("a b c").remove_whitespace().get(),           "abc")
check("collapse_spaces", String("hello   world").collapse_spaces().get(),       "hello world")
check("replace_regex",   String("a1b2c3").replace_regex(r"\d", "X").get(),      "aXbXcX")

section("String — naming conventions")
check("to_camel_case",    String("hello_world").to_camel_case().get(),    "helloWorld")
check("to_pascal_case",   String("hello_world").to_pascal_case().get(),   "HelloWorld")
check("to_snake_case",    String("HelloWorld").to_snake_case().get(),      "hello_world")
check("to_kebab_case",    String("HelloWorld").to_kebab_case().get(),      "hello-world")
check("to_constant_case", String("HelloWorld").to_constant_case().get(),   "HELLO_WORLD")
check("camel from spaces", String("hello world foo").to_camel_case().get(), "helloWorldFoo")

section("String — normalization")
check("normalize",    String("João").normalize().get(),          "Joao")
check("normalize 2",  String("Ñoño café").normalize().get(),    "Nono cafe")

section("String — multiline")
check("lines",   String("\nA\nB\nC\n").lines(),       ["A", "B", "C"])
check("indent",  String("Hello").indent(4).get(),     "    Hello")
check("dedent",  String("    Hi\n    World").dedent().get(), "Hi\nWorld")

section("String — other")
check("mask cpf",    String("12345678901").mask("###.###.###-##").get(),    "123.456.789-01")
check("truncate",    String("Hello World").truncate(7).get(),               "Hell...")
check("truncate ok", String("Hi").truncate(10).get(),                       "Hi")
check("chaining",    String("  hello_world  ").trim().to_pascal_case().get(), "HelloWorld")
check("__str__",     str(String("test")),                                   "test")
check("__eq__ str",  String("hello") == "hello",                            True)
check("__add__",     (String("Hello") + " World").get(),                    "Hello World")

section("String — ATEL template integration")

class Player:
    name  = "Samuel"
    coins = 15000

p = Player()
check("template()", String("{name:title} has {coins:number} coins.").template(p).get(),
      "Samuel has 15,000 coins.")

# ═══════════════════════════════════════════════════════
# StringBuilder
# ═══════════════════════════════════════════════════════

section("StringBuilder — core appends")
check("append",          StringBuilder().append("Hello").append(", World").build(),  "Hello, World")
check("append_line",     StringBuilder().append_line("A").append_line("B").build(),  "A\nB\n")
check("append_repeat",   StringBuilder().append_repeat("=", 5).build(),              "=====")
check("append_join",     StringBuilder().append_join(", ", ["A","B","C"]).build(),   "A, B, C")
check("append_if true",  StringBuilder().append_if(True, "yes", "no").build(),       "yes")
check("append_if false", StringBuilder().append_if(False, "yes", "no").build(),      "no")
check("append_each",     StringBuilder().append_each(["a","b","c"], " | ").build(),  "a | b | c")
check("append_lines",    StringBuilder().append_lines("X", "Y").build(),             "X\nY\n")
check("prepend",         StringBuilder().append("World").prepend("Hello ").build(),  "Hello World")
check("__iadd__",        (StringBuilder().__iadd__("A").__iadd__("B")).build(),      "AB")

section("StringBuilder — state")
b = StringBuilder()
check("is_empty true",      b.is_empty(),   True)
b.append("hello")
check("is_empty false",     b.is_empty(),   False)
check("length",             b.length(),     5)
check("fragment_count",     b.fragment_count(), 1)
b.clear()
check("clear",              b.build(),      "")

section("StringBuilder — ATEL template integration")
class Srv:
    name = "Samuel"
check("append_template", StringBuilder().append("[INFO] ").append_template("{name} joined.", Srv()).build(),
      "[INFO] Samuel joined.")

section("StringBuilder — to_string")
result = StringBuilder().append("hello").to_string()
check("to_string type", type(result).__name__, "String")
check("to_string value", result.get(), "hello")

# ═══════════════════════════════════════════════════════
# StringMatcher
# ═══════════════════════════════════════════════════════

section("StringMatcher — matching")
check("matches true",      StringMatcher.matches("hello123", r"[a-z]+\d+"),       True)
check("matches false",     StringMatcher.matches("hello123", r"[A-Z]+"),           False)
check("contains_match",    StringMatcher.contains_match("ID: 1234", r"\d+"),       True)
check("starts_with_pattern", StringMatcher.starts_with_pattern("hello", r"hel"),  True)

section("StringMatcher — extraction")
check("extract",           StringMatcher.extract("a1 b2 c3", r"\d"),              ["1","2","3"])
check("extract_first",     StringMatcher.extract_first("ID: 1234", r"\d+"),       "1234")
check("extract_last",      StringMatcher.extract_last("1 and 2 and 3", r"\d"),    "3")
check("extract_groups",    StringMatcher.extract_groups("2024-06-05", r"(\d{4})-(\d{2})-(\d{2})"), ("2024","06","05"))
check("extract_named",     StringMatcher.extract_named_groups("Sam, 30", r"(?P<name>\w+), (?P<age>\d+)"),
      {"name": "Sam", "age": "30"})
check("count_matches",     StringMatcher.count_matches("aabbcc", r"[a-z]"),       6)
check("find_span",         StringMatcher.find_span("hello world", r"world"),      (6, 11))

section("StringMatcher — replace / split")
check("replace",       StringMatcher.replace("a1b2c3", r"\d", "X"),              "aXbXcX")
check("replace_first", StringMatcher.replace_first("a1b2", r"\d", "X"),          "aXb2")
check("split",         StringMatcher.split("a,b,,c", r",+"),                     ["a","b","c"])

# ═══════════════════════════════════════════════════════
# StringNormalizer
# ═══════════════════════════════════════════════════════

section("StringNormalizer")
check("normalize",          StringNormalizer.normalize("João"),              "Joao")
check("to_ascii",           StringNormalizer.to_ascii("Héllo"),             "Hello")
check("remove_whitespace",  StringNormalizer.remove_whitespace("a b c"),    "abc")
check("collapse_spaces",    StringNormalizer.collapse_spaces("a  b   c"),   "a b c")
check("strip_lines",        StringNormalizer.strip_lines("  hi  \n  lo  "), "hi\nlo")
check("remove_blank_lines", StringNormalizer.remove_blank_lines("a\n\nb"),  "a\nb")
check("digits_only",        StringNormalizer.digits_only("+55 (88) 9999"),  "55889999")
check("letters_only",       StringNormalizer.letters_only("abc123"),        "abc")
check("alphanumeric_only",  StringNormalizer.alphanumeric_only("a@1#b"),    "a1b")
check("remove_punctuation", StringNormalizer.remove_punctuation("hi!"),     "hi")
check("slugify",            StringNormalizer.slugify("Hello World! Olá"),    "hello-world-ola")
check("truncate_words",     StringNormalizer.truncate_words("a b c d", 2),  "a b...")
check("strip_html",         StringNormalizer.strip_html("<b>Hi</b>"),        "Hi")
check("escape_html",        StringNormalizer.escape_html("<b>"),             "&lt;b&gt;")

# ═══════════════════════════════════════════════════════
# StringValidator
# ═══════════════════════════════════════════════════════

section("StringValidator — email / url / uuid")
check("is_email true",   StringValidator.is_email("user@example.com"),    True)
check("is_email false",  StringValidator.is_email("not-an-email"),         False)
check("is_url true",     StringValidator.is_url("https://arkhe.dev"),      True)
check("is_url false",    StringValidator.is_url("ftp://example.com"),      False)
check("is_uuid true",    StringValidator.is_uuid("550e8400-e29b-41d4-a716-446655440000"), True)
check("is_uuid false",   StringValidator.is_uuid("not-a-uuid"),            False)
check("is_ip_v4 true",   StringValidator.is_ip_v4("192.168.0.1"),          True)
check("is_ip_v4 false",  StringValidator.is_ip_v4("999.0.0.1"),            False)

section("StringValidator — numeric")
check("is_numeric int",   StringValidator.is_numeric("123"),    True)
check("is_numeric float", StringValidator.is_numeric("-45.67"), True)
check("is_numeric false", StringValidator.is_numeric("abc"),    False)
check("is_integer true",  StringValidator.is_integer("42"),     True)
check("is_integer false", StringValidator.is_integer("4.2"),    False)
check("is_positive",      StringValidator.is_positive("5"),     True)
check("is_in_range",      StringValidator.is_in_range("50", 0, 100), True)

section("StringValidator — length & composition")
check("has_min_length",   StringValidator.has_min_length("hello", 3),  True)
check("has_max_length",   StringValidator.has_max_length("hi", 5),     True)
check("has_length range", StringValidator.has_length("abc", 2, 5),     True)
check("is_alpha",         StringValidator.is_alpha("abc"),              True)
check("is_alphanumeric",  StringValidator.is_alphanumeric("abc123"),    True)
check("is_digits_only",   StringValidator.is_digits_only("12345"),      True)
check("has_uppercase",    StringValidator.has_uppercase("Hello"),        True)
check("has_lowercase",    StringValidator.has_lowercase("Hello"),        True)
check("has_digit",        StringValidator.has_digit("abc1"),             True)
check("has_special_char", StringValidator.has_special_char("abc!"),      True)

section("StringValidator — password")
check("strong password",  StringValidator.is_strong_password("Arkhe@2024"), True)
check("weak password",    StringValidator.is_strong_password("weak"),       False)

section("StringValidator — Brazilian documents")
check("is_cpf valid",   StringValidator.is_cpf("529.982.247-25"),  True)
check("is_cpf invalid", StringValidator.is_cpf("111.111.111-11"),  False)
check("is_cnpj valid",  StringValidator.is_cnpj("11.222.333/0001-81"), True)
check("is_cnpj invalid",StringValidator.is_cnpj("00.000.000/0000-00"), False)

section("StringValidator — general")
check("is_blank true",  StringValidator.is_blank("   "),           True)
check("is_blank false", StringValidator.is_blank("hi"),             False)
check("is_json true",   StringValidator.is_json('{"a":1}'),        True)
check("is_json false",  StringValidator.is_json("not json"),        False)
check("is_slug true",   StringValidator.is_slug("hello-world"),    True)
check("is_slug false",  StringValidator.is_slug("Hello World!"),   False)

# ═══════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════
total = _passed + _failed
color = "\033[92m" if _failed == 0 else "\033[91m"
print(f"\n{color}{'─'*40}")
print(f"  {_passed}/{total} tests passed  {'✓' if _failed == 0 else f'✗ ({_failed} failed)'}")
print(f"{'─'*40}\033[0m\n")
