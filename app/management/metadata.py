from enum import IntFlag, auto
import inspect
from typing import Annotated, Any, Callable, TypeVar, get_origin

class MetadataFlags(IntFlag):
    NONE = 0
    WRITABLE = auto()
    SETTINGS = auto()
    REPLACEMENT = auto()

T = TypeVar('T')

# TODO some general clean up with metadata code 
class ValueMetadata:
    TYPE_MAP: dict[type, str] = {
        str: "string",
        int: "int",
        float: "float",
        dict: "object",
        bool: "bool",
    }

    def __init__(self, flags: MetadataFlags, transform: Callable = None, section = None, name = None, friendly_name = None, type: str = None):
        self.flags = flags
        self.transform = transform
        self.section = section
        self.name = name
        self.friendly_name = friendly_name
        self.type = type

    def get_value(self, value):
        if callable(self.transform):
            value = self.transform(value)
        return value
    
    def get_type(self, override: str):
        """returns self.type, or uses override to either get from the map or if its a string just use that"""
        # TODO should unknown types throw an error?
        return self.type or (ValueMetadata.TYPE_MAP.get(override, "unknown") if isinstance(override, type) else override)
    
    def as_dict(self, value, value_type = None, transform = True):
        if value_type is None:
            value_type = type(value)
        return {
            "type": self.get_type(value_type),
            "value": self.get_value(value) if transform else value,
            "flags": self.flags,
            "name": self.friendly_name,
        }

    @staticmethod
    def is_metadata(annotation):
        return get_origin(annotation) is Annotated and type(annotation.__metadata__[0]) is ValueMetadata
    
    @staticmethod
    def iter_metadatas(obj: object, get_values = True, include_duplicates = False, filter = None):
        # TODO how should conflicting 
        found_fields = {}

        for cls in obj.__class__.__mro__:
            if not hasattr(cls, "__annotations__"):
                continue

            for var_name, annotation in inspect.get_annotations(cls).items():
                if not ValueMetadata.is_metadata(annotation):
                    continue
                metadata: ValueMetadata = annotation.__metadata__[0]
                if filter and not filter(metadata):
                    continue
                value = metadata.get_value(getattr(obj, var_name)) if get_values else None
                if (not include_duplicates) and var_name in found_fields:
                    continue
                found_fields[var_name] = cls
                yield var_name, value, metadata, cls

            for method_name, method in cls.__dict__.items():
                if not callable(method):
                    continue
                annotations = inspect.get_annotations(method)
                if 'return' not in annotations or not ValueMetadata.is_metadata(annotation):
                    continue
                annotation = annotations['return']
                metadata: ValueMetadata = annotation.__metadata__[0]
                if filter and not filter(metadata):
                    continue
                if method_name.startswith("get_"):
                    method_name = method_name[4:]
                if (not include_duplicates) and method_name in found_fields:
                    continue
                found_fields[method_name] = cls
                value = metadata.get_value(method(obj)) if get_values else None
                yield method_name, value, metadata, cls



Setting = Annotated[T, ValueMetadata(MetadataFlags.SETTINGS | MetadataFlags.WRITABLE)]
