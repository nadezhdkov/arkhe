"""
arkhe.komodo.ast_generators.repr
------------------------------------
AST generator for __repr__ and __str__.
"""

import ast
from typing import Type, Optional, List
from arkhe.komodo.ast_builders import make_arg, make_arguments, make_function, make_return
from arkhe.komodo.ast_generators.utils import get_all_fields_from_ast, mark_komodo_meta

def generate_to_str(class_def: ast.ClassDef, cls: Type, onlyExplicitlyIncluded: bool = False, callSuper: bool = False, includeFieldNames: bool = True, doNotUseGetters: bool = False, exclude: Optional[List[str]] = None, of: Optional[List[str]] = None):
    fields = get_all_fields_from_ast(class_def, cls)
    
    class_name = class_def.name
    values = [ast.Constant(value=f"{class_name}(")]
    
    if callSuper:
        # self.__class__.__bases__[0].__name__ is not easily accessible via super() in repr
        # super().__str__() + ", "
        values.append(ast.FormattedValue(
            value=ast.Call(
                func=ast.Attribute(value=ast.Call(func=ast.Name(id="super", ctx=ast.Load()), args=[], keywords=[]), attr="__str__", ctx=ast.Load()),
                args=[], keywords=[]
            ),
            conversion=-1, format_spec=None
        ))
    
    # Filtering fields
    fields_to_include = []
    exclude_list = exclude or []
    of_list = of or []
    
    for name in fields.keys():
        if onlyExplicitlyIncluded and name not in of_list:
            continue
        if of_list and name not in of_list:
            continue
        if name in exclude_list:
            continue
        fields_to_include.append(name)
        
    for i, name in enumerate(fields_to_include):
        if i > 0 or callSuper:
            values.append(ast.Constant(value=", "))
            
        if includeFieldNames:
            values.append(ast.Constant(value=f"{name}="))
            
        getter_name = f"get_{name}"
        has_getter = any(isinstance(n, ast.FunctionDef) and n.name == getter_name for n in class_def.body)
        
        if not doNotUseGetters and has_getter:
            val_ast = ast.Call(func=ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=getter_name, ctx=ast.Load()), args=[], keywords=[])
        else:
            val_ast = ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=name, ctx=ast.Load())
            
        values.append(ast.FormattedValue(
            value=val_ast,
            conversion=114, 
            format_spec=None
        ))
        
    values.append(ast.Constant(value=")"))
    
    joined_str = ast.JoinedStr(values=values)
    body = [make_return(joined_str)]
    
    repr_func = make_function("__repr__", make_arguments([make_arg("self")]), body, returns=ast.Name(id="str", ctx=ast.Load()))
    str_func = make_function("__str__", make_arguments([make_arg("self")]), body, returns=ast.Name(id="str", ctx=ast.Load()))
    
    class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name in ('__repr__', '__str__'))]
    class_def.body.extend([repr_func, str_func])
    
    mark_komodo_meta(cls, "to_str")
