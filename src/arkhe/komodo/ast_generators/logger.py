"""
arkhe.komodo.ast_generators.logger
--------------------------------------
AST generator for @komodo.logger.
"""

import ast
from typing import Type
from arkhe.komodo.ast_builders import make_assign, make_call
from arkhe.komodo.ast_generators.utils import mark_komodo_meta

import logging
from typing import Optional

def generate_logger(class_def: ast.ClassDef, cls: Type, level: int = logging.DEBUG, topic: Optional[str] = None):
    # Inject `import logging` at module level in the AST tree, not inside the class.
    # Then add `logger = logging.getLogger(f"{__name__}.{ClassName}")` inside the class body.
    
    if topic:
        get_logger_call = make_call("logging.getLogger", args=[ast.Constant(value=topic)])
    else:
        get_logger_call = make_call("logging.getLogger", args=[
            ast.JoinedStr(values=[
                ast.FormattedValue(value=ast.Name(id="__name__", ctx=ast.Load()), conversion=-1, format_spec=None),
                ast.Constant(value=f".{class_def.name}")
            ])
        ])
    
    assign_logger = make_assign("logger", get_logger_call)
    
    # if not logger.hasHandlers():
    #     _h = logging.StreamHandler()
    #     _h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    #     logger.addHandler(_h)
    # logger.setLevel(level)
    
    handler_check = ast.If(
        test=ast.UnaryOp(op=ast.Not(), operand=ast.Call(
            func=ast.Attribute(value=ast.Name(id="logger", ctx=ast.Load()), attr="hasHandlers", ctx=ast.Load()),
            args=[], keywords=[]
        )),
        body=[
            make_assign("_h", ast.Call(func=ast.Attribute(value=ast.Name(id="logging", ctx=ast.Load()), attr="StreamHandler", ctx=ast.Load()), args=[], keywords=[])),
            ast.Expr(value=ast.Call(
                func=ast.Attribute(value=ast.Name(id="_h", ctx=ast.Load()), attr="setFormatter", ctx=ast.Load()),
                args=[ast.Call(
                    func=ast.Attribute(value=ast.Name(id="logging", ctx=ast.Load()), attr="Formatter", ctx=ast.Load()),
                    args=[ast.Constant(value="%(asctime)s - %(name)s - %(levelname)s - %(message)s")],
                    keywords=[]
                )],
                keywords=[]
            )),
            ast.Expr(value=ast.Call(
                func=ast.Attribute(value=ast.Name(id="logger", ctx=ast.Load()), attr="addHandler", ctx=ast.Load()),
                args=[ast.Name(id="_h", ctx=ast.Load())],
                keywords=[]
            ))
        ],
        orelse=[]
    )
    
    set_level = ast.Expr(value=ast.Call(
        func=ast.Attribute(value=ast.Name(id="logger", ctx=ast.Load()), attr="setLevel", ctx=ast.Load()),
        args=[ast.Constant(value=level)],
        keywords=[]
    ))
    
    # Prepend these instructions in reverse order or just insert them sequentially
    class_def.body.insert(0, set_level)
    class_def.body.insert(0, handler_check)
    class_def.body.insert(0, assign_logger)
    
    mark_komodo_meta(cls, "logger")


def inject_logger_imports(tree: ast.Module):
    """Called by ast_engine to add `import logging` at the top of the module AST."""
    has_import = any(
        isinstance(n, ast.Import) and any(a.name == "logging" for a in n.names)
        for n in tree.body
    )
    if not has_import:
        tree.body.insert(0, ast.Import(names=[ast.alias(name="logging", asname=None)]))
