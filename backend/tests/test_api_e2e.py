import pytest


@pytest.mark.asyncio
async def test_health(client):
    res = await client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "categories" in body


@pytest.mark.asyncio
async def test_pilot_flow(client):
    channels = (await client.get("/api/v1/channels")).json()
    assert channels, "seed channel expected"

    topics = (await client.get("/api/v1/topics")).json()
    assert topics, "seed topics expected"

    topic = next(
        t
        for t in topics
        if t["status"] in ("recommended", "approved", "generated", "review_required")
    )
    approve = await client.post(f"/api/v1/topics/{topic['id']}/approve")
    assert approve.status_code == 200
    job_id = approve.json()["job_id"]

    run = await client.post(f"/api/v1/jobs/{job_id}/run")
    assert run.status_code == 200

    job = (await client.get(f"/api/v1/jobs/{job_id}")).json()
    assert job["status"].lower() in (
        "qa_pending",
        "ready_to_publish",
        "published",
        "rendering",
        "scripting",
        "metadata_approved",
    )

    publish = await client.post(f"/api/v1/jobs/{job_id}/publish")
    assert publish.status_code == 200
    pub = publish.json()
    assert pub["dry_run"] is True
