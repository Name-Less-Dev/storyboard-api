from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BriefRow(Base):
    __tablename__ = "briefs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(80))
    audience: Mapped[str] = mapped_column(String(120))
    tone: Mapped[str] = mapped_column(String(20))
    duration_seconds: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now
    )

    scenes: Mapped[list["SceneRow"]] = relationship(
        back_populates="brief",
        order_by="SceneRow.order",
        cascade="all, delete-orphan",
    )


class SceneRow(Base):
    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brief_id: Mapped[int] = mapped_column(ForeignKey("briefs.id"), nullable=False)
    order: Mapped[int] = mapped_column(Integer)
    duration_seconds: Mapped[int] = mapped_column(Integer)
    visual: Mapped[str] = mapped_column(Text)
    narration: Mapped[str] = mapped_column(Text)

    brief: Mapped[BriefRow] = relationship(back_populates="scenes")
