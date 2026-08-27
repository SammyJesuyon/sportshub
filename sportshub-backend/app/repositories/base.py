from typing import Iterable, TypeVar

from sqlalchemy.orm import Session


Model = TypeVar("Model")


class BaseRepository:
    """Shared persistence operations used by domain-specific repositories."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, entity: Model) -> Model:
        self.session.add(entity)
        return entity

    def add_all(self, entities: Iterable[object]) -> None:
        self.session.add_all(list(entities))

    def delete(self, entity: object) -> None:
        self.session.delete(entity)

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def refresh(self, entity: object) -> None:
        self.session.refresh(entity)
