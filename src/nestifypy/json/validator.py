"""
nestifypy.json.validator
---------------------
Schema validation for JSON objects.
"""

from typing import Dict, List, Type, Union

from nestifypy.yaml import DotDict
from nestifypy.json.exceptions import JsonValidationError
from nestifypy.json.models import JsonObject

class JsonValidator:
    """Handles schema validation for JSON objects."""

    @staticmethod
    def validate(data: Union[DotDict, JsonObject], schema: Dict[str, Type]) -> bool:
        """
        Validate a JSON object against a flat schema dict.
        
        Example:
            schema = {"fps": int, "title": str}
            JsonValidator.validate(config, schema)
        """
        errors: List[str] = []
        is_dotdict = isinstance(data, DotDict)
        
        for key, expected_type in schema.items():
            if is_dotdict:
                value = data.get(key)
            else:
                value = data.get(key)
                
            if value is None:
                errors.append(f"Missing required key: '{key}'")
            elif not isinstance(value, expected_type):
                errors.append(
                    f"Key '{key}' must be {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )
                
        if errors:
            raise JsonValidationError("JSON validation failed:\n" + "\n".join(errors))
            
        return True
