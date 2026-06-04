"""
nestifypy.komodo.ast_generators.immutable
-----------------------------------------
AST generator for @komodo.immutable.
"""

import ast
from typing import Type
from nestifypy.komodo.ast_builders import make_arg, make_arguments, make_function, make_return, make_if, make_raise
from nestifypy.komodo.ast_generators.utils import mark_komodo_meta

def generate_immutable(class_def: ast.ClassDef, cls: Type):
    
    # We generate a __setattr__ that checks if self._frozen == True
    # if getattr(self, "_frozen", False):
    #     raise AttributeError(f"Class is immutable — cannot set attribute '{name}'")
    # object.__setattr__(self, name, value)
    
    frozen_check = ast.Call(
        func=ast.Name(id="getattr", ctx=ast.Load()),
        args=[
            ast.Name(id="self", ctx=ast.Load()),
            ast.Constant(value="_frozen"),
            ast.Constant(value=False)
        ],
        keywords=[]
    )
    
    err_msg = ast.JoinedStr(values=[
        ast.Constant(value=f"{class_def.name} is immutable — cannot modify attribute '"),
        ast.FormattedValue(value=ast.Name(id="name", ctx=ast.Load()), conversion=-1, format_spec=None),
        ast.Constant(value="'")
    ])
    
    raise_err = ast.Raise(
        exc=ast.Call(func=ast.Name(id="AttributeError", ctx=ast.Load()), args=[err_msg], keywords=[]),
        cause=None
    )
    
    if_frozen = make_if(test=frozen_check, body=[raise_err])
    
    call_object_setattr = ast.Expr(value=ast.Call(
        func=ast.Attribute(value=ast.Name(id="object", ctx=ast.Load()), attr="__setattr__", ctx=ast.Load()),
        args=[
            ast.Name(id="self", ctx=ast.Load()),
            ast.Name(id="name", ctx=ast.Load()),
            ast.Name(id="value", ctx=ast.Load())
        ],
        keywords=[]
    ))
    
    setattr_body = [if_frozen, call_object_setattr]
    setattr_func = make_function("__setattr__", make_arguments([make_arg("self"), make_arg("name", "str"), make_arg("value")]), setattr_body, returns=ast.Constant(value=None))
    
    # __delattr__
    call_object_delattr = ast.Expr(value=ast.Call(
        func=ast.Attribute(value=ast.Name(id="object", ctx=ast.Load()), attr="__delattr__", ctx=ast.Load()),
        args=[
            ast.Name(id="self", ctx=ast.Load()),
            ast.Name(id="name", ctx=ast.Load())
        ],
        keywords=[]
    ))
    delattr_body = [if_frozen, call_object_delattr]
    delattr_func = make_function("__delattr__", make_arguments([make_arg("self"), make_arg("name", "str")]), delattr_body, returns=ast.Constant(value=None))
    
    class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name in ('__setattr__', '__delattr__'))]
    class_def.body.extend([setattr_func, delattr_func])
    
    # We must also inject `object.__setattr__(self, "_frozen", True)` at the end of __init__!
    # Let's find __init__
    init_func = next((n for n in class_def.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"), None)
    
    freeze_stmt = ast.Expr(value=ast.Call(
        func=ast.Attribute(value=ast.Name(id="object", ctx=ast.Load()), attr="__setattr__", ctx=ast.Load()),
        args=[
            ast.Name(id="self", ctx=ast.Load()),
            ast.Constant(value="_frozen"),
            ast.Constant(value=True)
        ],
        keywords=[]
    ))
    
    if init_func:
        # Prepend `object.__setattr__(self, "_frozen", False)`
        unfreeze_stmt = ast.Expr(value=ast.Call(
            func=ast.Attribute(value=ast.Name(id="object", ctx=ast.Load()), attr="__setattr__", ctx=ast.Load()),
            args=[
                ast.Name(id="self", ctx=ast.Load()),
                ast.Constant(value="_frozen"),
                ast.Constant(value=False)
            ],
            keywords=[]
        ))
        init_func.body.insert(0, unfreeze_stmt)
        init_func.body.append(freeze_stmt)
    
    mark_komodo_meta(cls, "immutable")
