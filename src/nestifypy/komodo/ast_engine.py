"""
nestifypy.komodo.ast_engine
---------------------------
Core engine for compiling AST-based macro modifications.
"""

import ast
import inspect
import sys
import textwrap
from typing import Any, Callable, Type


def apply_generator(cls: Type, generator: Callable[[ast.ClassDef, Type], None]) -> Type:
    """
    Retrieves or initializes the AST of the class, applies the given generator
    to mutate the AST, recompiles the AST, and returns the newly minted class.

    This mechanism allows stacking multiple komodo decorators without losing
    previous transformations or reading stale source code.
    """
    if hasattr(cls, "__komodo_ast__"):
        tree = getattr(cls, "__komodo_ast__")
        class_def = next(
            (node for node in tree.body if isinstance(node, ast.ClassDef)), None
        )
    else:
        try:
            source = inspect.getsource(cls)
            source = textwrap.dedent(source)
            tree = ast.parse(source)
        except (TypeError, OSError, SyntaxError):
            return cls

        class_def = next(
            (node for node in tree.body if isinstance(node, ast.ClassDef)), None
        )
        if not class_def:
            return cls

        # Strip komodo decorators to prevent recursion when we exec the AST
        new_decors = []
        for dec in class_def.decorator_list:
            is_komodo = False
            # Match @komodo.decorator
            if (
                isinstance(dec, ast.Attribute)
                and isinstance(dec.value, ast.Name)
                and dec.value.id == "komodo"
            ):
                is_komodo = True
            # Match @komodo.decorator(...)
            elif (
                isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Attribute)
                and isinstance(dec.func.value, ast.Name)
                and dec.func.value.id == "komodo"
            ):
                is_komodo = True

            if not is_komodo:
                new_decors.append(dec)
        class_def.decorator_list = new_decors

    # Apply the specific generator
    generator(class_def, cls)

    # Inject any needed module-level imports into the AST tree
    from nestifypy.komodo.ast_generators.logger import inject_logger_imports
    inject_logger_imports(tree)

    ast.fix_missing_locations(tree)
    code = compile(tree, filename="<komodo_ast>", mode="exec")

    # Build the execution namespace from the class's original module so that
    # names used in annotations and type hints resolve correctly.
    module = sys.modules.get(cls.__module__)
    if module:
        namespace = module.__dict__.copy()
    else:
        namespace = {}

    # FIX 1: Guarantee common typing names are always available inside the
    # generated code, regardless of what the user module imports.
    import typing as _typing
    for _name in ("Any", "Optional", "Union", "List", "Dict", "Tuple", "Set",
                  "Type", "Callable", "ClassVar"):
        namespace.setdefault(_name, getattr(_typing, _name))

    # FIX 2: Make the class itself available in the namespace so that
    # forward references inside nested classes (e.g. Builder.build returning
    # the outer class) resolve correctly.
    namespace[cls.__name__] = cls

    # Executing the compiled AST creates the class in the namespace
    exec(code, namespace)
    new_cls = namespace[cls.__name__]

    # FIX 3: Write the newly created class back into the *real* module dict so
    # that subsequent stacked decorators see the updated version when they call
    # inspect.getsource() or reference the class by name.
    if module:
        module.__dict__[cls.__name__] = new_cls

    # Carry over the AST for the next decorator
    setattr(new_cls, "__komodo_ast__", tree)

    # Carry over metadata
    if hasattr(cls, "__komodo_meta__"):
        setattr(new_cls, "__komodo_meta__", getattr(cls, "__komodo_meta__"))

    return new_cls
