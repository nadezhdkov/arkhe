from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ApplicationStartedEvent:
    """Published after all beans are initialized and the scheduler has started."""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ApplicationReadyEvent:
    """Published when the application is fully ready to serve requests."""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ApplicationStoppingEvent:
    """Published when the application begins its graceful shutdown."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
