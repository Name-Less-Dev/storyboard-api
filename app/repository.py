from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import BriefRow, SceneRow
from app.schemas import BriefResult


def create_brief(db: Session, result: BriefResult) -> BriefRow:
    brief = result.brief
    row = BriefRow(
        product_name=brief.product_name,
        audience=brief.audience,
        tone=brief.tone,
        duration_seconds=brief.duration_seconds,
        scenes=[
            SceneRow(
                order=scene.order,
                duration_seconds=scene.duration_seconds,
                visual=scene.visual,
                narration=scene.narration,
            )
            for scene in result.storyboard.scenes
        ],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_briefs(db: Session) -> list[BriefRow]:
    stmt = select(BriefRow).order_by(BriefRow.created_at.desc(), BriefRow.id.desc())
    return list(db.scalars(stmt))


def get_brief(db: Session, brief_id: int) -> BriefRow | None:
    stmt = (
        select(BriefRow)
        .where(BriefRow.id == brief_id)
        .options(selectinload(BriefRow.scenes))
    )
    return db.scalar(stmt)
