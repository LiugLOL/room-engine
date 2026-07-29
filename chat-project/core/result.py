from dataclasses import dataclass
from typing import Generic, TypeAlias, TypeVar

from network.error_types import ErrorType

T = TypeVar("T")


@dataclass(frozen=True)
class InternalError:
    code: ErrorType
    message: str
    details: dict[str, object] | None = None


@dataclass(frozen=True)
class Success(Generic[T]):
    value: T


@dataclass(frozen=True)
class Failure:
    error: InternalError


Result: TypeAlias = Success[T] | Failure