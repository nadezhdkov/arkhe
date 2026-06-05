"""
arkhe.komodo.ast_generators.serialization
---------------------------------------------
AST generators for serialization (to_dict, from_dict, to_json, from_json).
"""

import ast
from typing import Type
from arkhe.komodo.ast_builders import make_arg, make_arguments, make_function, make_return, make_call
from arkhe.komodo.ast_generators.utils import get_all_fields_from_ast, mark_komodo_meta

def generate_to_dict(class_def: ast.ClassDef, cls: Type):
    fields = get_all_fields_from_ast(class_def, cls)
    
    keys = []
    values = []
    for name in fields:
        keys.append(ast.Constant(value=name))
        values.append(ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=name, ctx=ast.Load()))
        
    dict_node = ast.Dict(keys=keys, values=values)
    
    body = [make_return(dict_node)]
    func = make_function("to_dict", make_arguments([make_arg("self")]), body, returns=ast.Name(id="dict", ctx=ast.Load()))
    
    class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name == "to_dict")]
    class_def.body.append(func)
    mark_komodo_meta(cls, "to_dict")

def generate_from_dict(class_def: ast.ClassDef, cls: Type):
    # @classmethod
    # def from_dict(cls, data: dict): return cls(**data)
    
    body = [make_return(ast.Call(
        func=ast.Name(id="cls", ctx=ast.Load()),
        args=[],
        keywords=[ast.keyword(arg=None, value=ast.Name(id="data", ctx=ast.Load()))]
    ))]
    func = make_function("from_dict", make_arguments([make_arg("cls"), make_arg("data", "dict")]), body, returns=ast.Constant(value=None))
    
    # Add @classmethod decorator
    func.decorator_list = [ast.Name(id="classmethod", ctx=ast.Load())]
    
    class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name == "from_dict")]
    class_def.body.append(func)
    mark_komodo_meta(cls, "from_dict")

def generate_json(class_def: ast.ClassDef, cls: Type):
    # requires import json
    
    # to_json
    body_to_json = [
        ast.Import(names=[ast.alias(name="json", asname=None)]),
        make_return(make_call("json.dumps", args=[make_call("self.to_dict")]))
    ]
    func_to = make_function("to_json", make_arguments([make_arg("self")]), body_to_json, returns=ast.Name(id="str", ctx=ast.Load()))
    
    # from_json
    body_from_json = [
        ast.Import(names=[ast.alias(name="json", asname=None)]),
        make_return(make_call("cls.from_dict", args=[make_call("json.loads", args=[ast.Name(id="data", ctx=ast.Load())])]))
    ]
    func_from = make_function("from_json", make_arguments([make_arg("cls"), make_arg("data", "str")]), body_from_json, returns=ast.Constant(value=None))
    func_from.decorator_list = [ast.Name(id="classmethod", ctx=ast.Load())]
    
    class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name in ("to_json", "from_json"))]
    class_def.body.extend([func_to, func_from])
    mark_komodo_meta(cls, "json")
