"""
nestifypy.komodo.ast_generators.record
--------------------------------------
AST generator for @komodo.record.
"""

import ast
from typing import Type
from nestifypy.komodo.ast_generators.constructor import generate_constructor
from nestifypy.komodo.ast_generators.repr import generate_to_str
from nestifypy.komodo.ast_generators.eq_hash import generate_eq_hash
from nestifypy.komodo.ast_generators.immutable import generate_immutable
from nestifypy.komodo.ast_generators.serialization import generate_to_dict, generate_from_dict, generate_json
from nestifypy.komodo.ast_generators.utils import mark_komodo_meta

def generate_record(class_def: ast.ClassDef, cls: Type):
    """
    Applies the full record generation:
    constructor, repr, eq/hash, immutable, and serialization.
    """
    generate_constructor(class_def, cls, mode="all")
    generate_to_str(class_def, cls)
    generate_eq_hash(class_def, cls)
    generate_immutable(class_def, cls)
    generate_to_dict(class_def, cls)
    generate_from_dict(class_def, cls)
    generate_json(class_def, cls)
    
    mark_komodo_meta(cls, "record")
