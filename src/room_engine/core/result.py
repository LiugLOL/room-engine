from dataclasses import dataclass
from typing import Generic, TypeAlias, TypeVar
from room_engine.core.error_types import ErrorType

T = TypeVar("T")


@dataclass(frozen=True)
class InternalError:
    """Describe an expected domain failure.

    Args:
        code: Machine-readable category of the failure.
        message: Human-readable explanation of the failure.
        details: Optional contextual values that help callers diagnose it.
    """

    code: ErrorType
    message: str
    details: dict[str, object] | None = None

@dataclass(frozen=True)
class Success(Generic[T]):
    """Wrap the value produced by a successful domain operation.

    Args:
        value: Result value returned by the operation.
    """

    value: T

@dataclass(frozen=True)
class Failure:
    """Wrap an expected domain error returned by an operation.

    Args:
        error: Error describing why the requested operation could not finish.
    """

    error: InternalError

Result: TypeAlias = Success[T] | Failure
