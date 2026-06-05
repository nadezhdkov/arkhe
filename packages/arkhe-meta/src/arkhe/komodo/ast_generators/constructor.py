"""
arkhe.komodo.ast_generators.constructor
-------------------------------------------
AST generator for __init__.

Inheritance-aware: when the decorated class has ancestors with annotated
fields, the generated __init__ includes those fields in the signature and
emits ``super().__init__(...)`` to initialise them, so the full field
hierarchy is properly wired.
"""

import ast
import inspect as _inspect
from typing import Type, Optional, Dict, List, Any

from arkhe.komodo.ast_builders import (
    make_arg,
    make_arguments,
    make_function,
    make_attribute_assign,
)
from arkhe.komodo.ast_generators.utils import (
    get_fields_from_ast,
    get_defaults_from_ast,
    get_inherited_fields,
    mark_komodo_meta,
)
from arkhe.komodo.access_level import AccessLevel


# ---------------------------------------------------------------------------
# Helper: convert a runtime annotation to an AST expression node.
# ---------------------------------------------------------------------------

def _annotation_to_ast(annotation: Any) -> ast.expr:
    """
    Convert a runtime annotation value to an AST expression node.

    Handles:
    - ast.expr nodes (already AST — pass through)
    - Plain types (int, str, …) — use their ``__name__``
    - Strings — wrap in ast.Name
    - Anything else — fall back to ast.Constant(None)
    """
    if isinstance(annotation, ast.expr):
        return annotation
    if isinstance(annotation, type):
        return ast.Name(id=annotation.__name__, ctx=ast.Load())
    if isinstance(annotation, str):
        return ast.Name(id=annotation, ctx=ast.Load())
    return ast.Constant(value=None)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_constructor(
    class_def: ast.ClassDef,
    cls: Type,
    mode: str = "all",
    access: AccessLevel = AccessLevel.PUBLIC,
    static_name: Optional[str] = None,
):
    """
    Generate ``__init__`` for *cls*.

    Parameters
    ----------
    class_def:
        The AST node being mutated.
    cls:
        The live class object (used to introspect the MRO for inherited fields).
    mode:
        ``"all"``       — accept every field (own + inherited).
        ``"required"``  — accept only fields without defaults.
        ``"no_args"``   — no parameters at all.
    access:
        ``AccessLevel.NONE`` skips generation entirely.
    static_name:
        If given, a ``@classmethod`` factory with this name is also generated.
    """
    if access == AccessLevel.NONE:
        return

    # ── Own fields (declared in the class body being decorated) ────────────
    own_fields: Dict[str, ast.expr] = get_fields_from_ast(class_def)
    own_defaults: Dict[str, ast.expr] = get_defaults_from_ast(class_def)

    # ── Inherited fields (from ancestor classes, via MRO) ──────────────────
    # These come back as runtime annotations; convert them to AST nodes.
    inherited_runtime: Dict[str, Any] = get_inherited_fields(cls)
    inherited_fields: Dict[str, ast.expr] = {
        name: _annotation_to_ast(ann)
        for name, ann in inherited_runtime.items()
        # Don't shadow fields explicitly declared on this class
        if name not in own_fields
    }

    # Defaults for inherited fields: look them up on the ancestor classes.
    inherited_defaults: Dict[str, ast.expr] = {}
    for name in inherited_fields:
        for klass in cls.__mro__[1:]:
            if klass is object:
                continue
            val = klass.__dict__.get(name)
            if val is not None and not callable(val):
                # Represent the default as a Constant if it's a literal,
                # otherwise fall back to a Name reference.
                try:
                    inherited_defaults[name] = ast.Constant(value=val)
                except Exception:
                    pass
                break

    # ── Determine which fields to include based on mode ────────────────────
    # Inherited fields always come before own fields in the signature
    # (mirrors the declaration order top-down).

    def _split(fields: Dict[str, ast.expr], defaults: Dict[str, ast.expr]):
        required = [n for n in fields if n not in defaults]
        optional = [n for n in fields if n in defaults]
        return required, optional

    inh_required, inh_optional = _split(inherited_fields, inherited_defaults)
    own_required, own_optional = _split(own_fields, own_defaults)

    args_list: List[ast.arg] = [make_arg("self")]
    body: List[ast.stmt] = []
    default_exprs: List[ast.expr] = []

    # Names of inherited fields that are passed to super().__init__().
    super_args: List[str] = []

    if mode == "no_args":
        # No parameters; if there are inherited fields, call super().__init__()
        # with no args (the parent's no-args constructor takes care of itself).
        pass

    elif mode == "required":
        # Inherited required fields → forwarded to super().__init__()
        for name in inh_required:
            args_list.append(make_arg(name, inherited_fields[name]))
            super_args.append(name)
        # Own required fields → assigned locally
        for name in own_required:
            args_list.append(make_arg(name, own_fields[name]))
            body.append(make_attribute_assign(
                "self", name, ast.Name(id=name, ctx=ast.Load())
            ))

    else:  # "all"
        # Inherited required fields → forwarded to super().__init__()
        for name in inh_required:
            args_list.append(make_arg(name, inherited_fields[name]))
            super_args.append(name)
        # Inherited optional fields → forwarded to super().__init__()
        for name in inh_optional:
            args_list.append(make_arg(name, inherited_fields[name]))
            default_exprs.append(inherited_defaults[name])
            super_args.append(name)
        # Own required fields → assigned locally
        for name in own_required:
            args_list.append(make_arg(name, own_fields[name]))
            body.append(make_attribute_assign(
                "self", name, ast.Name(id=name, ctx=ast.Load())
            ))
        # Own optional fields → assigned locally
        for name in own_optional:
            args_list.append(make_arg(name, own_fields[name]))
            default_exprs.append(own_defaults[name])
            body.append(make_attribute_assign(
                "self", name, ast.Name(id=name, ctx=ast.Load())
            ))

    # ── Emit super().__init__(...) when there are inherited fields ──────────
    # We insert it *before* any own-field assignments so that the parent is
    # initialised first (mirrors normal Python inheritance etiquette).
    if super_args or inherited_fields:
        super_call = ast.Expr(value=ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Name(id="super", ctx=ast.Load()),
                    args=[],
                    keywords=[],
                ),
                attr="__init__",
                ctx=ast.Load(),
            ),
            args=[ast.Name(id=n, ctx=ast.Load()) for n in super_args],
            keywords=[],
        ))
        body.insert(0, super_call)

    # ── Call __post_init__ if the class defines it ──────────────────────────
    post_init_exists = any(
        isinstance(n, ast.FunctionDef) and n.name == "__post_init__"
        for n in class_def.body
    )
    if post_init_exists:
        body.append(ast.Expr(value=ast.Call(
            func=ast.Attribute(
                value=ast.Name(id="self", ctx=ast.Load()),
                attr="__post_init__",
                ctx=ast.Load(),
            ),
            args=[],
            keywords=[],
        )))

    if not body:
        body.append(ast.Pass())

    arguments = make_arguments(args_list, defaults=default_exprs)
    init_func = make_function(
        "__init__", arguments, body, returns=ast.Constant(value=None)
    )

    # Replace any existing __init__ in the class body
    class_def.body = [
        n for n in class_def.body
        if not (isinstance(n, ast.FunctionDef) and n.name == "__init__")
    ]
    class_def.body.append(init_func)

    # ── Optional static factory method ─────────────────────────────────────
    if static_name:
        factory_args_list = [make_arg("cls")] + args_list[1:]
        factory_arguments = make_arguments(factory_args_list, defaults=default_exprs)

        call_args = [
            ast.Name(id=arg.arg, ctx=ast.Load())
            for arg in factory_args_list[1:]
        ]
        factory_body = [
            ast.Return(value=ast.Call(
                func=ast.Name(id="cls", ctx=ast.Load()),
                args=call_args,
                keywords=[],
            ))
        ]

        factory_func = make_function(static_name, factory_arguments, factory_body)
        factory_func.decorator_list.append(
            ast.Name(id="classmethod", ctx=ast.Load())
        )

        class_def.body = [
            n for n in class_def.body
            if not (isinstance(n, ast.FunctionDef) and n.name == static_name)
        ]
        class_def.body.append(factory_func)

    # ── Mark komodo metadata ────────────────────────────────────────────────
    if mode == "no_args":
        mark_komodo_meta(cls, "no_args_constructor")
    elif mode == "required":
        mark_komodo_meta(cls, "required_args_constructor")
    else:
        mark_komodo_meta(cls, "all_args_constructor")
