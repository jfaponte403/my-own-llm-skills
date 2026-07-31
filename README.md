# My own LLM skills

A small collection of [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) that I use in my daily work.

## Skills

| Skill | Folder | What it does |
|-------|--------|--------------|
| `write-tests` | [`writing-tests/`](writing-tests/) | Rules for writing Python tests: keep the payload a visible dict, assert only `statusCode` and `body` in a single `assertEqual`, never use `MagicMock` (use `responses`/`respx`, `moto`, in-memory `sqlite` instead), and import the real handler. Includes a `template.py` starter file and a `reference.md` cheat sheet. Triggers on "write tests", "run tests", "add testing". |

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

