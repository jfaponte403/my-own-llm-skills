# ═════════════════════════════════════════════════════════════
# core/exceptions.py
# ═════════════════════════════════════════════════════════════

class HttpError(Exception):
    def __init__(self, status_code: int, message: ResponseStatus, data=None):
        self.status_code = status_code
        self.message = message
        self.data = data


class BadRequest(HttpError):
    def __init__(self, data=None):
        super().__init__(400, ResponseStatus.FAILED, data)


class Unauthorized(HttpError):
    def __init__(self, data=None):
        super().__init__(401, ResponseStatus.FAILED, data)


class Forbidden(HttpError):
    def __init__(self, data=None):
        super().__init__(403, ResponseStatus.FAILED, data)


class NotFound(HttpError):
    def __init__(self, data=None):
        super().__init__(404, ResponseStatus.NOT_FOUND, data)


# ═════════════════════════════════════════════════════════════
# core/context.py
# ═════════════════════════════════════════════════════════════
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RequestContext:
    event: dict
    customer_id: Optional[str] = None
    claims: Optional[dict] = None
    body: Any = None  # parsed pydantic request
    path_params: dict = field(default_factory=dict)
    query_params: dict = field(default_factory=dict)


# ═════════════════════════════════════════════════════════════
# core/http_validator.py
# ═════════════════════════════════════════════════════════════
import json
from functools import wraps
from typing import Callable, Optional, Type

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
        request_model: Optional[Type[BaseModel]] = None,
        require_auth: bool = True,
        ownership: Optional[Callable[[RequestContext], bool]] = None,
        rules: Optional[list[Callable[[RequestContext], None]]] = None,
):
    """
    request_model → parse & validate the JSON body with Pydantic
    require_auth  → require valid claims and resolve customer_id
    ownership     → fn(ctx) -> bool: does the resource belong to the caller?
    rules         → list of fn(ctx) that raise HttpError on failure
                    (roles, plans, feature flags, rate limits, etc.)
    """

    def decorator(handler: Callable):
        @wraps(handler)
        def wrapper(event, context):
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
                return HttpResponse(message=ResponseStatus.FAILED).to_lambda(500)

        return wrapper

    return decorator


# ═════════════════════════════════════════════════════════════
# core/rules.py
# ═════════════════════════════════════════════════════════════


def require_role(role: str):
    def _rule(ctx: RequestContext):
        if role not in (ctx.claims or {}).get("cognito:groups", []):
            raise Forbidden({"reason": "role_required"})

    return _rule


# ═════════════════════════════════════════════════════════════
# models/requests/post_product_request.py
# ═════════════════════════════════════════════════════════════
from pydantic import BaseModel


class PostProductRequest(BaseModel):
    name: str
    price: float


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
# repositories/product_repository.py
# ═════════════════════════════════════════════════════════════
import uuid


def save_product(product: PostProductRequest, customer_id: str) -> dict:
    item = {
        "id": str(uuid.uuid4()),
        "customer_id": customer_id,  # ownership stamped from the token
        **product.model_dump(),  # spread all validated fields
    }
    return item


# ═════════════════════════════════════════════════════════════
# {lambdas||http||endpoints}/post_product.py
# ═════════════════════════════════════════════════════════════

# POST: /products
@http_validator(
    request_model=PostProductRequest,
    require_auth=True,
    # ownership=lambda ctx: ...,          # add when editing/reading an existing resource
    # rules=[require_role("seller")],     # add role/plan/quota checks here
)
def handler(ctx: RequestContext, context):
    product = save_product(product=ctx.body, customer_id=ctx.customer_id)
    return HttpResponse(message=ResponseStatus.SUCCESS, data=product).to_lambda(201)
