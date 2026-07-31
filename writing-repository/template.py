"""Starting structure for a repository.

Everything here would normally live in separate modules:
    models.py       -> Customer
    exceptions.py   -> RepositoryError
    repository.py   -> CustomerRepository (the contract)
    dynamo_repository.py -> DynamoCustomerRepository (the implementation)

It is kept in one file so the whole shape is visible at once.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from botocore.exceptions import ClientError


# --- models.py -------------------------------------------------------------
# Pure data. It knows nothing about DynamoDB, SQL or HTTP.

@dataclass
class Customer:
    customer_id: str
    name: str
    email: str
    source: str = "default"


# --- exceptions.py ---------------------------------------------------------
# The caller handles these. It must never need to import botocore.

class RepositoryError(Exception):
    """Something went wrong talking to the data source."""


# --- repository.py ---------------------------------------------------------
# The contract. Handlers and services depend on THIS, not on the implementation.
# Method names are domain language: no query, scan, execute, put_item.

class CustomerRepository(ABC):
    @abstractmethod
    def get_by_id(self, customer_id: str) -> Customer | None:
        """Return the customer, or None if it does not exist."""

    @abstractmethod
    def save(self, customer: Customer) -> None:
        """Create or replace the customer."""

    @abstractmethod
    def list_all(self) -> list[Customer]:
        """Return every customer."""

    @abstractmethod
    def delete(self, customer_id: str) -> None:
        """Remove the customer. Deleting a missing customer is not an error."""


# --- dynamo_repository.py --------------------------------------------------

class DynamoCustomerRepository(CustomerRepository):
    # The table is injected, never created here. That is what lets the tests
    # pass a moto-backed table instead of the real one.
    def __init__(self, table):
        self._table = table

    def get_by_id(self, customer_id: str) -> Customer | None:
        try:
            response = self._table.get_item(Key=self._key(customer_id))
        except ClientError as error:
            raise RepositoryError(f"could not read customer {customer_id}") from error

        item = response.get("Item")
        return self._to_domain(item) if item else None

    def save(self, customer: Customer) -> None:
        try:
            self._table.put_item(Item=self._to_item(customer))
        except ClientError as error:
            raise RepositoryError(f"could not save customer {customer.customer_id}") from error

    def list_all(self) -> list[Customer]:
        try:
            response = self._table.scan()
        except ClientError as error:
            raise RepositoryError("could not list customers") from error

        return [self._to_domain(item) for item in response.get("Items", [])]

    def delete(self, customer_id: str) -> None:
        try:
            self._table.delete_item(Key=self._key(customer_id))
        except ClientError as error:
            raise RepositoryError(f"could not delete customer {customer_id}") from error

    # --- mapping: the only place that knows the stored shape ---------------

    @staticmethod
    def _key(customer_id: str) -> dict:
        return {"PK": f"CUSTOMER#{customer_id}", "SK": "PROFILE"}

    @staticmethod
    def _to_domain(item: dict) -> Customer:
        return Customer(
            customer_id=item["PK"].split("#")[1],
            name=item["name"],
            email=item["email"],
            # Old rows have no source attribute: normalized to "default".
            source=item.get("source", "default"),
        )

    @staticmethod
    def _to_item(customer: Customer) -> dict:
        return {
            "PK": f"CUSTOMER#{customer.customer_id}",
            "SK": "PROFILE",
            "name": customer.name,
            "email": customer.email,
            "source": customer.source,
        }


# --- how the handler uses it ----------------------------------------------
# The handler never imports boto3 and never sees an item.
#
# import boto3, json
# from dataclasses import asdict
#
# repository = DynamoCustomerRepository(boto3.resource("dynamodb").Table("customers"))
#
# def lambda_handler(event, context):
#     customer = repository.get_by_id(event["pathParameters"]["customer_id"])
#     if customer is None:
#         return {"statusCode": 404, "body": json.dumps({"message": "not found"})}
#     return {
#         "statusCode": 200,
#         "body": json.dumps({"message": "success", "data": asdict(customer)}),
#     }
