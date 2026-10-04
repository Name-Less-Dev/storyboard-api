from datetime import datetime, timezone

from app.models import BriefRow
from app.schemas import BriefCreate, BriefRecord, BriefSummary, Scene, Storyboard


def _as_utc(value: datetime) -> datetime:
    # SQLite stores datetimes without timezone; values are always written in UTC.
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def to_summary(row: BriefRow) -> BriefSummary:
    return BriefSummary(
        id=row.id,
        product_name=row.product_name,
        tone=row.tone,
        duration_seconds=row.duration_seconds,
        created_at=_as_utc(row.created_at),
    )


def to_record(row: BriefRow) -> BriefRecord:
    return BriefRecord(
        id=row.id,
        created_at=_as_utc(row.created_at),
        brief=BriefCreate(
            product_name=row.product_name,
            audience=row.audience,
            tone=row.tone,
            duration_seconds=row.duration_seconds,
        ),
        storyboard=Storyboard(
            scenes=[
                Scene(
                    order=scene.order,
                    duration_seconds=scene.duration_seconds,
                    visual=scene.visual,
                    narration=scene.narration,
                )
                for scene in row.scenes
            ]
        ),
    )
