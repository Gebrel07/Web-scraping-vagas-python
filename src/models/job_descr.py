from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class JobDescr(Base):
    __tablename__ = "JobDescr"

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    word: Mapped[str] = mapped_column(String(255), nullable=False)
    freq: Mapped[int] = mapped_column(Integer(), nullable=False)

    def __repr__(self) -> str:
        return f"JobDescr(id={self.id!r}, word={self.word!r}, freq={self.freq!r})"
