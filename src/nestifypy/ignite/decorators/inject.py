def Inject(fn):
    """
    Marks a method or field for explicit dependency injection.
    Constructor injection is preferred; use @Inject for setter or field injection.
    """
    fn.__nestifypy_inject__ = True
    return fn
