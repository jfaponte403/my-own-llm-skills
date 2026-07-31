---
name: http
description: >
  Write the HTTP boundary of a serverless API: the `http_validator`
  decorator that parses and validates the body, resolves the caller from
  the token and runs ownership and business rules, an `HttpError`
  hierarchy with one class per status code, and a single `HttpResponse`
  every endpoint returns. Use when the user asks to "create http
  validator", "add validation", "validate request", or "http boundary".
---

# Writing the HTTP boundary

Follow these rules whenever you build the layer between API Gateway and your handlers, using `template.py` as the base. Assume Pydantic v2.

This is infrastructure you write **once per project**. `template.py` shows a Cognito authorizer, a `cognito:groups` role check and three `ResponseStatus` values — those are **illustrative, not required**. What you copy is the shape: validation lives in the decorator, failures raise, and only the decorator builds a response. The endpoints that consume this layer belong to the `lambdas` skill.

## Rules

1. **Validate at the boundary, never inside the handler.** Parsing, auth, ownership and business rules all run in `@http_validator`. The handler receives a `RequestContext` whose `body` is already a validated model, so it can assume its input is correct.
2. **Raise, don't return.** Failures raise an `HttpError` subclass and the decorator turns it into a response. A layer that builds its own `{"statusCode": ...}` dict is a layer that will drift.
3. **One exception class per status code.** `BadRequest`, `Unauthorized`, `Forbidden`, `NotFound` each carry their code and their `ResponseStatus`. Never pass a raw int around; add a subclass instead.
4. **Ownership comes from the token, never from the request.** Resolve `customer_id` from the claims. An id in the body, the path or a query string is untrusted input and must never decide what the caller may reach.
5. **Business checks are `rules`, not `if`s.** Roles, plans, quotas and feature flags are small `fn(ctx)` that raise, passed as `rules=[...]` and run in order. They stay reusable across endpoints.
6. **Every response is an `HttpResponse`.** Its `message` is a `ResponseStatus` enum, never a free-form string, so clients can branch on a closed set of values. `.to_lambda()` is what attaches the CORS headers.
7. **The catch-all returns 500 and logs.** Never let a traceback reach API Gateway, and never put the exception message in the body — log it (structured/CloudWatch) and return a bare `FAILED`.
8. **Adapt `_extract_claims` to your authorizer.** The template reads `requestContext.authorizer.claims`, which is where a Cognito authorizer puts them; a custom/Lambda authorizer or a different IdP puts them elsewhere.
9. **Declare `ResponseStatus` before `HttpError`.** The exception annotates the enum, so response models come first in the file order. Reordering breaks the import on Python < 3.14.

## File layout

```
core/
  exceptions.py           # HttpError hierarchy, one class per status code
  context.py              # RequestContext passed to every handler
  http_validator.py       # the decorator: auth, body, ownership, rules
  rules.py                # reusable fn(ctx) checks
models/
  responses/
    http_response.py      # ResponseStatus enum + HttpResponse.to_lambda
```
