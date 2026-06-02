"""
nestifypy.komodo.ast_generators.accessors
-----------------------------------------
AST generator for accessors (getter, setter, fluent).
"""

import ast
from typing import Type
from nestifypy.komodo.ast_builders import make_arg, make_arguments, make_function, make_return, make_attribute_assign, make_if, make_call
from nestifypy.komodo.ast_generators.utils import get_fields_from_ast, mark_komodo_meta

def generate_accessors(class_def: ast.ClassDef, cls: Type, fluent: bool = False, getter: bool = True, setter: bool = True, withers: bool = False):
    fields = get_fields_from_ast(class_def)
    
    for name in fields:
        private_name = f"_{name}"
        
        if fluent:
            # def name(self, *args):
            #     if not args: return self._name
            #     self._name = args[0]
            #     return self
            
            body = []
            
            not_args = ast.UnaryOp(op=ast.Not(), operand=ast.Name(id="args", ctx=ast.Load()))
            return_val = make_return(ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=private_name, ctx=ast.Load()))
            
            body.append(make_if(test=not_args, body=[return_val]))
            
            args_0 = ast.Subscript(value=ast.Name(id="args", ctx=ast.Load()), slice=ast.Constant(value=0), ctx=ast.Load())
            body.append(make_attribute_assign("self", private_name, args_0))
            body.append(make_return(ast.Name(id="self", ctx=ast.Load())))
            
            args = make_arguments([make_arg("self")])
            args.vararg = make_arg("args")
            func = make_function(name, args, body, returns=ast.Constant(value=None))
            
            class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name == name)]
            class_def.body.append(func)
            
        else:
            if getter:
                # @name.getter if setter exists, else @property
                has_setter = any(isinstance(n, ast.FunctionDef) and n.name == name and any(isinstance(d, ast.Attribute) and d.attr == "setter" for d in n.decorator_list) for n in class_def.body)
                
                body = [make_return(make_call("getattr", args=[ast.Name(id="self", ctx=ast.Load()), ast.Constant(value=private_name), ast.Constant(value=None)]))]
                func_get = make_function(name, make_arguments([make_arg("self")]), body, returns=ast.Constant(value=None))
                
                if has_setter:
                    func_get.decorator_list = [ast.Attribute(value=ast.Name(id=name, ctx=ast.Load()), attr="getter", ctx=ast.Load())]
                else:
                    func_get.decorator_list = [ast.Name(id="property", ctx=ast.Load())]
                    
                class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name == name and getattr(n.decorator_list[0], "id", "") == "property")]
                class_def.body.append(func_get)
                
            if setter:
                # @name.setter
                # def name(self, value): self._name = value
                
                has_getter = any(isinstance(n, ast.FunctionDef) and n.name == name for n in class_def.body)
                if not has_getter and not getter:
                    # If we only have setter, we must create a base property first
                    # name = property()
                    prop_assign = ast.Assign(
                        targets=[ast.Name(id=name, ctx=ast.Store())],
                        value=ast.Call(func=ast.Name(id="property", ctx=ast.Load()), args=[], keywords=[])
                    )
                    class_def.body.append(prop_assign)
                    
                body = [make_attribute_assign("self", private_name, ast.Name(id="value", ctx=ast.Load()))]
                func_set = make_function(name, make_arguments([make_arg("self"), make_arg("value")]), body, returns=ast.Constant(value=None))
                func_set.decorator_list = [ast.Attribute(value=ast.Name(id=name, ctx=ast.Load()), attr="setter", ctx=ast.Load())]
                class_def.body.append(func_set)
                
        if withers:
            # def with_name(self, value):
            #     return self.copy_with(name=value)
            body = [make_return(make_call("self.copy_with", kwargs=[ast.keyword(arg=name, value=ast.Name(id="value", ctx=ast.Load()))]))]
            func_with = make_function(f"with_{name}", make_arguments([make_arg("self"), make_arg("value")]), body, returns=ast.Constant(value=None))
            class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name == f"with_{name}")]
            class_def.body.append(func_with)

    mark_komodo_meta(cls, "accessors")
