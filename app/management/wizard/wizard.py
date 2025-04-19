from abc import ABC, abstractmethod
from fastapi import WebSocket
from typing import Any, Callable, Collection, Iterable, TypeVar

from .validators import ValidationError
from .inputs import InputRequest, InputType, Input

T = TypeVar('T')

class Wizard(ABC):
    def __init__(self):
        self.finished = False
    
    async def input(self, message: str, type: Callable[[Any], T], validators: Iterable[Callable[[Any], None]] | None = None) -> T:
        """
        Asks the user for input, and waits for a response.
        If the response is invalid, it will ask the user again.

        :param message: The message to show.
        :param type: The data type that the response should be.
            This can be any callable that takes in any input and either return the parsed output,
            or raise `ValidationError` if the input is invalid.
        :param validators: Additional callables that determine if the input is valid.
            Unlike `type`, this cannot transform the data - return values are ignored.
        """
        request = InputRequest(message, type, validators)
        
        while True:
            response = await self._get_input(request)
            try:
                value = request.type(response)
                if validators is not None:
                    for validator in validators:
                        validator(value)
            except ValidationError as error:
                request.retry = error
                continue
            break
        return value

    @abstractmethod
    async def _get_input(self, request: InputRequest) -> Any:
        """
        Method that asks the user for input,
        and returns what they said.
        
        No validation or data transforming should be done,
        this function should return the raw value from the user.
        """
    
    @abstractmethod
    async def _get_input_multi(self, requests: Iterable[InputRequest], error: 'ValidationError | None') -> list[Any]:
        """
        Asks user for multiple inputs,
        then returns the answers.
        
        `error` should be passed if this is being called again because of a validation error,
        and that the error was caused by an invalid combination of otherwise validation responses.
        (For example, ensuring that two numbers add up to a third.)
        """
    
    @abstractmethod
    async def message(self, message: str):
        """
        Display a message to the user, without expecting a response.

        :param message: The message to show
        """
    
    async def finish(self, message: str | None = None):
        """
        Display the finish status to the user, and cleanup the object.
        """
        self.finished = True
    
    async def cancel(self, message: str = "Setup cancelled!"):
        """
        Cancels the server creation and cleans up any
        """
        self.cancelled = True
        await self.finish(message)
        raise CancelledError(message, False)
            
    async def input_multiple(self, *requests: InputRequest, validators: Collection[Callable[[list[Any]], None]] | None = None):
        values = []
        retry = True
        validation_error = None
        while retry:
            retry = False
            values.clear()
            responses = await self._get_input_multi(requests, validation_error)
            for request, response in zip(requests, responses):
                try:
                    value = request.type(response)
                    if request.validators:
                        for validator in request.validators:
                            validator(value)
                except ValidationError as error:
                    request.retry = error
                    retry = True
                else:
                    request.fulfill(value)
                    values.append(value)
            try:
                if validators is not None:
                    for validator in validators:
                        validator(values)
            except ValidationError as error:
                retry = True
                validation_error = error
        return values

class CancelledError(Exception):
    def __init__(self, message: str, is_user: bool):
        self.message = message
        self.is_user = is_user

class WebsocketWizard(Wizard):
    def __init__(self, websocket: WebSocket):
        super().__init__()
        self.sock = websocket
        
    @staticmethod
    def _get_request_json(request: InputRequest):
        return {
            "message": request.message,
            "input_type": request.type.input_type.name if isinstance(request.type, Input) else InputType.STRING.name,
            "validation_data": request.get_validation_data()
        }
    
    @staticmethod
    def _validate_type(data: dict[str, Any], type: str):
        if data["type"] == "cancel":
            raise CancelledError("User cancelled!", True)
        if data["type"] != type:
            raise ValidationError("Invalid message type %s" % data["type"])
        
    async def _get_input(self, request: InputRequest):
        
        if not request.retry:
            await self.sock.send_json({"type": "input", **self._get_request_json(request)})
        else:
            await self.sock.send_json({"type": "retry", "message": request.retry.args[0]})
        
        data = await self.sock.receive_json()
        self._validate_type(data, "response")
        response = data["value"]
        
        return response
    
    async def _get_input_multi(self, requests: Iterable[InputRequest], error: ValidationError | None):
        retries = [request.retry for request in requests]
        if not (any(retries) or error is not None):
            await self.sock.send_json({"type": "input_multiple", "inputs": [self._get_request_json(request) for request in requests]})
        else:
            await self.sock.send_json({"type": "retry_multiple", "message": error and error.args[0], "messages": retries})
        
        data = await self.sock.receive_json()
        self._validate_type(data, "response_multiple")
        responses = data["values"]
        
        return responses
    
    async def message(self, message):
        await self.sock.send_json({"type": "message", "message": message})

    async def finish(self, message = None):
        await super().finish(message)
        await self.sock.send_json({"type": "finish", "message": message})
        await self.sock.close()

__all__ = ["Wizard", "WebsocketWizard", "CancelledError"]