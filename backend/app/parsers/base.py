from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseParser(ABC):
    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url

    @abstractmethod
    async def parse(self) -> List[Dict[str, Any]]:
        """
        Scrapes/requests tenders from the platform.
        Returns a list of dictionaries, where keys correspond to Tender model attributes:
        [
            {
                "title": str,
                "description": str,
                "price_current": float,
                "price_start": float,
                "source_platform": str,
                "url": str,
                "region": str,
                "machinery_type": str,
                "date_end": datetime
            },
            ...
        ]
        """
        pass
