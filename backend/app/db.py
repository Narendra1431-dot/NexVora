"""MongoDB connection, collection registry, indexes and startup validation.

Every module in the API talks to the database through this file so that the
collection names, indexes and validators live in exactly one place.

Credentials never leave the backend process: the frontend only ever talks to
the FastAPI routers, which resolve the caller's ``studentId`` from their JWT.
"""

from __future__ import annotations
import logging
from typing import Any
from .config import settings
from .mongo_compat import runner

logger = logging.getLogger("plcip.db")

# Canonical collection names (Step 12 of the build brief).
COLLECTIONS: dict[str, str] = {
    "assistant_messages": "assistantMessages",
    "agent_steps": "agentSteps",
    "agent_tool_calls": "agentToolCalls",
    "agent_events": "agentEvents",
    "agent_artifacts": "agentArtifacts",
    "runtime_actions": "runtimeActions",
    "runtime_audit": "runtimeAudit",
    "intelligence_jobs": "intelligenceJobs",
    "intelligence_documents": "intelligenceDocuments",
    "intelligence_chunks": "intelligenceChunks",
    "intelligence_results": "intelligenceResults",
    "intelligence_traces": "intelligenceTraces",
    "coding_problems": "codingProblems",
    "coding_games": "codingGames",
    "coding_submissions": "codingSubmissions",
    "coding_progress": "codingProgress",
    "game_progress": "gameProgress",
    "coding_stats": "codingStats",
    "coding_drafts": "codingDrafts",
    "coding_reports": "codingReports",
    "xp_transactions": "xpTransactions",
    "resume_drafts": "resumeDrafts",
    "agent_recommendations": "agentRecommendations",
    "agent_memory": "agentMemory",
    "agent_messages": "agentMessages",
    "learning_videos": "learningVideos",
    "learning_topics": "learningTopics",
    "learning_careers": "learningCareers",
    "learning_pdfs": "learningPdfs",
    "external_credentials": "externalCredentials",
    "certificates": "certificates",
    "certificate_orders": "certificateOrders",
    "agent_runs": "agentRuns",
    "rag_documents": "ragDocuments",
    "rag_chunks": "ragChunks",
    "diagnostics": "diagnostics",
    "users": "users",
    "password_resets": "passwordResets",
    "profiles": "profiles",
    "skills": "skills",
    "concepts": "concepts",
    "careers": "careers",
    "career_requirements": "careerRequirements",
    "evidence": "evidence",
    "competencies": "competencies",
    "roadmaps": "roadmaps",
    "assessments": "assessments",
    "attempts": "attempts",
    "resources": "resources",
    "projects": "projects",
    "submissions": "submissions",
    "resume_analysis": "resumeAnalysis",
    "documents": "documents",
    "notifications": "notifications",
    "events": "events",
    "analytics": "analyticsSnapshots",
}

_client: Any = None
_db: Any = None


async def connect() -> Any:
    """Create the process-wide client and verify the server answers."""
    global _client, _db
    if _db is not None:
        return _db

    # Fails fast and loudly: a missing database is a misconfiguration, not a
    # runtime condition we should silently degrade around.
    _db = await runner.connect_async(settings.mongodb_uri, settings.mongodb_db)
    _client = runner.client
    logger.info("Connected to MongoDB database '%s' via %s", settings.mongodb_db, runner.backend)
    return _db


async def close() -> None:
    global _client, _db
    await runner.close_async()
    _client = None
    _db = None


def database() -> Any:
    if _db is None:
        raise RuntimeError("Database not connected. Call connect() during startup.")
    return _db

def col(key: str) -> Any:
    """Fetch a collection by its registry key (e.g. ``col('evidence')``)."""
    if key not in COLLECTIONS:
        raise KeyError(f"Unknown collection key '{key}'")
    return database()[COLLECTIONS[key]]


def public_collection_keys() -> list[str]:
    return sorted(COLLECTIONS.keys())


async def ensure_database() -> None:
    """Ping the server so a bad MONGODB_URI fails at boot, not at first request."""
    await connect()
    await database().command("ping")


async def ensure_indexes() -> None:
    """Create indexes and per-collection schema validation.

    Called once during startup. Safe to re-run: ``create_index`` is idempotent
    and ``collMod`` failures (e.g. on a freshly created collection that the
    validator cannot apply to) are logged rather than fatal.
    """
    db = database()

    # --- Ownership + uniqueness indexes -----------------------------------
    await col('runtime_actions').create_index([('studentId',1),('requestId',1)],unique=True)
    await col('runtime_actions').create_index('id',unique=True)
    await col('agent_steps').create_index('stepId',unique=True)
    await col('agent_tool_calls').create_index('toolCallId',unique=True)
    await col('agent_events').create_index('eventId',unique=True)
    for name in ('agent_steps','agent_tool_calls','agent_events','agent_artifacts'):
        await col(name).create_index([('studentId',1),('runId',1)])
    await col('runtime_audit').create_index([('studentId',1),('timestamp',-1)])
    await db[COLLECTIONS["users"]].create_index("email", unique=True)
    await col('password_resets').create_index('tokenHash', unique=True)
    await col('password_resets').create_index([('email', 1), ('used', 1)])
    for key in ("profiles", "competencies", "evidence", "roadmaps", "analytics"):
        indexes = await db[COLLECTIONS[key]].index_information()
        needs_unique = key in {'profiles', 'competencies', 'roadmaps'}
        if needs_unique and 'studentId_1' in indexes and not indexes['studentId_1'].get('unique'):
            await db[COLLECTIONS[key]].drop_index('studentId_1')
        await db[COLLECTIONS[key]].create_index("studentId", unique=needs_unique)

    for key in ("notifications", "events", "attempts", "submissions", "documents", "resume_analysis"):
        await db[COLLECTIONS[key]].create_index([("studentId", 1), ("createdAt", -1)])
    await db[COLLECTIONS["evidence"]].create_index([("studentId", 1), ("date", -1)])

    await db[COLLECTIONS["resources"]].create_index([("skillId", 1), ("difficulty", 1)])
    await db[COLLECTIONS["assessments"]].create_index("skillId")
    await db[COLLECTIONS["projects"]].create_index("skillsValidated")
    await db[COLLECTIONS["skills"]].create_index("slug", unique=True)
    await db[COLLECTIONS["careers"]].create_index("slug", unique=True)

    for key in ('competencies', 'roadmaps', 'resume_analysis'):
        await db[COLLECTIONS[key]].create_index('studentId', unique=True)
    for key in ('evidence', 'attempts', 'submissions', 'documents', 'events', 'notifications', 'agent_runs', 'diagnostics'):
        await db[COLLECTIONS[key]].create_index([('studentId', 1), ('id', 1)], unique=True)
    for key in ('skills', 'careers', 'resources', 'projects', 'assessments'):
        await db[COLLECTIONS[key]].create_index('id', unique=True)

    await col('xp_transactions').create_index([('studentId',1),('sourceType',1),('sourceId',1)],unique=True)
    # Ensure only the compound unique index exists on coding_progress; drop legacy single-field unique index if present.
    coding_progress_indexes = await db[COLLECTIONS['coding_progress']].index_information()
    if 'studentId_1' in coding_progress_indexes and coding_progress_indexes['studentId_1'].get('unique'):
        await db[COLLECTIONS['coding_progress']].drop_index('studentId_1')
    await col('coding_progress').create_index([('studentId',1),('problemId',1)],unique=True)
    await col('game_progress').create_index([('studentId',1),('gameId',1),('level',1)],unique=True)
    await col('coding_submissions').create_index([('studentId',1),('requestId',1)],unique=True)
    await col('coding_drafts').create_index([('studentId',1),('problemId',1),('language',1)],unique=True)
    await col('intelligence_jobs').create_index('jobId',unique=True)
    await col('intelligence_jobs').create_index([('studentId',1),('requestId',1)],unique=True)
    await col('intelligence_jobs').create_index([('status',1),('createdAt',1)])
    await col('intelligence_documents').create_index('id',unique=True)
    await col('intelligence_documents').create_index([('studentId',1),('createdAt',-1)])
    await col('intelligence_chunks').create_index('id',unique=True)
    await col('intelligence_chunks').create_index([('studentId',1),('documentId',1)])
    await col('intelligence_results').create_index('id',unique=True)
    await col('intelligence_traces').create_index([('studentId',1),('createdAt',-1)])
    await col('coding_stats').create_index('studentId',unique=True)
    await col('coding_problems').create_index('problemId',unique=True)
    await col('coding_games').create_index('gameId',unique=True)
    await col('resume_drafts').create_index([('studentId',1),('updatedAt',-1)])
    await col('resume_drafts').create_index('draftId',unique=True)
    await col('learning_videos').create_index('id', unique=True)
    await col('agent_recommendations').create_index([('studentId',1),('stateVersion',1)],unique=True)
    await col('agent_memory').create_index('studentId',unique=True)
    await col('assistant_messages').create_index([('studentId',1),('id',1)],unique=True)
    await col('agent_messages').create_index([('studentId',1),('id',1)],unique=True)
    await col('agent_runs').create_index([('studentId',1),('requestId',1)],unique=True,partialFilterExpression={'requestId':{'$exists':True}})
    await col('learning_topics').create_index([('id',1),('signature',1)], unique=True)
    await col('learning_careers').create_index('careerId', unique=True)
    await col('learning_pdfs').create_index('key', unique=True)
    await col('external_credentials').create_index('id', unique=True)
    await col('external_credentials').create_index([('studentId',1),('certificationId',1)], unique=True)
    await col('certificates').create_index('certificateId', unique=True)
    await col('certificates').create_index([('studentId',1),('courseId',1),('type',1)], unique=True)
    await col('certificate_orders').create_index('orderId', unique=True)
    await col('certificate_orders').create_index([('studentId',1),('courseId',1)])

    # --- Schema validation ------------------------------------------------
    # Lightweight validators: they reject structurally invalid writes (missing
    # ownership, wrong score type, out-of-range mastery) without pinning the
    # document shape so tightly that additive fields break old data.
    validators: dict[str, dict[str, Any]] = {
        "users": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["email", "passwordHash", "createdAt"],
                "properties": {
                    "email": {"bsonType": "string"},
                    "passwordHash": {"bsonType": "string"},
                    "studentId": {"bsonType": "string"},
                },
            }
        },
        "evidence": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["studentId", "title", "type", "verificationState"],
                "properties": {
                    "studentId": {"bsonType": "string"},
                    "title": {"bsonType": "string"},
                    "type": {"bsonType": "string"},
                    "verificationState": {
                        "enum": ["Verified", "Estimated", "Needs Review", "Unverified"]
                    },
                    "confidenceScore": {"bsonType": ["int", "double", "null"], "minimum": 0, "maximum": 100},
                },
            }
        },
        "competencies": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["studentId", "nodes"],
                "properties": {"studentId": {"bsonType": "string"}, "nodes": {"bsonType": "array"}},
            }
        },
        "attempts": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["studentId", "assessmentId", "score"],
                "properties": {
                    "studentId": {"bsonType": "string"},
                    "assessmentId": {"bsonType": "string"},
                    "score": {"bsonType": ["int", "double"], "minimum": 0, "maximum": 100},
                    "accuracy": {"bsonType": ["int", "double", "null"], "minimum": 0, "maximum": 100},
                },
            }
        },
        "notifications": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["studentId", "title", "message"],
                "properties": {
                    "studentId": {"bsonType": "string"},
                    "read": {"bsonType": ["bool", "null"]},
                },
            }
        },
    }

    for key, validator in validators.items():
        name = COLLECTIONS[key]
        try:
            if name not in await db.list_collection_names():
                await db.create_collection(name)
            await db.command({"collMod": name, "validator": validator, "validationLevel": "moderate"})
        except Exception as exc:  # noqa: BLE001 - validator application is best effort
            logger.debug("Validator for %s not applied: %s", name, exc)


async def server_info() -> dict[str, Any]:
    return {"version": await runner.server_version(), "database": settings.mongodb_db, "driver": runner.backend}
