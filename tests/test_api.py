import logging

from app.schemas import BriefCreate, Scene, Storyboard

VALID_BRIEF = {
    "product_name": "Brew Box",
    "audience": "remote workers",
    "tone": "casual",
    "duration_seconds": 32,
}


def post_brief(client, **overrides):
    return client.post("/briefs", json=VALID_BRIEF | overrides)


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_valid_brief_returns_201_with_record(client):
    response = post_brief(client)

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["created_at"]
    assert body["brief"] == VALID_BRIEF
    assert len(body["storyboard"]["scenes"]) == 3


def test_post_invalid_brief_returns_422_and_saves_nothing(client):
    response = post_brief(client, tone="banana", duration_seconds=-5)

    assert response.status_code == 422
    assert {err["loc"][-1] for err in response.json()["detail"]} == {"tone", "duration_seconds"}
    assert client.get("/briefs").json() == []


def test_list_briefs_returns_newest_first(client):
    first = post_brief(client, product_name="First").json()
    second = post_brief(client, product_name="Second").json()

    response = client.get("/briefs")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [second["id"], first["id"]]


def test_get_brief_returns_full_storyboard_in_order(client):
    created = post_brief(client).json()

    response = client.get(f"/briefs/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body == created
    assert [scene["order"] for scene in body["storyboard"]["scenes"]] == [1, 2, 3]


def test_get_unknown_brief_returns_404(client):
    response = client.get("/briefs/9999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Brief not found"}


def test_invalid_generator_output_returns_502_and_saves_nothing(client, monkeypatch, caplog):
    def broken_generator(brief: BriefCreate) -> Storyboard:
        return Storyboard(
            scenes=[
                Scene(order=1, duration_seconds=6, visual="v", narration="n"),
                Scene(order=2, duration_seconds=6, visual="v", narration="n"),
                Scene(order=3, duration_seconds=7, visual="v", narration="n"),
            ]
        )  # 19s

    # Patch where the route looks the name up, not where it is defined.
    monkeypatch.setattr("app.main.generate_storyboard", broken_generator)

    with caplog.at_level(logging.ERROR, logger="app.main"):
        response = post_brief(client, duration_seconds=20)

    assert response.status_code == 502
    assert response.json() == {"detail": "Generated storyboard failed validation"}
    assert "failed validation" in caplog.text
    assert client.get("/briefs").json() == []
