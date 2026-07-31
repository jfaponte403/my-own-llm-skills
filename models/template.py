from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- models/customer.py ---

class CustomerStatus(str, Enum):
    MISSING_INFO = "missing_info"
    NO_PLAN = "no_plan"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# Request: body of POST /customers
class CreateCustomerRequest(BaseModel):
    name: str = Field(min_length=1)
    age: int = Field(gt=0, lt=150)
    email: EmailStr
    password: str = Field(min_length=8)
    status: CustomerStatus = CustomerStatus.MISSING_INFO  # default on creation


# Request: body of PATCH /customers/{id} (all optional)
class UpdateCustomerRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    age: int | None = Field(default=None, gt=0, lt=150)
    email: EmailStr | None = None
    status: CustomerStatus | None = None


# Source of truth: what lives in the DB
class CustomerModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    age: int
    email: EmailStr
    password_hash: str
    status: CustomerStatus


# Response: body returned to the client (no secrets)
class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    age: int
    email: EmailStr
    status: CustomerStatus