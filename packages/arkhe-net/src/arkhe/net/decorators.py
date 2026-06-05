"""
arkhe.net.decorators
--------------------
API Declarativa para o arkhe.net. Permite definir clientes HTTP
usando decorators em métodos (inspirado em Retrofit / Feign).
"""

from typing import Any, Callable, Dict, Optional, Type, TypeVar, get_type_hints
import inspect

from arkhe.net.net import API, Request

T = TypeVar("T")


def api(base_url: str) -> Callable[[Type[T]], Type[T]]:
    """
    Transforma uma classe num cliente HTTP declarativo.
    Uma instância de `arkhe.net.API` será criada e gerida internamente.
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Salvamos o __init__ original, se houver
        orig_init = getattr(cls, "__init__", None)

        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            # Instancia o cliente API do arkhe.net
            self._api_client = API(base_url)
            
            # Chama o init original
            if orig_init is not None and orig_init is not object.__init__:
                orig_init(self, *args, **kwargs)

        cls.__init__ = new_init  # type: ignore[misc]
        return cls
    return decorator


def _create_http_method(method: str, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        sig = inspect.signature(func)
        hints = get_type_hints(func)
        return_type = hints.get("return", type(None))

        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Bind arguments to extract path parameters and body
            bound = sig.bind(self, *args, **kwargs)
            bound.apply_defaults()
            
            params_dict = dict(bound.arguments)
            params_dict.pop("self", None)

            # Format the path using bound arguments
            formatted_path = path.format(**params_dict)
            
            api_client: API = getattr(self, "_api_client")
            req: Request = api_client.request(formatted_path)
            
            # Remove path variables from params to find the body/query
            # Basic heuristic: if the function accepts 'json', pass it as json.
            # Otherwise, you could pass all remaining arguments as query parameters
            # but for simplicity, we look for explicit 'json' or 'form' kwargs.
            if "json" in params_dict:
                req.json(params_dict["json"])
            elif "form" in params_dict:
                req.form(params_dict["form"])
            
            # Execute request
            resp = req._execute(method)
            resp.raise_for_status()

            # Se o return type for genérico ou Response, podemos retornar direto.
            # Usar .into() se houver um type hint.
            if return_type is type(None):
                return None
            from arkhe.net.net import Response
            if return_type is Response:
                return resp
                
            return resp.into(return_type)

        return wrapper
    return decorator


def get(path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Define um método GET na API Declarativa."""
    return _create_http_method("GET", path)


def post(path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Define um método POST na API Declarativa."""
    return _create_http_method("POST", path)


def put(path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Define um método PUT na API Declarativa."""
    return _create_http_method("PUT", path)


def patch(path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Define um método PATCH na API Declarativa."""
    return _create_http_method("PATCH", path)


def delete(path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Define um método DELETE na API Declarativa."""
    return _create_http_method("DELETE", path)

__all__ = ["api", "get", "post", "put", "patch", "delete"]
