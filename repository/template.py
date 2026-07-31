from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any

T = TypeVar("T")


# --- repository/base_repository.py ---
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
    def __init__(self, adapter: StorageAdapter, table: str) -> None:
        self.adapter = adapter
        self.table = table

    def create(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return self.adapter.insert(self.table, item)

    def get(self, id_: str) -> Optional[Dict[str, Any]]:
        return self.adapter.get(self.table, id_)

    def update(self, id_: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.adapter.update(self.table, id_, data)

    def delete(self, id_: str) -> bool:
        return self.adapter.delete(self.table, id_)

    def list(self) -> List[Dict[str, Any]]:
        return self.adapter.list(self.table)


# --- repository/user_repository.py ---
class UserRepository(BaseRepository[Dict[str, Any]]):
    def __init__(self, adapter: StorageAdapter) -> None:
        super().__init__(adapter, table="users")


# --- repository/customer_repository.py ---
class CustomerRepository(BaseRepository[Dict[str, Any]]):
    def __init__(self, adapter: StorageAdapter) -> None:
        super().__init__(adapter, table="customers")


# --- repository/order_repository.py ---
class OrderRepository(BaseRepository[Dict[str, Any]]):
    def __init__(self, adapter: StorageAdapter) -> None:
        super().__init__(adapter, table="orders")