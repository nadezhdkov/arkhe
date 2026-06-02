"""
nestifypy.komodo.ast_builders
-----------------------------
Utilities for generating Python AST nodes.
"""

import ast
from typing import List, Union

def make_arg(name: str, annotation: Union[str, ast.expr, None] = None) -> ast.arg:
    if isinstance(annotation, str):
        ann = ast.Name(id=annotation, ctx=ast.Load())
    else:
        ann = annotation
    return ast.arg(arg=name, annotation=ann)

def make_arguments(args: List[ast.arg], defaults: List[ast.expr] = None) -> ast.arguments:
    return ast.arguments(
        posonlyargs=[],
        args=args,
        kwonlyargs=[],
        kw_defaults=[],
        defaults=defaults or [],
        vararg=None,
        kwarg=None
    )

def make_function(name: str, args: ast.arguments, body: List[ast.stmt], returns: Union[str, ast.expr, None] = None) -> ast.FunctionDef:
    if isinstance(returns, str):
        ret = ast.Name(id=returns, ctx=ast.Load())
    else:
        ret = returns
    return ast.FunctionDef(
        name=name,
        args=args,
        body=body or [ast.Pass()],
        decorator_list=[],
        returns=ret,
        lineno=1,
        col_offset=0
    )

def make_assign(target: str, value: ast.expr) -> ast.Assign:
    return ast.Assign(
        targets=[ast.Name(id=target, ctx=ast.Store())],
        value=value,
        lineno=1,
        col_offset=0
    )

def make_attribute_assign(target_obj: str, target_attr: str, value: ast.expr) -> ast.Assign:
    return ast.Assign(
        targets=[ast.Attribute(
            value=ast.Name(id=target_obj, ctx=ast.Load()),
            attr=target_attr,
            ctx=ast.Store()
        )],
        value=value,
        lineno=1,
        col_offset=0
    )

def make_return(value: ast.expr) -> ast.Return:
    return ast.Return(value=value, lineno=1, col_offset=0)

def make_call(func_name: str, args: List[ast.expr] = None, kwargs: List[ast.keyword] = None) -> ast.Call:
    if "." in func_name:
        parts = func_name.split(".")
        func = ast.Name(id=parts[0], ctx=ast.Load())
        for part in parts[1:]:
            func = ast.Attribute(value=func, attr=part, ctx=ast.Load())
    else:
        func = ast.Name(id=func_name, ctx=ast.Load())
        
    return ast.Call(
        func=func,
        args=args or [],
        keywords=kwargs or [],
        lineno=1,
        col_offset=0
    )

def make_raise(exc_name: str, msg: str) -> ast.Raise:
    return ast.Raise(
        exc=ast.Call(
            func=ast.Name(id=exc_name, ctx=ast.Load()),
            args=[ast.Constant(value=msg)],
            keywords=[]
        ),
        cause=None,
        lineno=1,
        col_offset=0
    )

def make_if(test: ast.expr, body: List[ast.stmt], orelse: List[ast.stmt] = None) -> ast.If:
    return ast.If(
        test=test,
        body=body,
        orelse=orelse or [],
        lineno=1,
        col_offset=0
    )
