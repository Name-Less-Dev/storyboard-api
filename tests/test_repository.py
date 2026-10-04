from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app import repository
from app.models import BriefRow, SceneRow
from tests.conftest import make_result


def count(db, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def test_create_brief_persists_brief_and_scenes(db_session):
    row = repository.create_brief(db_session, make_result(duration_seconds=32))

    assert row.id is not None
    assert row.created_at is not None
    assert count(db_session, BriefRow) == 1
    assert count(db_session, SceneRow) == 3


def test_get_brief_returns_scenes_ordered_by_order(db_session):
    created = repository.create_brief(db_session, make_result())
    db_session.expire_all()  # force a real reload from the database

    fetched = repository.get_brief(db_session, created.id)

    assert fetched is not None
    assert [scene.order for scene in fetched.scenes] == [1, 2, 3]


def test_list_briefs_returns_newest_first(db_session):
    older = repository.create_brief(db_session, make_result(product_name="Older"))
    newer = repository.create_brief(db_session, make_result(product_name="Newer"))
    older.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    newer.created_at = datetime(2026, 6, 1, tzinfo=timezone.utc)
    db_session.commit()

    names = [row.product_name for row in repository.list_briefs(db_session)]

    assert names == ["Newer", "Older"]


def test_get_brief_returns_none_for_unknown_id(db_session):
    assert repository.get_brief(db_session, 9999) is None


def test_deleting_brief_cascades_to_scenes(db_session):
    row = repository.create_brief(db_session, make_result())

    db_session.delete(row)
    db_session.commit()

    assert count(db_session, BriefRow) == 0
    assert count(db_session, SceneRow) == 0


def test_scene_with_unknown_brief_id_violates_foreign_key(db_session):
    db_session.add(
        SceneRow(brief_id=9999, order=1, duration_seconds=10, visual="v", narration="n")
    )

    with pytest.raises(IntegrityError, match="FOREIGN KEY"):
        db_session.commit()
    db_session.rollback()
