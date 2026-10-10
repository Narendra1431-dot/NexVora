"""Failure-path acceptance (Phase 14): an unavailable provider must produce a
genuine FAILED run with a recorded error code and no fabricated result."""

import asyncio, os, sys, uuid
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["MONGODB_DB"] = "career_intelligence_qa"
os.environ["RATE_LIMIT_PER_MINUTE"] = "2000"
os.environ["SEED_ON_STARTUP"] = "false"
os.environ["DISABLE_RAG_INDEX"] = "true"


class LockTransport:
    @asynccontextmanager
    async def lock(self, *args, **kwargs):
        yield


async def main() -> None:
    from fastapi.testclient import TestClient
    from app.main import app
    from app.workers import tasks
    from app.providers.base import ProviderError
    from app.agents import graph as agent_graph

    async def unavailable(prompt, schema, context, **kwargs):
        raise ProviderError("http_429", "groq")

    original = agent_graph.structured
    agent_graph.structured = unavailable
    try:
        with TestClient(
            app, backend_options={"loop_factory": asyncio.SelectorEventLoop}
        ) as client:
            reg = client.post(
                "/api/v1/auth/register",
                json={
                    "name": "Fail QA",
                    "email": f"fail-{uuid.uuid4().hex}@example.com",
                    "password": "qa-secure-pass",
                },
            )
            headers = {"Authorization": "Bearer " + reg.json()["token"]}
            created = client.post(
                "/api/v1/agent/runs/run",
                headers=headers,
                json={
                    "message": "Create my learning plan.",
                    "requestId": uuid.uuid4().hex,
                },
            ).json()
            run_id = created["id"]
            persisted = client.get(
                f"/api/v1/agent/runs/run/{run_id}", headers=headers
            ).json()
            client.portal.call(
                tasks.process_job, {"redis": LockTransport()}, persisted["jobId"]
            )
            final = client.get(
                f"/api/v1/agent/runs/run/{run_id}", headers=headers
            ).json()
            print(
                f"STATUS={final['status']} error={final.get('error')} result_present={bool(final.get('result'))}"
            )
            assert final["status"] == "FAILED", final
            assert final["error"]["code"] == "http_429", final["error"]
            assert not final.get(
                "result"
            ), "a failed run must not store a fabricated result"
            print(
                "FAILURE PATH OK: genuine FAILED, error recorded, no fabricated result"
            )
    finally:
        agent_graph.structured = original


asyncio.run(main())
