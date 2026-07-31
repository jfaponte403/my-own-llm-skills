# References

Quick reference for writing tests in this project. Read this together with `skill.md`.

## Recommended libraries

| Dependency to fake | Use this | Why |
|--------------------|----------|-----|
| External HTTP calls | `responses` or `respx` | Register real fake responses per URL; `respx` if you use `httpx`, `responses` if you use `requests` |
| AWS services (DynamoDB, S3, SQS, Cognito...) | `moto` (or `botocore` Stubber) | Simulates real AWS behavior without hitting the cloud |
| SQL databases | `sqlite` in-memory | Real engine, real queries, zero setup, resets per test |

Install:

```bash
pip install responses respx moto
# sqlite comes with Python (import sqlite3)
```

## What NOT to do

- ❌ **Do not use `MagicMock` or `unittest.mock.patch`** to fake dependencies. They let any call pass and hide real bugs.
- ❌ **Do not assert on internal calls** (e.g. "was this function called once"). Only assert the response and status code.
- ❌ **Do not hide the payload** inside fixtures or helpers. Keep it a visible dict inside the test.
- ❌ **Do not redefine the handler** inside the test file. Import the real one from source.
- ❌ **Do not hit real services** (real HTTP, real AWS, real DB). Everything must be mocked locally.
- ❌ **Do not share state between tests.** Set up mocks in `setUp` so each test starts clean.

## Links

- responses → https://github.com/getsentry/responses
- respx → https://lundberg.github.io/respx/
- moto → https://docs.getmoto.org/
- botocore Stubber → https://botocore.amazonaws.com/v1/documentation/api/latest/reference/stubber.html
- sqlite3 → https://docs.python.org/3/library/sqlite3.html