---
name: models
description: >
  Write Pydantic models that define the shape and validation of your
  entities. Covers request models (input), the DB model (source of truth),
  response models (output, hiding secrets), and enums for fixed value sets.
  Use when the user asks to "create model", "write model", "add model", or
  "new model".
---

# Writing models

Follow these rules whenever you create a Pydantic model, using `template.py` as the base. Assume Pydantic v2.

`template.py` shows a `Customer` with `name`, `age`, `email`, `password_hash`, `status` — those fields are **illustrative, not required**. What you copy is the pattern: one model per role, secrets absent from the response, enums for fixed value sets. The actual fields come from the entity you're modeling, and only exist if the domain needs them (an entity without a password has no `password_hash`; one without a fixed lifecycle has no status enum).

## Rules

1. **Separate models by role.** Never reuse one model everywhere:
   - `XxxModel` — source of truth, matches what's stored in the DB.
   - `CreateXxxRequest` / `UpdateXxxRequest` — client input.
   - `XxxResponse` — client output, never includes secrets.
2. **Never return the DB model directly.** Always map to a response model so secrets can't leak.
3. **Exclude secrets at the type level**, not manually per endpoint. If a field must never leave the server (e.g. `password_hash`), it must not exist on the response model.
4. **Passwords are never plain fields on the DB model.** Store a `password_hash`; accept the raw `password` only on the create request.
5. **Use rich types over primitives:** `EmailStr` for emails, constrained `Field` (`gt`, `lt`, `min_length`) instead of bare `str`/`int`.
6. **Request models validate input automatically.** Pass them as the endpoint parameter — FastAPI returns 422 on invalid bodies. Pair every endpoint with `response_model=XxxResponse`.
7. **Update requests have all fields optional** (`X | None = None`), so clients can send partial patches.
8. **Use `str, Enum` for fixed value sets** (status, roles, types). Inheriting from `str` keeps them JSON-serializable and readable in the DB; Pydantic rejects any value outside the enum.
9. **Enable attribute reading** with `model_config = ConfigDict(from_attributes=True)` on models built from DB/ORM objects.

## File layout

```
models/
  customer.py             # enum + request/DB/response models per entity
  order.py
```