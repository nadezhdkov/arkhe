"""
nestifypy.komodo.ast_generators.logger
--------------------------------------
AST generator for @komodo.logger.
"""

import ast
from typing import Type
from nestifypy.komodo.ast_builders import make_assign, make_call
from nestifypy.komodo.ast_generators.utils import mark_komodo_meta

def generate_logger(class_def: ast.ClassDef, cls: Type):
    # Inject `import logging` at module level in the AST tree, not inside the class.
    # Then add `logger = logging.getLogger(f"{__name__}.{ClassName}")` inside the class body.
    
    get_logger_call = make_call("logging.getLogger", args=[
        ast.JoinedStr(values=[
            ast.FormattedValue(value=ast.Name(id="__name__", ctx=ast.Load()), conversion=-1, format_spec=None),
            ast.Constant(value=f".{class_def.name}")
        ])
    ])
    
    assign_node = make_assign("logger", get_logger_call)
    class_def.body.insert(0, assign_node)
    
    mark_komodo_meta(cls, "logger")


def inject_logger_imports(tree: ast.Module):
    """Called by ast_engine to add `import logging` at the top of the module AST."""
    has_import = any(
        isinstance(n, ast.Import) and any(a.name == "logging" for a in n.names)
        for n in tree.body
    )
    if not has_import:
        tree.body.insert(0, ast.Import(names=[ast.alias(name="logging", asname=None)]))
