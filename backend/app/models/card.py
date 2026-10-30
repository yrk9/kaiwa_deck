import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # 公式のお題は作成者なし(NULL)。作成者が消えたら、そのお題も消す
    create_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    content: Mapped[str]
    description: Mapped[str | None]
    # 公式のお題だけが持つ種類(面接の定番など)。自分のお題はNULL
    category: Mapped[str | None]
