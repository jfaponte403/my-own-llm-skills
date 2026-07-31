# My own LLM skills

A small collection of [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) that I use in my daily work.

They are meant to be used together: `models` defines the entities, `repository` stores and returns those models, `http` guards the boundary, `lambdas` exposes them as endpoints, and `tests` verifies the result.

## Skills

| Skill | Folder | What it does |
|-------|--------|--------------|
| `models` | [`models/`](models/) | Rules for Pydantic v2 models: one model per role (`CreateXxxRequest` / `UpdateXxxRequest` for input, `XxxModel` as the DB source of truth, `XxxResponse` for output), never return the DB model directly, exclude secrets at the type level instead of stripping them per endpoint, store `password_hash` and accept `password` only on create, prefer rich types (`EmailStr`, constrained `Field`) over primitives, all-optional update requests, and `str, Enum` for fixed value sets. Includes a `template.py` starter file. Triggers on "create model", "write model", "add model", "new model". |
| `repository` | [`repository/`](repository/) | Rules for the data access layer: never touch the database directly — everything goes through a `StorageAdapter` so persistence (DynamoDB, SQL, in-memory) can be swapped, always return a model instead of a raw dict, parametrize `BaseRepository[T]` with the entity's DB model from the `models` skill, one repository per entity with shared CRUD in the base, consistent method names (`create`, `get`, `update`, `delete`, `list`), and adapter injected through the constructor. Includes a `template.py` starter file and a `reference.md` cheat sheet. Triggers on "create repository", "write repository", "add repository", "new repository". |
| `http` | [`http/`](http/) | Rules for the HTTP boundary of a serverless API: validate at the boundary and never inside the handler — `@http_validator` parses the body, resolves the caller from the token and runs ownership and business rules, failures raise an `HttpError` subclass instead of returning a hand-built dict, one exception class per status code so no raw ints travel around, ownership always comes from the token and never from the body or path, roles/plans/quotas are reusable `fn(ctx)` rules rather than `if`s in the handler, every response is an `HttpResponse` whose `message` is a `ResponseStatus` enum, and the catch-all returns a bare 500 without leaking the exception message. Includes a `template.py` starter file. Triggers on "create http validator", "add validation", "validate request", "http boundary". |
| `lambdas` | [`lambdas/`](lambdas/) | Rules for AWS Lambda handlers behind API Gateway: one file per endpoint with a single `handler(ctx, context)`, always decorated with `@http_validator` from the `http` skill, no JSON parsing and no `try`/`except` inside the handler, input read only from the `RequestContext` (`body`, `path_params`, `query_params`, `customer_id`) and never from the raw `event`, ownership taken from the token instead of the request, `HttpResponse(...).to_lambda(status)` returned with the right code, and persistence delegated to a repository. Includes a `template.py` starter file. Triggers on "create lambda", "write lambda", "add endpoint", "new endpoint". |
| `tests` | [`tests/`](tests/) | Rules for writing Python tests: keep the payload a visible dict inside the test, assert only `statusCode` and `body` in a single `assertEqual` against a full expected dict, never use `MagicMock` (use `responses`/`respx`, `moto`, in-memory `sqlite` instead), set up mocks in `setUp`, and import the real handler. Includes a `template.py` starter file and a `reference.md` cheat sheet. Triggers on "write tests", "run tests", "add testing". |

## Installation

Copy (or symlink) a skill folder into your skills directory.

**Globally**, so it's available in every project:

```
C:\Users\<your-name>\.claude\skills\
```

**Per project**, so it's available only there:

```
.claude\skills\
```

## Working on this repo

The templates are type-checked against real Pydantic, so install the dependency before editing them:

```
pip install -r requirements.txt
```
