# ═════════════════════════════════════════════════════════════
# models/responses/http_response.py
# ═════════════════════════════════════════════════════════════
import enum
from typing import Any

from pydantic import BaseModel

DEFAULT_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*",
    "Content-Type": "application/json",
}


class ResponseStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    NOT_FOUND = "not_found"


class HttpResponse(BaseModel):
    message: ResponseStatus
    data: Any = None

    def to_lambda(self, status_code: int, headers: dict | None = None) -> dict:
        return {
            "statusCode": status_code,
            "headers": {**DEFAULT_CORS_HEADERS, **(headers or {})},
            "body": self.model_dump_json(),
        }


# ═════════════════════════════════════════════════════════════
# core/exceptions.py
# ═════════════════════════════════════════════════════════════
# Declared after ResponseStatus on purpose: HttpError annotates it.
# One class per status code, so no handler ever passes a raw int around.


class HttpError(Exception):
    def __init__(self, status_code: int, message: ResponseStatus, data: Any = None) -> None:
        self.status_code = status_code
        self.message = message
        self.data = data


class BadRequest(HttpError):
    def __init__(self, data: Any = None) -> None:
        super().__init__(400, ResponseStatus.FAILED, data)


class Unauthorized(HttpError):
    def __init__(self, data: Any = None) -> None:
        super().__init__(401, ResponseStatus.FAILED, data)


class Forbidden(HttpError):
    def __init__(self, data: Any = None) -> None:
        super().__init__(403, ResponseStatus.FAILED, data)


class NotFound(HttpError):
    def __init__(self, data: Any = None) -> None:
        super().__init__(404, ResponseStatus.NOT_FOUND, data)


# ═════════════════════════════════════════════════════════════
# core/context.py
# ═════════════════════════════════════════════════════════════
from dataclasses import dataclass, field


# Everything a handler is allowed to read. The raw event stays here
# so handlers never reach into it themselves.
@dataclass
class RequestContext:
    event: dict
    customer_id: str | None = None
    claims: dict | None = None
    body: Any = None  # parsed pydantic request
    path_params: dict = field(default_factory=dict)
    query_params: dict = field(default_factory=dict)


# ═════════════════════════════════════════════════════════════
# core/http_validator.py
# ═════════════════════════════════════════════════════════════
import json
from functools import wraps
from typing import Callable

from pydantic import BaseModel, ValidationError


def _extract_claims(event: dict) -> dict:
    # Cognito Authorizer drops claims here. Adjust if you use a
    # custom/Lambda authorizer or a different IdP.
    try:
        return event["requestContext"]["authorizer"]["claims"]
    except (KeyError, TypeError):
        raise Unauthorized()


def http_validator(
        *,
        request_model: type[BaseModel] | None = None,
        require_auth: bool = True,
        ownership: Callable[[RequestContext], bool] | None = None,
        rules: list[Callable[[RequestContext], None]] | None = None,
) -> Callable:
    """
    request_model → parse & validate the JSON body with Pydantic
    require_auth  → require valid claims and resolve customer_id
    ownership     → fn(ctx) -> bool: does the resource belong to the caller?
    rules         → list of fn(ctx) that raise HttpError on failure
                    (roles, plans, feature flags, rate limits, etc.)
    """

    def decorator(handler: Callable) -> Callable:
        @wraps(handler)
        def wrapper(event: dict, context: Any) -> dict:
            try:
                ctx = RequestContext(
                    event=event,
                    path_params=event.get("pathParameters") or {},
                    query_params=event.get("queryStringParameters") or {},
                )

                # 1. Auth + customer_id from token
                if require_auth:
                    ctx.claims = _extract_claims(event)
                    ctx.customer_id = ctx.claims.get("sub")  # or "custom:customer_id"
                    if not ctx.customer_id:
                        raise Unauthorized()

                # 2. Body validation
                if request_model is not None:
                    raw = event.get("body")
                    if raw is None:
                        raise BadRequest()
                    body = json.loads(raw) if isinstance(raw, str) else raw
                    ctx.body = request_model.model_validate(body)

                # 3. Ownership check
                if ownership is not None and not ownership(ctx):
                    raise Forbidden()

                # 4. Custom rules (run in order, each raises on failure)
                for rule in (rules or []):
                    rule(ctx)

                return handler(ctx, context)

            except HttpError as e:
                return HttpResponse(message=e.message, data=e.data).to_lambda(e.status_code)
            except (json.JSONDecodeError, ValidationError):
                return HttpResponse(message=ResponseStatus.FAILED).to_lambda(400)
            except Exception:
                # Last-resort catch-all → 500. Log here (structured/CloudWatch).
                # Never let the exception message reach the client.
                return HttpResponse(message=ResponseStatus.FAILED).to_lambda(500)

        return wrapper

    return decorator


# ═════════════════════════════════════════════════════════════
# core/rules.py
# ═════════════════════════════════════════════════════════════
# Reusable checks: small fn(ctx) that raise. Add plans, quotas, flags here.


def require_role(role: str) -> Callable[[RequestContext], None]:
    def _rule(ctx: RequestContext) -> None:
        if role not in (ctx.claims or {}).get("cognito:groups", []):
            raise Forbidden({"reason": "role_required"})

    return _rule
