---
name: Tests
description: >
  This guide will help you write tests correctly. This skill could be actived when ask to "write tests" or "run tests" or "add testings" or when a new code block is created.
---

# How to write tests

Follow these rules whenever you write or add tests. Use `template.py` in this skill folder as the starting structure for every new test file.

## Core rules

1. **Payloads must be clearly visible.** Define the `payload` as a plain dict right inside the test so anyone can see exactly what is sent to the endpoint. Do not hide it in helpers or fixtures.

2. **Only validate the response and the status code.** Assert on the returned `statusCode` and `body`. Do not assert on internal function calls, implementation details, or how the result was produced.

3. **Never use MagicMock.** Do not use `unittest.mock.MagicMock` or `patch` to fake behavior. Use real mockers that simulate the actual dependency:
   - `responses` / `respx` → for external HTTP calls
   - `moto` / `boto` stubs → for AWS services (DynamoDB, S3, SQS, Cognito, etc.)
   - `sqlite` (in-memory) → for SQL databases
   
   Register all mocked resources in `setUp` so every test starts from a clean, known state.

4. **Import the real handler.** Import the actual `lambda_handler` from the source module under test. Do not redefine it inside the test file.

## Structure

- `BaseTestCase(unittest.TestCase)` → holds shared `setUp` with all infra and mocks.
- `Test<Endpoint>(BaseTestCase)` → one class per endpoint, with one method per case (success, missing body, validation error, etc.).

## Example

See `template.py` in this folder for a complete working example that follows all the rules above.

## Checklist before finishing

- [ ] Payload is a visible dict inside the test
- [ ] Only `statusCode` and `body` are asserted
- [ ] No `MagicMock` — real mockers used instead
- [ ] Mocks set up in `setUp`, clean per test
- [ ] Real handler imported from source

## Counter-example: don't assert field by field

❌ **Bad** — many asserts, hard to read, noisy:

```python
def test_returns_200_with_users_and_pagination(self):
    self._add_customer("c1", "Alice", "alice@x.com")

    response = get_customers(event={"requestContext": ADMIN_CONTEXT}, context=None)

    self.assertEqual(response["statusCode"], 200)
    body = json.loads(response["body"])
    self.assertEqual(body["message"], "success")
    users = body["data"]["users"]
    self.assertEqual(len(users), 1)
    self.assertEqual(users[0]["customer_id"], "c1")
    self.assertEqual(users[0]["name"], "Alice")
    self.assertEqual(users[0]["email"], "alice@x.com")
    self.assertTrue(users[0]["has_questionnaires"])
    self.assertFalse(users[0]["has_answers"])
    self.assertEqual(users[0]["source"], "default")
    pagination = body["data"]["pagination"]
    self.assertEqual(pagination["page"], 1)
    self.assertEqual(pagination["page_size"], 20)
    self.assertEqual(pagination["total_items"], 1)
```

✅ **Good** — build the full expected JSON and assert once:

```python
def test_returns_200_with_users_and_pagination(self):
    self._add_customer("c1", "Alice", "alice@x.com")

    response = get_customers(event={"requestContext": ADMIN_CONTEXT}, context=None)

    status, body = response["statusCode"], json.loads(response["body"])

    expected = {
        "message": "success",
        "data": {
            "users": [
                {
                    "customer_id": "c1",
                    "name": "Alice",
                    "email": "alice@x.com",
                    "has_questionnaires": True,
                    "has_answers": False,
                    # Row has no source attribute: normalized to "default".
                    "source": "default",
                }
            ],
            "pagination": {"page": 1, "page_size": 20, "total_items": 1},
        },
    }

    self.assertEqual(status, 200)
    self.assertEqual(body, expected)
```

Build the whole expected response as one dict and compare it in a single `assertEqual`. Less code, easier to read, and the diff shows exactly what changed.