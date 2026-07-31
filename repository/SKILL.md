---
name: repository
description: >
  Write repository classes that encapsulate data access and abstract
  persistence (SQL, DynamoDB, NoSQL, in-memory) behind a storage adapter,
  keeping business logic separate from storage. Use when the user asks to
  "create repository", "write repository", "add repository", or
  "new repository".
---

# Writing a repository

Follow these rules whenever you create a repository, using `template.py` as the base.

## Rules

1. **Never touch the database directly.** All persistence goes through a `StorageAdapter`. Repositories know nothing about DynamoDB, SQL, or HTTP clients.
2. **Always return a model, never a raw dict.** The adapter speaks dicts; the repository converts them with `Model.model_validate(...)` at the boundary. `get`/`update` return `Model | None`, `list` returns `list[Model]`.
3. **Type your repositories.** Parametrize `BaseRepository[T]` with the entity's DB model from the `models` skill (e.g. `BaseRepository[CustomerModel]`) and pass that class to the constructor so the base can build it.
4. **One repository per aggregate/entity.** Each concrete repository only sets its `table` name and adds entity-specific queries.
5. **Put shared CRUD in `BaseRepository`.** Only add methods to a concrete repository when the query is specific to that entity (e.g. `get_by_email`).
6. **Keep method names consistent:** `create`, `get`, `update`, `delete`, `list`.
7. **Inject the adapter** through the constructor. Never instantiate it inside the repository.

## File layout

```
repository/
  base_repository.py      # BaseRepository + StorageAdapter interface
  user_repository.py
  customer_repository.py
  order_repository.py
```