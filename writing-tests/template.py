import json
import unittest

# Import the real lambda_handler from your source module
# from src.handlers.my_endpoint import lambda_handler

def lamda_handler(event, context):
    return {}

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # Set up all infra and mocks here. Do NOT use MagicMock.
        # Use real mockers instead:
        #   - responses / respx  -> for external HTTP calls
        #   - moto / boto stubs   -> for AWS services (DynamoDB, S3, SQS, etc.)
        #   - sqlite (in-memory)  -> for SQL databases
        # Register the mocked resources/endpoints here so every test starts clean.
        pass

class TestPostEndpoint(BaseTestCase):
    def test_post_endpoint(self):

        # The payload must be clearly visible so anyone reading the test
        # knows exactly what is being sent to the endpoint.
        payload = {
            "custom": "some"
        }

        event = {
            "body": json.dumps(payload)
        }

        response = lamda_handler(event=event, context=None)

        # Build the full expected response and assert it once.
        # Only validate the body and the status code.
        status, body = response["statusCode"], json.loads(response["body"])

        expected = {
            "message": "ok"
        }

        self.assertEqual(status, 200)
        self.assertEqual(body, expected)