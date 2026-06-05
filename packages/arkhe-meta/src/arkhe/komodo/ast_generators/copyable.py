"""
arkhe.komodo.ast_generators.copyable
----------------------------------------
AST generator for @komodo.copyable.
"""

import ast
from typing import Type
from arkhe.komodo.ast_builders import make_arg, make_arguments, make_function, make_return, make_call
from arkhe.komodo.ast_generators.utils import get_all_fields_from_ast, mark_komodo_meta

def generate_copyable(class_def: ast.ClassDef, cls: Type):
    fields = get_all_fields_from_ast(class_def, cls)
    
    # copy(self)
    # import copy as copy_module; return copy_module.copy(self)
    copy_body = [
        ast.Import(names=[ast.alias(name="copy", asname="copy_module")]),
        make_return(make_call("copy_module.copy", args=[ast.Name(id="self", ctx=ast.Load())]))
    ]
    copy_func = make_function("copy", make_arguments([make_arg("self")]), copy_body, returns=ast.Constant(value=None))
    
    # copy_with(self, **overrides)
    # current = {f: getattr(self, f) for f in fields}
    # current.update(overrides)
    # return self.__class__(**current)
    
    keys = []
    values = []
    for name in fields:
        keys.append(ast.Constant(value=name))
        values.append(ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=name, ctx=ast.Load()))
        
    current_dict = ast.Assign(
        targets=[ast.Name(id="current", ctx=ast.Store())],
        value=ast.Dict(keys=keys, values=values)
    )
    
    update_call = ast.Expr(value=make_call("current.update", args=[ast.Name(id="overrides", ctx=ast.Load())]))
    
    return_stmt = make_return(ast.Call(
        func=ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr="__class__", ctx=ast.Load()),
        args=[],
        keywords=[ast.keyword(arg=None, value=ast.Name(id="current", ctx=ast.Load()))]
    ))
    
    copy_with_body = [current_dict, update_call, return_stmt]
    
    args = make_arguments([make_arg("self")])
    args.kwarg = make_arg("overrides")
    
    copy_with_func = make_function("copy_with", args, copy_with_body, returns=ast.Constant(value=None))
    
    class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name in ("copy", "copy_with"))]
    class_def.body.extend([copy_func, copy_with_func])
    
    mark_komodo_meta(cls, "copyable")
