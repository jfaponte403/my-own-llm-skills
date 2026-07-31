# My own LLM skills

A small collection of [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) that I use in my daily work.

They are meant to be used together: `models` defines the entities, `repository` stores and returns those models, `tests` verifies the endpoints built on top of them.

## Skills

| Skill | Folder | What it does |
|-------|--------|--------------|
| `models` | [`models/`](models/) | Rules for Pydantic v2 models: one model per role (`CreateXxxRequest` / `UpdateXxxRequest` for input, `XxxModel` as the DB source of truth, `XxxResponse` for output), never return the DB model directly, exclude secrets at the type level instead of stripping them per endpoint, store `password_hash` and accept `password` only on create, prefer rich types (`EmailStr`, constrained `Field`) over primitives, all-optional update requests, and `str, Enum` for fixed value sets. Includes a `template.py` starter file. Triggers on "create model", "write model", "add model", "new model". |
| `repository` | [`repository/`](repository/) | Rules for the data access layer: never touch the database directly — everything goes through a `StorageAdapter` so persistence (DynamoDB, SQL, in-memory) can be swapped, always return a model instead of a raw dict, parametrize `BaseRepository[T]` with the entity's DB model from the `models` skill, one repository per entity with shared CRUD in the base, consistent method names (`create`, `get`, `update`, `delete`, `list`), and adapter injected through the constructor. Includes a `template.py` starter file and a `reference.md` cheat sheet. Triggers on "create repository", "write repository", "add repository", "new repository". |
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
