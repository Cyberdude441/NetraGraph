from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
from ..models.entity import Entity
from ..models.relationship import Relationship


class BaseConnector(ABC):
    """Abstract interface for all official Cyber Cell data source connectors."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the law enforcement data feed / gateway."""
        pass

    @abstractmethod
    async def parse_and_extract(
        self, payload: Any
    ) -> Tuple[List[Entity], List[Relationship]]:
        """
        Validate, normalize and extract strongly-typed Entities and Relationships
        from the raw or structured input payload.
        """
        pass
