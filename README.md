# My own LLM skills

A small collection of [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) that I use in my daily work.

## Skills

| Skill | Folder | What it does |
|-------|--------|--------------|
| `write-tests` | [`tests/`](tests/) | Rules for writing Python tests: keep the payload a visible dict, assert only `statusCode` and `body` in a single `assertEqual`, never use `MagicMock` (use `responses`/`respx`, `moto`, in-memory `sqlite` instead), and import the real handler. Includes a `template.py` starter file and a `reference.md` cheat sheet. Triggers on "write tests", "run tests", "add testing". |
| `write-repository` | [`writing-repository/`](writing-repository/) | Rules for writing the data access layer: define the contract as an `ABC` first, keep `boto3`/SQL/`requests` inside the repository only, name methods in domain terms, return domain models with the mapping isolated in `_to_domain`/`_to_item`, translate infrastructure errors into domain exceptions, and inject the client in `__init__`. Includes a `template.py` starter file and a `reference.md` cheat sheet. Triggers on "write a repository", "add a repository", "create the data access layer". |

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

