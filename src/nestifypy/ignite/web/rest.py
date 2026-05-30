"""
nestifypy.ignite.web.rest
~~~~~~~~~~~~~~~~~~~~~~~~~
HTTP route decorators for use on controller methods.

Usage::

    from nestifypy.ignite.web.rest import Get, Post, Put, Patch, Delete

    @Controller("/users")
    class UserController:

        @Get("/")
        async def list_users(self): ...

        @Post("/")
        async def create_user(self): ...
"""

_ROUTE_ATTR = "__nestifypy_route__"


def _route(method: str, path: str):
    def decorator(fn):
        fn.__nestifypy_route__ = True
        fn.__nestifypy_http_method__ = method.upper()
        fn.__nestifypy_http_path__ = path
        return fn
    return decorator


def Get(path: str = "/"):
    """Map an HTTP GET request to a controller method."""
    return _route("GET", path)


def Post(path: str = "/"):
    """Map an HTTP POST request to a controller method."""
    return _route("POST", path)


def Put(path: str = "/"):
    """Map an HTTP PUT request to a controller method."""
    return _route("PUT", path)


def Patch(path: str = "/"):
    """Map an HTTP PATCH request to a controller method."""
    return _route("PATCH", path)


def Delete(path: str = "/"):
    """Map an HTTP DELETE request to a controller method."""
    return _route("DELETE", path)
