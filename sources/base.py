from abc import ABC, abstractmethod


class ListingParser(ABC):
    @abstractmethod
    def can_handle(self, text: str, html: str | None = None, file_name: str | None = None) -> bool:
        pass

    @abstractmethod
    def extract_fields(self, text: str, html: str | None = None, file_name: str | None = None) -> dict:
        pass