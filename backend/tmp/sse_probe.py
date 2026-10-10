"""Bounded SSE probe against the live backend. Uses the public demo account."""

import json
import urllib.request


def post(url, payload, headers=None):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json", **(headers or {})}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def main() -> None:
    base = "http://127.0.0.1:8000"
    login = post(
        base + "/api/v1/auth/demo",
        {"email": "alex.rivera@cs.university.edu", "password": "demo1234"},
    )
    auth = {"Authorization": "Bearer " + login["token"]}
    runs = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(base + "/api/v1/agent/runs/run", headers=auth),
            timeout=30,
        ).read()
    )
    print("runs:", len(runs))
    run_id = runs[0]["id"]
    print("run:", run_id, "status:", runs[0]["status"])

    req = urllib.request.Request(
        base + f"/api/v1/agent/runs/run/{run_id}/events", headers=auth
    )
    with urllib.request.urlopen(req, timeout=6) as resp:
        print("SSE content-type:", resp.headers.get("content-type"))
        print("SSE cache-control:", resp.headers.get("cache-control"))
        chunks = []
        try:
            for _ in range(6):
                line = resp.readline()
                if not line:
                    break
                chunks.append(line.decode(errors="replace").rstrip())
        except Exception as exc:  # noqa: BLE001
            chunks.append(f"<read stopped: {type(exc).__name__}>")
        print("first frames:")
        for c in chunks:
            print("  ", repr(c))


if __name__ == "__main__":
    main()
