"""
arkhe.komodo.ast_generators.repr
------------------------------------
AST generator for __repr__ and __str__.
"""

import ast
from typing import Type
from arkhe.komodo.ast_builders import make_arg, make_arguments, make_function, make_return
from arkhe.komodo.ast_generators.utils import get_fields_from_ast, mark_komodo_meta

def generate_to_str(class_def: ast.ClassDef, cls: Type):
    fields = get_fields_from_ast(class_def)
    
    # We want to return f"ClassName(field1={self.field1!r}, ...)"
    # Creating an f-string in AST is a JoinedStr node
    class_name = class_def.name
    
    values = [ast.Constant(value=f"{class_name}(")]
    
    for i, name in enumerate(fields.keys()):
        if i > 0:
            values.append(ast.Constant(value=", "))
        values.append(ast.Constant(value=f"{name}="))
        
        # FormattedValue(value=self.name, conversion=114, format_spec=None)
        # conversion 114 is 'r' (!r)
        values.append(ast.FormattedValue(
            value=ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=name, ctx=ast.Load()),
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
