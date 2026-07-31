# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is **not an application** — it is the source of truth for Jhonattan's personal [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills). Every top-level folder (`models/`, `repository/`, `tests/`, `lambdas/`) is one skill, meant to be copied or symlinked into `~/.claude/skills/` (global) or `.claude/skills/` (per project).

Two consequences that shape every change here:

- **The Python files are documentation, not a library.** `template.py` is a starter file an LLM will copy into a real project. It has no imports across folders, no packaging, no `__init__.py`. Illustrative entities (`Customer`, `Product`) exist to show the *pattern* — a consumer replaces the fields.
- **The skills are designed to compose.** `models` defines the entities → `repository` stores and returns those models → `lambdas` validates input with those models and returns them → `tests` verifies the resulting endpoints. When editing one skill, check whether the change breaks the seam with the others (e.g. renaming `XxxModel` in `models/template.py` means `repository/template.py` and its `BaseRepository[T]` docs go stale).

## Skill anatomy

Each skill folder follows the same three-file shape. Match it exactly when adding a new skill:

| File | Required | Contents |
|------|----------|----------|
| `SKILL.md` | yes | YAML frontmatter (`name`, `description`) + `# <Doing the thing>` + `## Rules` + `## File layout` |
| `template.py` | yes | One flattened, runnable file showing the whole pattern |
| `reference.md` | optional | Cheat sheet: library table, ❌ what-not-to-do list, links |

**Frontmatter conventions:**
- `name` is the lowercase folder name (`tests/SKILL.md` currently has `name: Tests` — inconsistent; new skills use lowercase).
- `description` is a folded block (`>`) that states what the skill produces, then closes with the literal trigger phrases: `Use when the user asks to "create model", "write model", ...`. Those phrases are what makes the skill fire, so they are part of the contract — don't paraphrase them away.

**Rules sections** are a numbered list where each item leads with a **bold imperative** and then explains it in one or two sentences. Rules are prohibitions and defaults, not tutorials. Keep them to ~7–9; if a rule needs a long example it belongs in `reference.md` or as a `## Counter-example` section with a ❌ bad / ✅ good pair (see `tests/SKILL.md`).

**Templates are one file that pretends to be many.** Since a skill can't ship a whole package, each `template.py` concatenates what would be several real files and marks the boundaries with a comment banner naming the destination path:

```python
# --- repository/base_repository.py ---
```
```python
# ═════════════════════════════════════════════════════════════
# core/http_validator.py
# ═════════════════════════════════════════════════════════════
```

Either banner style is fine (`---` in `models`/`repository`, `═` in `lambdas`); be consistent *within* a file. The banner path must match the `## File layout` block in that skill's `SKILL.md`.

## Verifying a change

There is no build, no lint config, and no test suite for this repo — the templates themselves are the artifact. Verification is: **the template must import cleanly under real Pydantic.**

```powershell
pip install -r requirements.txt          # pydantic only
pip install "pydantic[email]"            # needed for EmailStr in models/ and repository/

# Import a template to check it (from the repo root)
python -c "import importlib.util,sys; s=importlib.util.spec_from_file_location('t','models/template.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print('OK')"
```

Do this after any edit to a `template.py`. `models/template.py` and `repository/template.py` fail without `email-validator`; that is an environment gap, not a template bug.

The `venv/` in this repo is Python 3.14. `lambdas/template.py` relies on PEP 649 lazy annotations (`HttpError` is annotated with `ResponseStatus`, which is defined further down the file) — it imports on 3.14 but would raise `NameError` on older interpreters. Keep forward references in mind when reordering banner sections.

## Coding style the templates must teach

The templates exist to make an LLM write code the way Jhonattan writes it. Reproduce these in every template, and apply them when writing Python anywhere in this repo:

- **Modern type syntax only.** `str | None`, `list[T]`, `dict[str, Any]`, `type[T]` — never `Optional[...]`, `List[...]`, `Dict[...]`. (`lambdas/template.py` still uses `Optional`; that is legacy, not the target.) Annotate everything, including `-> None` on `__init__`.
- **Pydantic v2 API.** `model_validate`, `model_dump`, `model_dump_json`, `model_config = ConfigDict(...)`. Never v1 (`parse_obj`, `.dict()`, inner `class Config`).
- **Rich types over primitives.** `EmailStr` over `str`; `Field(gt=0, min_length=1)` over a bare annotation.
- **`str, Enum` for fixed value sets** — stays JSON-serializable and readable in the DB.
- **One type per role.** Separate request / DB / response models; secrets are excluded structurally (absent from the response type) rather than stripped at runtime.
- **Depend on abstractions, inject them.** `StorageAdapter` is an `ABC`; the concrete adapter arrives through the constructor and is never instantiated inside the class that uses it.
- **Convert at the boundary.** Adapters speak `dict`; the layer above returns models. No raw dicts leak upward.
- **Comments explain intent, not mechanics.** Short, above the line, English. `# Response: body returned to the client (no secrets)`, `# ownership stamped from the token`. No docstrings on obvious functions; a docstring on a decorator factory that documents its knobs is fine (see `http_validator`).
- **Everything in English** — code, comments, `SKILL.md`, commit messages.

## Adding a new skill

1. Create the folder, `SKILL.md`, and `template.py` following the anatomy above.
2. Add a row to the table in `README.md`. That table's cell is a dense one-paragraph summary of the skill's rules plus its trigger phrases — it is the repo's index, so a new skill isn't done until it is listed there.
3. If the skill touches Pydantic, verify the template imports (above).

`lambdas/` is currently a work in progress: it has a `template.py` (a Lambda + API Gateway pattern — `http_validator` decorator, `RequestContext`, `HttpError` hierarchy, `HttpResponse.to_lambda`) but no `SKILL.md` and no `README.md` row yet.
