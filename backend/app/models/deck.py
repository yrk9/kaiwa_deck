import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    create_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    deck_name: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # 更新するたびに、自動で今の時刻になる
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # デッキを消すと、中のdeck_cardsも一緒に消える
    cards: Mapped[list["DeckCard"]] = relationship(
        back_populates="deck", cascade="all, delete-orphan"
    )


class DeckCard(Base):
    """デッキとお題の中間テーブル。並び順は管理しない(テーブル設計.md参照)。"""

    __tablename__ = "deck_cards"

    deck_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("decks.id", ondelete="CASCADE"), primary_key=True
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"), primary_key=True
    )

    deck: Mapped["Deck"] = relationship(back_populates="cards")
