"""
arkhe.komodo.ast_generators.eq_hash
---------------------------------------
AST generator for __eq__ and __hash__.
"""

import ast
from typing import Type
from arkhe.komodo.ast_builders import make_arg, make_arguments, make_function, make_return, make_if, make_call
from arkhe.komodo.ast_generators.utils import get_fields_from_ast, mark_komodo_meta

def generate_eq_hash(class_def: ast.ClassDef, cls: Type):
    fields = get_fields_from_ast(class_def)
    field_names = list(fields.keys())
    
    # __eq__
    # if not isinstance(other, __class__): return NotImplemented
    # return self.f1 == other.f1 and self.f2 == other.f2 ...
    
    isinstance_check = ast.UnaryOp(
        op=ast.Not(),
        operand=make_call("isinstance", args=[
            ast.Name(id="other", ctx=ast.Load()),
            ast.Name(id="__class__", ctx=ast.Load())
        ])
    )
    
    if_not_isinstance = make_if(
        test=isinstance_check,
        body=[make_return(ast.Name(id="NotImplemented", ctx=ast.Load()))]
    )
    
    if not field_names:
        eq_body = [if_not_isinstance, make_return(ast.Constant(value=True))]
    else:
        comparisons = []
        for name in field_names:
            comparisons.append(ast.Compare(
                left=ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=name, ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Attribute(value=ast.Name(id="other", ctx=ast.Load()), attr=name, ctx=ast.Load())]
            ))
            
        if len(comparisons) == 1:
            ret_val = comparisons[0]
        else:
            ret_val = ast.BoolOp(op=ast.And(), values=comparisons)
            
        eq_body = [if_not_isinstance, make_return(ret_val)]
        
    eq_func = make_function("__eq__", make_arguments([make_arg("self"), make_arg("other", "object")]), eq_body, returns=ast.Name(id="bool", ctx=ast.Load()))
    
    # __hash__
    # try: return hash((self.f1, self.f2))
    # except TypeError: return id(self)
    
    if not field_names:
        hash_body = [make_return(ast.Constant(value=0))]
    else:
        hash_args = []
        for name in field_names:
            hash_args.append(ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=name, ctx=ast.Load()))
        
        tuple_node = ast.Tuple(elts=hash_args, ctx=ast.Load())
        hash_val = make_call("hash", args=[tuple_node])
        
        try_body = [make_return(hash_val)]
        except_body = [make_return(make_call("id", args=[ast.Name(id="self", ctx=ast.Load())]))]
        
        handler = ast.ExceptHandler(
            type=ast.Name(id="TypeError", ctx=ast.Load()),
            name=None,
            body=except_body
        )
        
        try_stmt = ast.Try(
            body=try_body,
            handlers=[handler],
            orelse=[],
            finalbody=[]
        )
        
        hash_body = [try_stmt]
        
    hash_func = make_function("__hash__", make_arguments([make_arg("self")]), hash_body, returns=ast.Name(id="int", ctx=ast.Load()))
    
    class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name in ('__eq__', '__hash__'))]
    class_def.body.extend([eq_func, hash_func])
    
    mark_komodo_meta(cls, "eq")
