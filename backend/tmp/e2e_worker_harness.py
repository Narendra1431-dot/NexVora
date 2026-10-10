"""End-to-end acceptance harness (Phase 14).

Drives the REAL run-creation API, the REAL worker function and the REAL SSE
stream against the QA database, with the AI provider stubbed deterministically.
The only thing substituted is the Redis transport (unavailable on this machine),
replaced by an in-process async lock that mimics arq's ctx['redis'].lock().
"""

import asyncio, json, os, sys, uuid
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["MONGODB_DB"] = "career_intelligence_qa"
os.environ["RATE_LIMIT_PER_MINUTE"] = "2000"
os.environ["SEED_ON_STARTUP"] = "false"
os.environ["DISABLE_RAG_INDEX"] = "true"


class LockTransport:
    """Stands in for arq's Redis: provides ctx['redis'].lock()."""

    @asynccontextmanager
    async def lock(self, *args, **kwargs):
        yield


async def main() -> None:
    from fastapi.testclient import TestClient
    from app.main import app
    from app.workers import tasks
    from app.providers.base import Generation
    from app.brain.schemas import Advisory
    from app.agents import graph as agent_graph

    # Deterministic provider double: the agent graph is the real code path.
    async def fake_structured(prompt, schema, context, **kwargs):
        if schema.__name__ == "Plan":
            data = schema(
                intent="career plan",
                agents=[
                    "profile",
                    "career",
                    "competency",
                    "evidence",
                    "gap",
                    "roadmap",
                    "resources",
                ],
            )
        else:
            data = Advisory(
                intent="explain",
                summary="Plan prepared from verified state.",
                recommendations=[],
                evidenceRefs=[],
                citations=[],
                confidence=0.7,
            )
        return data, Generation("", "test", "test-model", 1, 10), []

    original = agent_graph.structured
    agent_graph.structured = fake_structured
    try:
        with TestClient(
            app, backend_options={"loop_factory": asyncio.SelectorEventLoop}
        ) as client:
            reg = client.post(
                "/api/v1/auth/register",
                json={
                    "name": "E2E QA",
                    "email": f"e2e-{uuid.uuid4().hex}@example.com",
                    "password": "qa-secure-pass",
                },
            )
            assert reg.status_code == 201, reg.text
            token = reg.json()["token"]
            headers = {"Authorization": "Bearer " + token}

            req = {
                "message": "Analyze my profile and create my learning plan.",
                "requestId": uuid.uuid4().hex,
            }
            created = client.post("/api/v1/agent/runs/run", headers=headers, json=req)
            assert created.status_code == 202, created.text
            run = created.json()
            run_id = run["id"]
            print(f"1. RUN CREATED        id={run_id} status={run['status']}")
            assert run["status"] == "QUEUED"

            persisted = client.get(
                f"/api/v1/agent/runs/run/{run_id}", headers=headers
            ).json()
            print(
                f"2. PERSISTED          status={persisted['status']} jobId={persisted.get('jobId')}"
            )
            assert persisted["status"] == "QUEUED"

            # 3. Worker consumes the job (real process_job, real Mongo, real graph).
            client.portal.call(
                tasks.process_job, {"redis": LockTransport()}, persisted["jobId"]
            )

            final = client.get(
                f"/api/v1/agent/runs/run/{run_id}", headers=headers
            ).json()
            print(
                f"3. AFTER WORKER       status={final['status']} steps={len(final.get('steps', []))} error={final.get('error')}"
            )

            # 4. SSE stream delivers recorded events and closes at terminal state.
            events = []
            with client.stream(
                "GET", f"/api/v1/agent/runs/run/{run_id}/events", headers=headers
            ) as stream:
                for line in stream.iter_lines():
                    if line:
                        events.append(line)
                    if len(events) > 400:
                        break
            types = [e.split("event: ")[1] for e in events if e.startswith("event: ")]
            print(
                f"4. SSE events={len(events)} stream-end={'stream-end' in types} sample-types={sorted(set(types))}"
            )
            terminal = any(
                '"status": "COMPLETED"' in e or "run.completed" in e for e in events
            )
            print(f"5. TERMINAL EVENT SEEN = {terminal}")

            proof = final.get("proof", {})
            print(
                f"6. PROOF agentsExecuted={proof.get('agentsExecuted')} toolCalls={proof.get('toolCalls')} sources={proof.get('sourcesRetrieved')}"
            )
            print(
                "RESULT:",
                "COMPLETED" if final["status"] == "COMPLETED" else final["status"],
            )
    finally:
        agent_graph.structured = original


asyncio.run(main())
