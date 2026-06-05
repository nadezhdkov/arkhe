"""
arkhe.komodo.ast_generators.accessors
-----------------------------------------
AST generator for accessors (getter, setter, fluent).
"""

import ast
from typing import Type
from arkhe.komodo.ast_builders import make_arg, make_arguments, make_function, make_return, make_attribute_assign, make_if, make_call
from arkhe.komodo.ast_generators.utils import get_fields_from_ast, get_inherited_fields, mark_komodo_meta
from arkhe.komodo.access_level import AccessLevel

def _annotation_to_ast(annotation) -> ast.expr:
    """Convert a runtime annotation to an AST expression node."""
    if isinstance(annotation, ast.expr):
        return annotation
    if isinstance(annotation, type):
        return ast.Name(id=annotation.__name__, ctx=ast.Load())
    if isinstance(annotation, str):
        return ast.Name(id=annotation, ctx=ast.Load())
    return ast.Constant(value=None)

def generate_accessors(class_def: ast.ClassDef, cls: Type, fluent: bool = False, getter: bool = True, setter: bool = True, withers: bool = False, access: AccessLevel = AccessLevel.PUBLIC):
    if access == AccessLevel.NONE:
        return

    prefix = ""
    if access == AccessLevel.PROTECTED:
        prefix = "_"
    elif access == AccessLevel.PRIVATE:
        prefix = "__"

    # Own fields (declared in this class body)
    own_fields = get_fields_from_ast(class_def)

    # Inherited fields: convert runtime annotations to AST nodes
    inherited_runtime = get_inherited_fields(cls)
    inherited_fields = {
        name: _annotation_to_ast(ann)
        for name, ann in inherited_runtime.items()
        if name not in own_fields
    }

    # Combined: inherited first (top-down order), then own
    fields = {**inherited_fields, **own_fields}

    for name in fields:
        # Accessors operate on the public attribute (self.name), which is what
        # the generated __init__ assigns.  Using self._name would cause
        # AttributeError because no underscore-prefixed attribute is ever set
        # by the constructor unless @komodo.immutable is also applied.
        public_name = name

        if fluent:
            # def name(self, *args):
            #     if not args: return self.name
            #     self.name = args[0]
            #     return self

            body = []

            not_args = ast.UnaryOp(op=ast.Not(), operand=ast.Name(id="args", ctx=ast.Load()))
            return_val = make_return(ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=public_name, ctx=ast.Load()))

            body.append(make_if(test=not_args, body=[return_val]))

            args_0 = ast.Subscript(value=ast.Name(id="args", ctx=ast.Load()), slice=ast.Constant(value=0), ctx=ast.Load())
            body.append(make_attribute_assign("self", public_name, args_0))
            body.append(make_return(ast.Name(id="self", ctx=ast.Load())))

            args = make_arguments([make_arg("self")])
            args.vararg = make_arg("args")
            method_name = f"{prefix}{name}"
            func = make_function(method_name, args, body, returns=ast.Constant(value=None))

            class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name == method_name)]
            class_def.body.append(func)

        else:
            if getter:
                # def get_name(self) -> <type>:
                #     return self.name
                get_method_name = f"{prefix}get_{name}"
                body = [make_return(ast.Attribute(
                    value=ast.Name(id="self", ctx=ast.Load()),
                    attr=public_name,
                    ctx=ast.Load()
                ))]
                func_get = make_function(
                    get_method_name,
                    make_arguments([make_arg("self")]),
                    body,
                    returns=fields[name]
                )
                class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name == get_method_name)]
                class_def.body.append(func_get)

            if setter:
                # def set_name(self, value: <type>) -> None:
                #     self.name = value
                set_method_name = f"{prefix}set_{name}"
                body = [make_attribute_assign("self", public_name, ast.Name(id="value", ctx=ast.Load()))]
                func_set = make_function(
                    set_method_name,
                    make_arguments([make_arg("self"), make_arg("value", fields[name])]),
                    body,
                    returns=ast.Constant(value=None)
                )
                class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name == set_method_name)]
                class_def.body.append(func_set)

        if withers:
            # def with_name(self, value: <type>) -> Self:
            #     return self.copy_with(name=value)
            body = [make_return(make_call("self.copy_with", kwargs=[ast.keyword(arg=name, value=ast.Name(id="value", ctx=ast.Load()))]))]
            with_method_name = f"{prefix}with_{name}"
            func_with = make_function(
                with_method_name,
                make_arguments([make_arg("self"), make_arg("value", fields[name])]),
                body,
                returns=ast.Constant(value=None)
            )
            class_def.body = [n for n in class_def.body if not (isinstance(n, ast.FunctionDef) and n.name == with_method_name)]
            class_def.body.append(func_with)

    mark_komodo_meta(cls, "accessors")
