def Bean(fn):
    """
    Marks a method inside a @Configuration class as a bean factory.

    Usage::

        @Configuration
        class AppConfig:
            @Bean
            def jwt_service(self) -> JwtService:
                return JwtService(secret="my-secret")
    """
    fn.__arkhe_bean__ = True
    return fn
