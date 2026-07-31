# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is **not an application** — it is the source of truth for Jhonattan's personal [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills). Every top-level folder (`models/`, `repository/`, `services/`, `http/`, `lambdas/`, `tests/`, `hooks/`, `components/`) is one skill, meant to be copied or symlinked into `~/.claude/skills/` (global) or `.claude/skills/` (per project).

Two consequences that shape every change here:

- **The template files are documentation, not a library.** `template.py` (and `template.ts` in `services/`) is a starter file an LLM will copy into a real project. No packaging, no `__init__.py`, and no imports between skill folders — where a template needs another skill's code it either restates the minimum inline (`repository/template.py` redeclares slim models) or imports the path the *consumer project* will have (`lambdas/template.py` imports `core.http_validator`, `services/template.ts` imports `./apiClient`, `components/template.tsx` imports `@/hooks/useProducts`). Illustrative entities (`Customer`, `Product`) exist to show the *pattern* — a consumer replaces the fields.
- **The skills are designed to compose.** `models` defines the entities → `repository` stores and returns those models → `services` does the work on top of them → `http` validates input at the boundary and shapes every response → `lambdas` wires one endpoint on top of all three → `tests` verifies the resulting endpoints. `services` also extends past the backend: its frontend half consumes the very API `lambdas` exposes, and on that side the chain continues → `hooks` owns the state, the effects and the exception handling of a screen → `components` render what the hook returns and nothing else. When editing one skill, check whether the change breaks the seam with the others (e.g. renaming `XxxModel` in `models/template.py` means `repository/template.py` and its `BaseRepository[T]` docs go stale; renaming anything in `http/template.py` breaks the import block at the top of `lambdas/template.py`).

## Skill anatomy

Each skill folder follows the same three-file shape. Match it exactly when adding a new skill:

| File | Required | Contents |
|------|----------|----------|
| `SKILL.md` | yes | YAML frontmatter (`name`, `description`) + `# <Doing the thing>` + `## Rules` + `## File layout` |
| `template.py` | yes | One flattened, runnable file showing the whole pattern. A skill that spans two languages ships one template per language instead (`services/` has `template.ts` + `template.py`), each showing the same pattern in its own idiom |
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

Either banner style is fine (`---` in `models`/`repository`, `═` in `lambdas`); be consistent *within* a file. The same applies outside Python — `services/template.ts` uses the `═` banner in `//` comments. The banner path must match the `## File layout` block in that skill's `SKILL.md`.

## Verifying a change

There is no build, no lint config, and no test suite for this repo — the templates themselves are the artifact. Verification is: **the template must import cleanly under real Pydantic.**

```powershell
pip install -r requirements.txt          # pydantic + the SDKs services/template.py calls
pip install "pydantic[email]"            # needed for EmailStr in models/ and repository/

# Import a template to check it (from the repo root)
python -c "import importlib.util,sys; s=importlib.util.spec_from_file_location('t','models/template.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print('OK')"
```

Do this after any edit to a `template.py`. `models/template.py` and `repository/template.py` fail without `email-validator`; that is an environment gap, not a template bug.

**`lambdas/template.py` is the one exception — it does not import standalone, by design.** It imports `core.context`, `core.http_validator` and `models.responses.http_response`, which exist in the consumer's project (they come from the `http` skill), not here. Check it with a syntax pass instead:

```powershell
python -m py_compile lambdas/template.py
```

Keep forward references in mind when reordering banner sections. `http/template.py` deliberately declares `models/responses/http_response.py` *before* `core/exceptions.py`, because `HttpError` annotates `ResponseStatus`. In the other order the file only imports on Python 3.14 (via PEP 649 lazy annotations) and raises `NameError` on older interpreters — the `venv/` here is 3.14, so that regression would pass locally and break for a consumer.

## Coding style the templates must teach

The templates exist to make an LLM write code the way Jhonattan writes it. Reproduce these in every template, and apply them when writing Python anywhere in this repo:

- **Modern type syntax only.** `str | None`, `list[T]`, `dict[str, Any]`, `type[T]` — never `Optional[...]`, `List[...]`, `Dict[...]`. Annotate everything, including `-> None` on `__init__`.
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

Prefer splitting a skill over letting its `template.py` grow. A template that mixes write-once infrastructure with the pattern a consumer repeats every time is really two skills: that is why the Lambda + API Gateway pattern is `http` (the boundary — `http_validator`, `RequestContext`, `HttpError`, `HttpResponse`) plus `lambdas` (one endpoint on top of it). Roughly, if a section would be copied once per *project* rather than once per *entity or endpoint*, it belongs in its own skill.

`repository/reference.md` is an empty stub, but the `repository` row in `README.md` already advertises a `reference.md` cheat sheet — either fill it or drop the claim.
