"""
arkhe.komodo.ast_generators.validation
------------------------------------------
AST generators for validation.
"""

import ast
from typing import Type
from arkhe.komodo.ast_builders import make_if, make_raise, make_call
from arkhe.komodo.ast_generators.utils import get_all_fields_from_ast, mark_komodo_meta

def generate_non_null(class_def: ast.ClassDef, cls: Type):
    fields = get_all_fields_from_ast(class_def, cls)
    
    init_func = next((n for n in class_def.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"), None)
    if not init_func:
        return
        
    checks = []
    for name in fields.keys():
        is_none_check = ast.Compare(
            left=ast.Name(id=name, ctx=ast.Load()),
            ops=[ast.Is()],
            comparators=[ast.Constant(value=None)]
        )
        raise_err = make_raise("ValueError", f"{class_def.name}: field '{name}' must not be None")
        checks.append(make_if(test=is_none_check, body=[raise_err]))
        
    init_func.body = checks + init_func.body
    mark_komodo_meta(cls, "non_null")

def generate_validated(class_def: ast.ClassDef, cls: Type):
    fields = get_all_fields_from_ast(class_def, cls)
    
    init_func = next((n for n in class_def.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"), None)
    if not init_func:
        return
        
    checks = []
    for name, annotation in fields.items():
        # Very basic isinstance check for AST.
        # Handles simple types (str, int, float, bool)
        # Skip if annotation is complex (Subscript, etc.)
        if isinstance(annotation, ast.Name):
            type_name = annotation.id
            
            # if name is not None and not isinstance(name, type): raise TypeError(...)
            is_not_none = ast.Compare(
                left=ast.Name(id=name, ctx=ast.Load()),
                ops=[ast.IsNot()],
                comparators=[ast.Constant(value=None)]
            )
            
            not_isinstance = ast.UnaryOp(
                op=ast.Not(),
                operand=make_call("isinstance", args=[ast.Name(id=name, ctx=ast.Load()), ast.Name(id=type_name, ctx=ast.Load())])
            )
            
            condition = ast.BoolOp(op=ast.And(), values=[is_not_none, not_isinstance])
            
            raise_err = make_raise("TypeError", f"{class_def.name}: field '{name}' expected {type_name}")
            checks.append(make_if(test=condition, body=[raise_err]))
            
    init_func.body = checks + init_func.body
    mark_komodo_meta(cls, "validated")
