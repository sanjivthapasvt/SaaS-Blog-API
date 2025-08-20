from typing import Any, Type, TypeVar

from pydantic import BaseModel, TypeAdapter, ValidationError

T = TypeVar("T", bound=BaseModel)


def validate_response(data: Any, schema: Type[T]) -> T:
    """
    Validate response against the given Pydantic schema.
    Collects all validation errors if present.
    """
    adapter = TypeAdapter(schema)
    try:
        return adapter.validate_python(data)
    except ValidationError as e:
        # Re-raise with all collected issues for pytest readability
        raise AssertionError(
            f"Response validation failed for {schema.__name__}:\n{e.errors()}"
        ) from e
