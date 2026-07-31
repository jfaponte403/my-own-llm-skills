from typing import Any

# The boundary layer comes from the `http` skill — write it once per project.
# This file only shows what you write again for every new endpoint.
from core.context import RequestContext
from core.http_validator import http_validator
from models.responses.http_response import HttpResponse, ResponseStatus

# ═════════════════════════════════════════════════════════════
# models/requests/post_product_request.py  (see the `models` skill)
# ═════════════════════════════════════════════════════════════
from pydantic import BaseModel, Field


class PostProductRequest(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)


# ═════════════════════════════════════════════════════════════
# repositories/product_repository.py  (see the `repository` skill)
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
# lambdas/post_product.py
# ═════════════════════════════════════════════════════════════

# POST: /products
@http_validator(
    request_model=PostProductRequest,
    require_auth=True,
    # ownership=lambda ctx: ...,                    # add when editing/reading an existing resource
    # rules=[require_role("seller")],               # from core.rules — role/plan/quota checks
)
def handler(ctx: RequestContext, context: Any) -> dict:
    # ctx.body is already a valid PostProductRequest; ctx.customer_id came from the token.
    product = save_product(product=ctx.body, customer_id=ctx.customer_id)
    return HttpResponse(message=ResponseStatus.SUCCESS, data=product).to_lambda(201)
