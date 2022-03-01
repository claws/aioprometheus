from typing import Any, Awaitable, Callable, Dict, Sequence

from aioprometheus import REGISTRY, Counter, Registry

Scope = Dict[str, Any]
Message = Dict[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGICallable = Callable[[Scope, Receive, Send], Awaitable[None]]


EXCLUDE_PATHS = (
    "/metrics",
    "/metrics/",
    "/docs",
    "/openapi.json",
    "/docs/oauth2-redirect",
    "/redoc",
    "/favicon.ico",
)


class MetricsMiddleware:
    """This class implements a Prometheus metrics collection middleware for
    ASGI applications.

    The default metrics provided by this middleware include counters for
    requests received, responses sent, exceptions raised and status codes
    for route handlers.

    :param app: An ASGI callable. This callable represents the next ASGI
      callable in the chain which might be the application or another
      middleware.

    :param registry: A collector registry to use when rendering metrics. If
      not specified then the default registry will be used.

    :param exclude_paths: A list of urls that should not trigger updates to
      the default metrics.

    :param use_template_urls: A boolean that defines whether route template
      URLs should be used by the default route monitoring metrics. Template
      URLs will report '/users/{user_id}' instead of '/users/bob' or
      '/users/alice', etc. The template URLS can be more useful than the
      actual route url as they allow the route handler to be easily
      identified. This feature is only supported with Starlette / FastAPI
      currently.

    :param group_status_codes: A boolean that defines whether status codes
      should be grouped under a value representing that code kind. For
      example, 200, 201, etc will all be grouped under 2xx. The default value
      is False which means that status codes are not grouped.
    """

    def __init__(
        self,
        app: ASGICallable,
        registry: Registry = REGISTRY,
        exclude_paths: Sequence[str] = EXCLUDE_PATHS,
        use_template_urls: bool = True,
        group_status_codes: bool = False,
        const_labels: LabelsType = None,
    ) -> None:
        # The 'app' argument really represents an ASGI framework callable.
        self.asgi_callable = app

        # Starlette applications add a reference to the ASGI app in the
        # lifespan start scope. Save a reference to the ASGI app to assist
        # later when extracting route templates. Only Starlette/FastAPI
        # apps provide this feature.
        self.starlette_app = None

        self.exclude_paths = exclude_paths if exclude_paths else []
        self.use_template_urls = use_template_urls
        self.group_status_codes = group_status_codes

        if registry is not None and not isinstance(registry, Registry):
            raise Exception(f"registry must be a Registry, got: {type(registry)}")
        self.registry = registry

        # Create default metrics

        self.requests_counter = Counter(
            "requests_total_counter",
            "Total number of requests received",
            const_labels=const_labels,
        )

        self.responses_counter = Counter(
            "responses_total_counter",
            "Total number of responses sent",
            const_labels=const_labels,
        )

        self.exceptions_counter = Counter(
            "exceptions_total_counter",
            "Total number of requested which generated an exception",
            const_labels=const_labels,
        )

        self.status_codes_counter = Counter(
            "status_codes_counter",
            "Total number of response status codes",
            const_labels=const_labels,
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send):

        if scope["type"] == "lifespan":
            # Starlette adds a reference to the app in the lifespan start
            # scope. Store a reference to the app to assist later when
            # extracting route templates.
            self.starlette_app = scope.get("app")

        if scope["type"] != "http":
            await self.asgi_callable(scope, receive, send)
            return

        def wrapped_send(response):
            """
            Wrap the ASGI send function so that metrics collection can be finished.
            """
            # This function makes use of labels defined in the calling context.

            if response["type"] == "http.response.start":
                status_code_labels = labels.copy()
                status_code = str(response["status"])
                status_code_labels["status_code"] = (
                    f"{status_code[0]}xx" if self.group_status_codes else status_code
                )
                self.status_codes_counter.inc(status_code_labels)
                self.responses_counter.inc(labels)

            return send(response)

        # Store HTTP path and method attributes in a variable that can be used
        # later in the send method to complete metrics updates.

        method = scope["method"]
        path = self.get_full_or_template_path(scope)

        if path in self.exclude_paths:
            await self.asgi_callable(scope, receive, send)
            return

        labels = dict(method=method, path=path)

        self.requests_counter.inc(labels)
        try:
            await self.asgi_callable(scope, receive, wrapped_send)
        except Exception:
            self.exceptions_counter.inc(labels)

            status_code_labels = labels.copy()
            status_code_labels["status_code"] = (
                "5xx" if self.group_status_codes else "500"
            )
            self.status_codes_counter.inc(status_code_labels)
            self.responses_counter.inc(labels)

            raise

    def get_full_or_template_path(self, scope) -> str:
        """
        Using the route template url can be more insightful than the actual
        route url so that the route handler function can be easily identified.

        For example, seeing the path '/users/{user_id}' in metrics is often
        better than every combination of '/users/bob', /users/alice', etc.

        Obtaining the route template will be a unique procedure for each web
        framework. This feature is currently only supported for Starlette
        and FastAPI applications.
        """
        root_path = scope.get("root_path", "")
        path = scope.get("path", "")
        full_path = f"{root_path}{path}"

        if self.use_template_urls:
            if self.starlette_app:
                # Extract the route template from Starlette / FastAPI apps
                for route in self.starlette_app.routes:
                    match, _child_scope = route.matches(scope)
                    # Enum value 2 represents the route template Match.FULL
                    if match.value == 2:
                        return route.path

        return full_path
