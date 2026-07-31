# References

Quick reference for writing repositories in this project. Read this together with `SKILL.md`.

## Naming: domain method vs storage call

| Say this (repository method) | Not this | Where the storage word belongs |
|------------------------------|----------|--------------------------------|
| `get_by_id(customer_id)` | `get_item(key)` | inside the implementation |
| `list_by_customer(customer_id)` | `query(index, condition)` | inside the implementation |
| `save(customer)` | `put_item(item)` / `INSERT INTO` | inside the implementation |
| `delete(customer_id)` | `delete_item(key)` | inside the implementation |
| `exists(email)` | `count(*) > 0` | inside the implementation |

## What each layer is allowed to know

| Layer | Knows about | Never touches |
|-------|-------------|---------------|
| Handler | `event`, `statusCode`, domain models | tables, keys, SQL, `boto3` |
| Service / use case | domain models, repository contract | tables, keys, SQL, `boto3` |
| Repository | tables, keys, SQL, HTTP clients | `statusCode`, `event`, business rules |
| Model | its own fields | everything else |

## What NOT to do

- ❌ **Do not import `boto3`, `sqlalchemy` or `requests` outside the repository.** If a handler
  imports them, the repository is missing or incomplete.
- ❌ **Do not return raw items, rows or ORM objects.** Map them to a domain model first.
- ❌ **Do not put business rules in the repository** (discounts, permissions, validation). It
  stores and retrieves — nothing else.
- ❌ **Do not build HTTP responses inside it.** No `statusCode`, no `json.dumps` for the API.
- ❌ **Do not leak `ClientError` / `sqlite3.Error`.** Translate them into `RepositoryError` or a
  more specific domain exception.
- ❌ **Do not create the client inside the repository** (no module-level `boto3.resource(...)`
  used from within). Inject it in `__init__`.
- ❌ **Do not mix entities.** One repository per aggregate.
- ❌ **Do not mix "not found" styles.** Either return `None` everywhere or raise everywhere.

## Testing it

Follows the `write-tests` skill: because the client is injected, the tests build the repository
with a real local backend — never with `MagicMock`.

| Implementation | Test backend |
|----------------|--------------|
| DynamoDB / S3 / SQS | `moto` (or `botocore` Stubber) |
| SQL | in-memory `sqlite3` |
| External HTTP API | `responses` / `respx` |

```python
@mock_aws
class TestDynamoCustomerRepository(unittest.TestCase):
    def setUp(self):
        table = boto3.resource("dynamodb", region_name="us-east-1").create_table(...)
        self.repository = DynamoCustomerRepository(table)
```

Test the repository through its public methods (`save` then `get_by_id`), not by inspecting the
stored item.

## Links

- Repository pattern (Fowler) → https://martinfowler.com/eaaCatalog/repository.html
- Architecture Patterns with Python, ch. 2 → https://www.cosmicpython.com/book/chapter_02_repository.html
- `abc` module → https://docs.python.org/3/library/abc.html
- `dataclasses` → https://docs.python.org/3/library/dataclasses.html
- moto → https://docs.getmoto.org/
