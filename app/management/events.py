from enum import Enum, auto

class GameServerEventType(Enum):
    # used so that if a plugin or something wants to send an event they don't have to add an extra type
    CUSTOM = 0
    STATUS = auto()
    CONSOLE_LINE = auto()

class GameServerEvent:
    type = GameServerEventType.CUSTOM

    def __init__(self, type: GameServerEventType = None, **extra_data):
        if type is not None:
            self.type = type
        # used to store the current listener being called in the dispatch,
        # so that the handler function can easily access it
        self.listener: GameServerEventListener = None
        self.extra_data = extra_data

    def as_dict(self):
        """
        Returns a dictionary representing this event.
        This dict has two entries:
        * `event`: contains the event type
        * `data`: contains any extra data the event provides.

        :return: The dict representing this event.
        """
        return {"event": self.type, "data": self.data_dict()}
    
    def data_dict(self):
        """
        Gets the "data" part of the dict from `as_dict()`.

        `as_dict()` should be used most of the time because it has a consistent format across all events, see its docstring.

        This is here so subclasses don't have to override `as_dict()` and just change the part of the dict that matters.

        :return: A dict representation of any extra data associated with an event
        """
        return self.extra_data

class ConsoleLineEvent(GameServerEvent):
    type = GameServerEventType.CONSOLE_LINE

    def __init__(self, line: 'GameConsoleLine'):
        super().__init__()
        self.line = line

    def data_dict(self):
        return self.line.as_dict()
    
class StatusEvent(GameServerEvent):
    type = GameServerEventType.STATUS

    def __init__(self, status: 'GameServerStatus'):
        super().__init__()
        self.status = status

    def data_dict(self):
        return {"status": self.status.name}

class GameServerEventListener:
    def __init__(self, func, filter = None):
        self.func = func
        self.filter = filter
        self._registered = True

    def deregister(self):
        self._registered = False

    def call(self, event):
        if self.filter is not None and event.type != self.filter:
            return
        self.func(event)

# mandatory "i hate circular imports" here
from app.management.server import *
