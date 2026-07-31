from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any

from pydantic import BaseModel, ConfigDict, EmailStr


# --- models/ (see the `models` skill) ---
# DB models: source of truth for what each table stores.


class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    password_hash: str


class CustomerModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr


class OrderModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    total: float


# --- repository/base_repository.py ---
# Repositories always return models, never raw dicts.
T = TypeVar("T", bound=BaseModel)


# Storage adapter interface (swap DynamoDB, SQL, in-memory, etc.)
class StorageAdapter(ABC):
    @abstractmethod
    def insert(self, table: str, item: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    def get(self, table: str, id_: str) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def update(self, table: str, id_: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def delete(self, table: str, id_: str) -> bool: ...

    @abstractmethod
    def list(self, table: str) -> List[Dict[str, Any]]: ...


# Generic base repository — shared by all repositories.
class BaseRepository(Generic[T]):
    def __init__(self, adapter: StorageAdapter, table: str, model: type[T]) -> None:
        self.adapter = adapter
        self.table = table
        self.model = model

    def create(self, item: T) -> T:
        return self.model.model_validate(self.adapter.insert(self.table, item.model_dump()))

    def get(self, id_: str) -> Optional[T]:
        raw = self.adapter.get(self.table, id_)
        return self.model.model_validate(raw) if raw else None

    def update(self, id_: str, data: Dict[str, Any]) -> Optional[T]:
        raw = self.adapter.update(self.table, id_, data)
        return self.model.model_validate(raw) if raw else None

    def delete(self, id_: str) -> bool:
        return self.adapter.delete(self.table, id_)

    def list(self) -> List[T]:
        return [self.model.model_validate(raw) for raw in self.adapter.list(self.table)]


# --- repository/user_repository.py ---
class UserRepository(BaseRepository[UserModel]):
    def __init__(self, adapter: StorageAdapter) -> None:
        super().__init__(adapter, table="users", model=UserModel)


# --- repository/customer_repository.py ---
class CustomerRepository(BaseRepository[CustomerModel]):
    def __init__(self, adapter: StorageAdapter) -> None:
        super().__init__(adapter, table="customers", model=CustomerModel)


# --- repository/order_repository.py ---
class OrderRepository(BaseRepository[OrderModel]):
    def __init__(self, adapter: StorageAdapter) -> None:
        super().__init__(adapter, table="orders", model=OrderModel)
