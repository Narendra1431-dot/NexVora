"""Compatibility helpers.

Two environments are supported:

* **modern** — Python 3.14 / PyMongo 4.12 (server returns the OIDC handshake),
  where the async driver is the maintained surface.
* **pinned** — the versions in ``requirements.txt`` (Motor 3.6 / PyMongo 4.9),
  used when a machine only has an older Python or a restricted network.

Both are exposed through the same tiny surface: ``connect_async``,
``close_async`` and ``run_command``.
"""

from __future__ import annotations

import inspect
from typing import Any, Optional

import pymongo

try:  # pragma: no cover - depends on installed driver set
    from motor.motor_asyncio import AsyncIOMotorClient

    _HAS_MOTOR = True
except Exception:  # noqa: BLE001
    AsyncIOMotorClient = None  # type: ignore[assignment]
    _HAS_MOTOR = False

try:  # pragma: no cover - depends on installed driver set
    from pymongo import AsyncMongoClient

    _HAS_PYMONGO_ASYNC = True
except Exception:  # noqa: BLE001
    AsyncMongoClient = None  # type: ignore[assignment]
    _HAS_PYMONGO_ASYNC = False


def available_backends() -> tuple[str, ...]:
    backends: list[str] = []
    if _HAS_MOTOR:
        backends.append("motor")
    if _HAS_PYMONGO_ASYNC:
        backends.append("pymongo-async")
    return tuple(backends)


def driver_version() -> str:
    return pymongo.version


class _CollectionProxy:
    """Uniform collection access for both async drivers."""

    __slots__ = ("_collection",)

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    def __getattr__(self, item: str) -> Any:
        return getattr(self._collection, item)

    def __getitem__(self, item: str) -> "_CollectionProxy":
        return _CollectionProxy(self._collection[item])


class _DatabaseProxy:
    __slots__ = ("_db",)

    def __init__(self, db: Any) -> None:
        self._db = db

    def __getitem__(self, name: str) -> _CollectionProxy:
        return _CollectionProxy(self._db[name])

    def __getattr__(self, item: str) -> Any:
        return getattr(self._db, item)


class MongoRunner:
    """Owns the client and hides which async driver is in use."""

    def __init__(self) -> None:
        self._client: Any = None
        self._db: Any = None
        self._backend: Optional[str] = None

    @property
    def backend(self) -> Optional[str]:
        return self._backend

    @property
    def client(self) -> Any:
        return self._client

    async def connect_async(self, uri: str, db_name: str, timeout_ms: int = 4000) -> Any:
        if self._db is not None:
            return self._db

        errors: list[str] = []
        if _HAS_PYMONGO_ASYNC:
            try:
                client = AsyncMongoClient(uri, serverSelectionTimeoutMS=timeout_ms, uuidRepresentation="standard")
                await client.admin.command("ping")
                self._client, self._backend = client, "pymongo-async"
            except Exception as exc:  # noqa: BLE001
                errors.append(f"pymongo-async: {exc}")
        if self._client is None and _HAS_MOTOR:
            try:
                client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=timeout_ms, uuidRepresentation="standard")
                await client.admin.command("ping")
                self._client, self._backend = client, "motor"
            except Exception as exc:  # noqa: BLE001
                errors.append(f"motor: {exc}")

        if self._client is None:
            raise RuntimeError("No usable MongoDB async driver. Tried: " + "; ".join(errors))

        self._db = _DatabaseProxy(self._client[db_name])
        return self._db

    def database(self) -> Any:
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect_async() during startup.")
        return self._db

    async def close_async(self) -> None:
        if self._client is not None:
            result = self._client.close()
            if inspect.isawaitable(result):
                await result
        self._client = None
        self._db = None
        self._backend = None

    async def server_version(self) -> Optional[str]:
        info = await self.database().command("buildInfo")
        return info.get("version")


runner = MongoRunner()
