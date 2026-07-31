# My own LLM skills

A small collection of [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) that I use in my daily work.

They are meant to be used together: `models` defines the entities, `repository` stores and returns those models, `services` does the work on top of them, `http` guards the boundary, `lambdas` exposes them as endpoints, and `tests` verifies the result. `services` is also the one that reaches the frontend, where it wraps the API those endpoints expose — and from there `hooks` owns the state and the exceptions of a screen, while `components` only render what the hook hands them.

## Skills

| Skill | Folder | What it does |
|-------|--------|--------------|
| `models` | [`models/`](models/) | Rules for Pydantic v2 models: one model per role (`CreateXxxRequest` / `UpdateXxxRequest` for input, `XxxModel` as the DB source of truth, `XxxResponse` for output), never return the DB model directly, exclude secrets at the type level instead of stripping them per endpoint, store `password_hash` and accept `password` only on create, prefer rich types (`EmailStr`, constrained `Field`) over primitives, all-optional update requests, and `str, Enum` for fixed value sets. Includes a `template.py` starter file. Triggers on "create model", "write model", "add model", "new model". |
| `repository` | [`repository/`](repository/) | Rules for the data access layer: never touch the database directly — everything goes through a `StorageAdapter` so persistence (DynamoDB, SQL, in-memory) can be swapped, always return a model instead of a raw dict, parametrize `BaseRepository[T]` with the entity's DB model from the `models` skill, one repository per entity with shared CRUD in the base, consistent method names (`create`, `get`, `update`, `delete`, `list`), and adapter injected through the constructor. Includes a `template.py` starter file and a `reference.md` cheat sheet. Triggers on "create repository", "write repository", "add repository", "new repository". |
| `services` | [`services/`](services/) | Rules for services on both sides of the stack: one service per capability instead of one per screen or handler, the caller never speaks the transport (no `axios` in a component, no `requests` or provider SDK in a handler), models in and models out — the frontend service returns the UI model and never the raw API shape, conversion happens in a single pure `mapXxx(raw)` mapper that absorbs `snake_case`, missing fields and string prices and computes derived values like `formattedPrice` once, collaborators are abstractions injected through the constructor (`FileAnalyzer` as an `ABC`, each analyzer receiving an already-built SDK client), a service that handles several cases stays open-closed by looking each one up in an injected registry keyed on the input instead of branching (`FileAnalyzerService` maps `application/pdf` → OpenAI, `image/png` → Gemini, `text/plain` → Claude), the result shape belongs to the service rather than the provider so swapping one is a single line, no state or presentation logic inside the service, and errors propagate instead of being swallowed into `null`. Includes a `template.ts` (frontend) and a `template.py` (backend) starter file. Triggers on "create service", "write service", "add service", "new service". |
| `hooks` | [`hooks/`](hooks/) | Rules for the hook that owns a screen's state: every `useState`, `useEffect` and ref lives here instead of in the component, the hook returns a named object (`{ products, isLoading, error, refresh }`) and never a tuple so adding a key can't break a caller, data plus loading plus error are always exposed so the UI can tell "loading" from "empty" from "the request died", the hook calls a service from the `services` skill and never `axios`/`fetch`/a URL, the `try`/`catch` that turns a rejection into `error` state lives here and only here, handlers like `removeProduct` are returned by the hook rather than written inside JSX, returned functions are wrapped in `useCallback` so children don't re-render and effects don't loop, a context is added only when siblings share the state — the provider calls the very same hook and republishes its value unchanged (`type ProductsContextValue = ReturnType<typeof useProducts>`) — and `useXxxContext` throws a named error when used outside its provider. Includes a `template.tsx` starter file. Triggers on "create hook", "write hook", "add hook", "new hook", "create context". |
| `components` | [`components/`](components/) | Rules for React components that only render: the body is one hook call and a `return` — no `useState`, no `useEffect`, no `fetch`, no `try`/`catch` — everything the component needs is destructured from a single `useXxx()` at the top, so swapping `useProducts()` for `useProductsContext()` is a one-line change, loading and error are early returns instead of ternaries wrapping the whole tree, no `.filter()`/`.sort()`/`toFixed` between the braces (`{product.formattedPrice}` was computed once by the mapper), handlers are references (`onClick={removeProduct}`) rather than multi-statement arrows, a presentational leaf like `ProductCard` takes props and calls no hook so it stays reusable and testable, props are typed with an exported interface on an arrow `const` (never `React.FC`, never `any`) with the callback parameter annotated too (`products.map((product: IProduct) => …)`), and `key` is a stable id rather than the array index. Includes a `template.tsx` starter file. Triggers on "create component", "write component", "add component", "new component". |
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
