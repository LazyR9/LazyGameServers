from abc import ABC, abstractmethod
from enum import auto, Enum
from typing import Any, Callable, Generic, TYPE_CHECKING, Iterable, TypeVar

from .validators import ValidationError, Validator

T = TypeVar('T')

# TODO better name
class InputRequest(Generic[T]):
    def __init__(self, message: str, type: Callable[[Any], T], validators: Iterable[Callable[[Any], None]] | None = None):
        self.message = message
        self.type = type
        self.validators = validators
        
        self.result = None
        self.retry: ValidationError | None = None
    
    def fulfill(self, response):
        self.result = response
    
    def get_validation_data(self):
        validation_data = {}
        if self.validators is not None:
            for validator in self.validators:
                if isinstance(validator, Validator):
                    validation_data.update(validator.validation_data())
        return validation_data

class InputType(Enum):
    STRING = auto()
    NUMBER = auto()
    BOOL = auto()

class Input(ABC):
    input_type: InputType
    
    @abstractmethod
    def parse(self, input) -> Any: ...
    
    def __call__(self, input):
        return self.parse(input)

class NativeTypeInput(Input, Generic[T]):
    type: type[T]
    input_type = InputType.STRING
    
    def parse(self, input) -> T:
        if not isinstance(input, self.type):
            raise ValidationError(f"Input must be of type \"{self.type.__name__}\"")
        return input
    
    if TYPE_CHECKING:
        def __call__(self, input) -> T: ...
    
class CustomTypeInput(NativeTypeInput):
    def __init__(self, type: type[T]):
        self.type = type
    
class StringInput(NativeTypeInput[str]):
    input_type = InputType.STRING
    type = str

class BoolInput(NativeTypeInput[bool]):
    input_type = InputType.BOOL
    type = bool

class IntInput(NativeTypeInput[int]):
    input_type = InputType.NUMBER
    type = int

class FloatInput(NativeTypeInput[float]):
    input_type = InputType.NUMBER
    type = float

__all__ = ["InputRequest", "InputType", "NativeTypeInput", "CustomTypeInput", "StringInput", "BoolInput", "IntInput", "FloatInput"]