"""
nestifypy.komodo.ast_generators.builder
---------------------------------------
AST generator for @komodo.builder.
"""

import ast
from typing import Type
from nestifypy.komodo.ast_builders import make_arg, make_arguments, make_function, make_return, make_if, make_raise, make_call, make_assign, make_attribute_assign
from nestifypy.komodo.ast_generators.utils import get_fields_from_ast, get_defaults_from_ast, mark_komodo_meta, get_komodo_meta

def generate_builder(class_def: ast.ClassDef, cls: Type):
    fields = get_fields_from_ast(class_def)
    defaults = get_defaults_from_ast(class_def)
    
    # Read singulars from metadata if registered by @komodo.singular class decorator
    # E.g. cls.__komodo_singulars__ = ["members"]
    singulars = getattr(cls, "__komodo_singulars__", [])
    
    # Class Builder:
    builder_class = ast.ClassDef(
        name="Builder",
        bases=[],
        keywords=[],
        body=[
            ast.Assign(
                targets=[ast.Name(id="_UNSET", ctx=ast.Store())],
                value=ast.Call(func=ast.Name(id="object", ctx=ast.Load()), args=[], keywords=[])
            )
        ],
        decorator_list=[]
    )
    
    # Builder.__init__
    init_body = []
    for name in fields:
        # if default exists, use it, else _UNSET
        if name in defaults:
            val = defaults[name]
        else:
            val = ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr="_UNSET", ctx=ast.Load())
            
        if name in singulars:
            # Singulars initialize to empty list
            val = ast.List(elts=[], ctx=ast.Load())
            
        init_body.append(make_attribute_assign("self", f"_{name}", val))
        
    if not init_body:
        init_body.append(ast.Pass())
        
    builder_init = make_function("__init__", make_arguments([make_arg("self")]), init_body, returns=ast.Constant(value=None))
    builder_class.body.append(builder_init)
    
    # Builder methods
    for name in fields:
        if name in singulars:
            # def member(self, item): self._members.append(item); return self
            singular_name = name[:-1] if name.endswith("s") else f"single_{name}"
            
            append_body = [
                ast.Expr(value=make_call(f"self._{name}.append", args=[ast.Name(id="item", ctx=ast.Load())])),
                make_return(ast.Name(id="self", ctx=ast.Load()))
            ]
            builder_class.body.append(make_function(
                singular_name,
                make_arguments([make_arg("self"), make_arg("item")]),
                append_body,
                returns=ast.Constant(value=None)
            ))
            # Also keep the regular setter
            setter_body = [
                make_attribute_assign("self", f"_{name}", ast.Name(id="value", ctx=ast.Load())),
                make_return(ast.Name(id="self", ctx=ast.Load()))
            ]
            builder_class.body.append(make_function(
                name,
                make_arguments([make_arg("self"), make_arg("value")]),
                setter_body,
                returns=ast.Constant(value=None)
            ))
        else:
            # def with_name(self, value): self._name = value; return self
            setter_body = [
                make_attribute_assign("self", f"_{name}", ast.Name(id="value", ctx=ast.Load())),
                make_return(ast.Name(id="self", ctx=ast.Load()))
            ]
            builder_class.body.append(make_function(
                f"with_{name}",
                make_arguments([make_arg("self"), make_arg("value")]),
                setter_body,
                returns=ast.Constant(value=None)
            ))
            
    # Builder.build(self)
    build_body = []
    build_kwargs = []
    for name in fields:
        if name not in defaults and name not in singulars:
            # if self._name is self._UNSET: raise ValueError(...)
            is_unset_check = ast.Compare(
                left=ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=f"_{name}", ctx=ast.Load()),
                ops=[ast.Is()],
                comparators=[ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr="_UNSET", ctx=ast.Load())]
            )
            raise_err = make_raise("ValueError", f"{class_def.name}.Builder: required field '{name}' was not set")
            build_body.append(make_if(test=is_unset_check, body=[raise_err]))
            
        build_kwargs.append(ast.keyword(arg=name, value=ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=f"_{name}", ctx=ast.Load())))
        
    build_body.append(
        make_return(ast.Call(
            func=ast.Name(id=class_def.name, ctx=ast.Load()),
            args=[],
            keywords=build_kwargs
        ))
    )
    # Use a string literal as the return annotation so Python treats it as a
    # forward reference and does NOT try to resolve the outer class name inside
    # the Builder's own class scope (which would raise NameError).
    builder_class.body.append(make_function("build", make_arguments([make_arg("self")]), build_body, returns=ast.Constant(value=class_def.name)))
    
    # Remove existing Builder if any
    class_def.body = [n for n in class_def.body if not (isinstance(n, ast.ClassDef) and n.name == "Builder")]
    class_def.body.append(builder_class)
    
    # classmethod builder()
    builder_method_body = [
        make_return(make_call("cls.Builder"))
    ]
    builder_method = make_function("builder", make_arguments([make_arg("cls")]), builder_method_body, returns=ast.Constant(value=None))
    builder_method.decorator_list = [ast.Name(id="classmethod", ctx=ast.Load())]
    
    class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name == "builder")]
    class_def.body.append(builder_method)
    
    mark_komodo_meta(cls, "builder")
