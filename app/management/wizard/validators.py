from abc import ABC, abstractmethod
from typing import Any
import re

class ValidationError(Exception):
    pass

class Validator(ABC):
    @abstractmethod
    def validate(self, input): ...
    
    def __call__(self, input):
        return self.validate(input)
    
    @abstractmethod
    def validation_data(self) -> dict[str, Any]:
        """
        Returns extra JSON data to be sent to frontend.
        
        Useful for basic validation that can be done on the frontend, like regex or number ranges.
        """
    
class LengthValidator(Validator):
    def __init__(self, min, max) -> None:
        self.min = min
        self.max = max
    
    def validate(self, input):
        if len(input) < self.min or len(input) > self.max:
            raise ValidationError
        
class RangeValidator(Validator):
    def __init__(self, min, max) -> None:
        self.min = min
        self.max = max
    
    def validate(self, input):
        if input < self.min or input > self.max:
            raise ValidationError
        
    def validation_data(self) -> dict[str, Any]:
        return {"min": self.min, "max": self.max}
    
class StepValidator(Validator):
    def __init__(self, step, offset = 0):
        self.step = step
        self.offset = offset
        
    def validate(self, input):
        if (input - self.offset) % self.step:
            raise ValidationError("Invalid step!")
        
    def validation_data(self) -> dict[str, Any]:
        return {"step": self.step}
        
class SingleChoiceValidator(Validator):
    def __init__(self, choices):
        self.choices = choices
        
    def validate(self, input):
        if input not in self.choices:
            raise ValidationError(f"Input {input} was not one of {self.choices}!")
        
    def validation_data(self) -> dict[str, Any]:
        return {"choices": self.choices}
        
class RegexValidator(Validator):
    def __init__(self, regex: str):
        self.regex = re.compile(regex)
        
    def validate(self, input: str):
        if not self.regex.match(input):
            raise ValidationError(f"Input {input} did not match pattern {self.regex.pattern}!")
        
    def validation_data(self) -> dict[str, Any]:
        return {"regex": self.regex.pattern}

__all__ = ["Validator", "ValidationError", "LengthValidator", "RangeValidator", "StepValidator", "SingleChoiceValidator", "RegexValidator"]