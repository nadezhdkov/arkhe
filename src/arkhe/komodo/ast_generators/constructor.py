"""
arkhe.komodo.ast_generators.constructor
-------------------------------------------
AST generator for __init__.
"""

import ast
from typing import Type, Optional
from arkhe.komodo.ast_builders import make_arg, make_arguments, make_function, make_attribute_assign
from arkhe.komodo.ast_generators.utils import get_fields_from_ast, get_defaults_from_ast, mark_komodo_meta
from arkhe.komodo.access_level import AccessLevel

def generate_constructor(class_def: ast.ClassDef, cls: Type, mode="all", access: AccessLevel = AccessLevel.PUBLIC, static_name: Optional[str] = None):
    """
    mode: "all", "no_args", "required"
    """
    if access == AccessLevel.NONE:
        return

    fields = get_fields_from_ast(class_def)
    defaults = get_defaults_from_ast(class_def)
    
    args_list = [make_arg("self")]
    body = []
    
    required = []
    optional = []
    for name in fields:
        if name in defaults:
            optional.append(name)
        else:
            required.append(name)
            
    default_exprs = []

    if mode == "no_args":
        pass
    elif mode == "required":
        for name in required:
            args_list.append(make_arg(name, fields[name]))
            body.append(make_attribute_assign("self", name, ast.Name(id=name, ctx=ast.Load())))
    else: # all args
        for name in required:
            args_list.append(make_arg(name, fields[name]))
            body.append(make_attribute_assign("self", name, ast.Name(id=name, ctx=ast.Load())))
        
        for name in optional:
            args_list.append(make_arg(name, fields[name]))
            default_exprs.append(defaults[name])
            body.append(make_attribute_assign("self", name, ast.Name(id=name, ctx=ast.Load())))

    arguments = make_arguments(args_list, defaults=default_exprs)
    
    post_init_exists = any(isinstance(n, ast.FunctionDef) and n.name == '__post_init__' for n in class_def.body)
    if post_init_exists:
        body.append(ast.Expr(value=ast.Call(
            func=ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr="__post_init__", ctx=ast.Load()),
            args=[], keywords=[]
        )))

    if not body:
        body.append(ast.Pass())

    # In Python, constructors are always __init__
    init_func = make_function("__init__", arguments, body, returns=ast.Constant(value=None))
    
    class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name == '__init__')]
    class_def.body.append(init_func)

    if static_name:
        factory_args_list = [make_arg("cls")] + args_list[1:]
        factory_arguments = make_arguments(factory_args_list, defaults=default_exprs)
        
        call_args = [ast.Name(id=arg.arg, ctx=ast.Load()) for arg in factory_args_list[1:]]
        factory_body = [
            ast.Return(value=ast.Call(
                func=ast.Name(id="cls", ctx=ast.Load()),
                args=call_args,
                keywords=[]
            ))
        ]
        
        factory_func = make_function(static_name, factory_arguments, factory_body)
        factory_func.decorator_list.append(ast.Name(id="classmethod", ctx=ast.Load()))
        
        class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name == static_name)]
        class_def.body.append(factory_func)
    
    if mode == "no_args":
        mark_komodo_meta(cls, "no_args_constructor")
    elif mode == "required":
        mark_komodo_meta(cls, "required_args_constructor")
    else:
        mark_komodo_meta(cls, "all_args_constructor")
