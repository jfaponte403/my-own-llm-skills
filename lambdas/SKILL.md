---
name: lambdas
description: >
  Write AWS Lambda handlers behind API Gateway: one file per endpoint, a
  `handler` decorated with `@http_validator`, input read only from the
  `RequestContext`, persistence delegated to a repository, and an
  `HttpResponse` returned with the right status code. Use when the user
  asks to "create lambda", "write lambda", "add endpoint", or "new
  endpoint".
---

# Writing a Lambda handler

Follow these rules whenever you add an endpoint, using `template.py` as the base. Assume Pydantic v2.

This skill covers **one endpoint**. The boundary layer it depends on — `http_validator`, `RequestContext`, `HttpResponse`, the `HttpError` hierarchy — belongs to the `http` skill and is written once per project; `template.py` imports it rather than redefining it. The `Product` fields and the `save_product` helper are **illustrative, not required**: the entity comes from the `models` skill and its persistence from the `repository` skill.

## Rules

1. **One file per endpoint, one handler per file.** Name the function `handler` and give it the signature `(ctx: RequestContext, context)`. Two endpoints in one file means two things to redeploy together.
2. **Decorate every handler with `@http_validator`.** A bare handler is an unvalidated handler — pass `request_model` whenever the endpoint has a body.
3. **No parsing and no `try`/`except` in the handler.** If you are writing `json.loads`, reading claims by hand, or returning a 400, that logic belongs in the decorator or in a rule.
4. **Read input only from `ctx`** — `ctx.body`, `ctx.path_params`, `ctx.query_params`, `ctx.customer_id`. Never touch `event` directly; that is what the decorator normalized away.
5. **Never take ownership from the body or the path.** Pass `ctx.customer_id`, which the decorator resolved from the token, so a client cannot write rows it does not own.
6. **Return `HttpResponse(...).to_lambda(status)`** with the right code — `201` on create, `200` on read/update. Never hand-build the response dict.
7. **Keep persistence in a repository.** The handler orchestrates: call the repository, shape the response. No queries, no adapter calls, no SQL.

## File layout

```
lambdas/                          # or endpoints/
  post_product.py                 # POST /products
  get_product.py                  # GET /products/{id}
models/
  requests/
    post_product_request.py       # one request model per endpoint
repositories/
  product_repository.py
```

## Counter-example: don't parse and guard inside the handler

❌ **Bad** — the endpoint re-implements the boundary, and gets it wrong:

```python
def handler(event, context):
    try:
        body = json.loads(event["body"])
        if not body.get("name") or body.get("price", 0) <= 0:
            return {"statusCode": 400, "body": json.dumps({"message": "invalid"})}

        claims = event["requestContext"]["authorizer"]["claims"]
        customer_id = claims["sub"]

        # trusts an id the client sent
        product = save_product(product=body, customer_id=body.get("customer_id", customer_id))

        return {"statusCode": 201, "body": json.dumps(product)}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": str(e)})}
```

✅ **Good** — the decorator owns validation, the handler owns the use case:

```python
# POST: /products
@http_validator(request_model=PostProductRequest, require_auth=True)
def handler(ctx: RequestContext, context: Any) -> dict:
    product = save_product(product=ctx.body, customer_id=ctx.customer_id)
    return HttpResponse(message=ResponseStatus.SUCCESS, data=product).to_lambda(201)
```

The bad version leaks the exception message to the client, forgets the CORS headers, lets the caller stamp someone else's `customer_id`, and duplicates validation that Pydantic already does — in every single endpoint file. The good version cannot: `ctx.body` is a validated model and `ctx.customer_id` came from the token.
