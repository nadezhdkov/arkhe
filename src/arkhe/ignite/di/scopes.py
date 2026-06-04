from enum import Enum


class Scope(str, Enum):
    SINGLETON = "singleton"
    PROTOTYPE = "prototype"
