"""
arkhe.komodo.ast_generators.utils
-------------------------------------
Utilities for AST generators.
"""

import ast
from typing import Dict, Any, Type, Tuple, List

def get_fields_from_ast(class_def: ast.ClassDef) -> Dict[str, ast.expr]:
    """
    Extracts annotated fields from the class AST.
    Returns a dict mapping field name to its annotation AST node.
    """
    fields = {}
    for node in class_def.body:
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                # Ignore private fields starting with _
                if not node.target.id.startswith("_"):
                    fields[node.target.id] = node.annotation
    return fields

def get_defaults_from_ast(class_def: ast.ClassDef) -> Dict[str, ast.expr]:
    """
    Extracts default values assigned to annotated fields.
    """
    defaults = {}
    for node in class_def.body:
        if isinstance(node, ast.AnnAssign) and node.value is not None:
            if isinstance(node.target, ast.Name):
                if not node.target.id.startswith("_"):
                    defaults[node.target.id] = node.value
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    defaults[target.id] = node.value
    return defaults

def has_method(class_def: ast.ClassDef, name: str) -> bool:
    for node in class_def.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return True
    return False

def add_method(class_def: ast.ClassDef, method_def: ast.FunctionDef):
    # Only add if it doesn't already exist to respect user overrides
    if not has_method(class_def, method_def.name):
        class_def.body.append(method_def)

def get_inherited_fields(cls: Type) -> Dict[str, Any]:
    """
    Returns annotated fields from ancestor classes (excluding `cls` itself and
    `object`), collected in MRO order (closest ancestor first).

    Only public fields (not starting with ``_``) are included.  The returned
    dict is ordered: fields from higher-up ancestors come first so that the
    generated ``__init__`` signature matches the natural top-down declaration
    order.
    """
    # Collect per-class annotations in reverse MRO (top → bottom, excluding
    # `cls` itself and `object`) then reverse so that the closest ancestor
    # wins on duplicates.
    ancestor_chain = [
        klass
        for klass in reversed(cls.__mro__)
        if klass is not cls and klass is not object
    ]

    inherited: Dict[str, Any] = {}
    for klass in ancestor_chain:
        for name, annotation in getattr(klass, "__annotations__", {}).items():
            if not name.startswith("_"):
                inherited[name] = annotation
    return inherited


def annotation_to_ast(annotation: Any) -> ast.expr:
    if isinstance(annotation, ast.expr):
        return annotation
    if isinstance(annotation, type):
        return ast.Name(id=annotation.__name__, ctx=ast.Load())
    if isinstance(annotation, str):
        return ast.Name(id=annotation, ctx=ast.Load())
    return ast.Constant(value=None)

def get_all_fields_from_ast(class_def: ast.ClassDef, cls: Type) -> Dict[str, ast.expr]:
    own_fields = get_fields_from_ast(class_def)
    inherited_runtime = get_inherited_fields(cls)
    inherited_fields = {
        name: annotation_to_ast(ann)
        for name, ann in inherited_runtime.items()
        if name not in own_fields
    }
    return {**inherited_fields, **own_fields}

def get_komodo_meta(cls: Type) -> set:
    return getattr(cls, "__komodo_meta__", set())

def mark_komodo_meta(cls: Type, feature: str):
    if not hasattr(cls, "__komodo_meta__"):
        setattr(cls, "__komodo_meta__", set())
    getattr(cls, "__komodo_meta__").add(feature)
