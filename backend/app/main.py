import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import close, ensure_database, ensure_indexes, server_info
from .routers import ai, auth, catalog, mutations, notifications, student, documents, workflow, reviews
from .seed.run import seed_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("plcip.main")

# Global task tracking for RAG indexing
_rag_indexing_task = None
_rag_indexing_started = False
_rag_indexing_complete = False
_rag_indexing_lock = asyncio.Lock()
@asynccontextmanager
async def lifespan(application: FastAPI):
    # Store background tasks to manage them properly
    background_tasks = []
    
    # Startup sequence
    await _startup_sequence()
    
    try:
        yield {"background_tasks": background_tasks}
    finally:
        # Shutdown sequence
        await _shutdown_sequence(background_tasks)
app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)
from .middleware import rate_limit
app.middleware("http")(rate_limit)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix + "/v1")
app.include_router(catalog.router, prefix=settings.api_prefix + "/v1")
app.include_router(student.router, prefix=settings.api_prefix + "/v1")
app.include_router(mutations.router, prefix=settings.api_prefix + "/v1")
app.include_router(notifications.router, prefix=settings.api_prefix + "/v1")
app.include_router(ai.router, prefix=settings.api_prefix + "/v1")
app.include_router(documents.router, prefix=settings.api_prefix + "/v1")
app.include_router(workflow.router, prefix=settings.api_prefix + "/v1")
app.include_router(reviews.router, prefix=settings.api_prefix + "/v1")


async def _startup_sequence() -> None:
    """Run startup sequence but don't wait for RAG indexing."""
    logger.info("Starting application startup sequence...")
    
    # Essential startup that should complete quickly
    await ensure_database()
    await ensure_indexes()
    
    if settings.seed_on_startup:
        await seed_all()
    
    from .routers.coding import initialize
    await initialize()
    
    from .services import llm
    await llm.is_available()

    from .services import openrouter
    if settings.openrouter_api_key and llm.provider_name()!='OpenRouter':
        await openrouter.is_available()
    
    logger.info("API ready (prefix %s), starting RAG indexing in background", settings.api_prefix)
    
    # Start RAG indexing in background task
    global _rag_indexing_task, _rag_indexing_started
    if not _rag_indexing_started:
        _rag_indexing_started = True
        _rag_indexing_task = asyncio.create_task(_rag_indexing_background_task())
        logger.info("Started RAG indexing background task")
    else:
        logger.info("RAG indexing already started, skipping")


async def _rag_indexing_background_task() -> None:
    """Background task to build RAG index without blocking startup."""
    global _rag_indexing_task, _rag_indexing_complete
    try:
        from .services.rag import ensure_index
        logger.info("Starting background RAG indexing...")
        result = await ensure_index()
        logger.info("Background RAG indexing completed: %s chunks using %s", result.get('chunks', 0), result.get('backend', 'unknown'))
        _rag_indexing_complete = True
    except asyncio.CancelledError:
        logger.info("RAG indexing task was cancelled")
        raise
    except Exception as exc:
        logger.error("Background RAG indexing failed: %s", exc, exc_info=True)
    finally:
        _rag_indexing_task = None


async def _shutdown_sequence(background_tasks: list) -> None:
    """Shutdown sequence - cancel background tasks."""
    logger.info("Shutting down application...")
    
    # Cancel RAG indexing task if it's running
    global _rag_indexing_task
    if _rag_indexing_task and not _rag_indexing_task.done():
        logger.info("Cancelling RAG indexing task...")
        _rag_indexing_task.cancel()
        try:
            await _rag_indexing_task
        except asyncio.CancelledError:
            logger.info("RAG indexing task successfully cancelled")
        except Exception as exc:
            logger.error("Error during RAG indexing task cancellation: %s", exc)
    
    # Cancel any other background tasks
    for task in background_tasks:
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                logger.error("Error during background task cancellation: %s", exc)
    
    await close()
    logger.info("Application shutdown complete")



@app.get("/health", include_in_schema=False)
@app.get("/api/health", include_in_schema=False)
async def health() -> dict[str, object]:
    from .services import rag
    from .ml.inference.ranker import model, predict
    db_status = "healthy"
    try:
        db_info = await server_info()
    except Exception:
        db_info = {}; db_status = "unavailable"
    try:
        rag_info = await rag.health()
    except Exception:
        rag_info = {"status":"unavailable"}
    try:
        from .ml.inference.advisory import predict as advisory_predict
        predict([.5]*5)
        advisory_predict('evidence-strength',[.5]*5)
        advisory_predict('learning-risk',[.5]*5)
        ml_status = 'healthy_synthetic_demo'
    except Exception:
        ml_status = "unavailable"
    return {"api":"healthy", "mongodb":db_status, "database":db_info, "llm":await llm_health(), "rag":rag_info, "ml":ml_status, "agents":"read_only_tools_available"}



async def llm_health() -> dict[str, object]:
    from .services import llm

    return await llm.health()

from .routers import certificates
app.include_router(certificates.router, prefix=settings.api_prefix + "/v1")

from .routers import external_credentials
app.include_router(external_credentials.router, prefix=settings.api_prefix + "/v1")

from .routers import learning_hub
app.include_router(learning_hub.router, prefix=settings.api_prefix + "/v1")

from .routers import agent
app.include_router(agent.router,prefix=settings.api_prefix + "/v1")
from .routers import agent_runs
app.include_router(agent_runs.router,prefix=settings.api_prefix + "/v1")

@app.get('/health/agents',include_in_schema=False)
async def agents_health():
    from .services import llm,rag,openrouter
    from .db import database,col
    from .ml.inference.ranker import predict
    try:await database().command('ping');mongo='healthy'
    except Exception:mongo='unavailable'
    try:rag_status=await rag.health()
    except Exception:rag_status={'status':'unavailable'}
    try:predict([.5]*5);ml='healthy_synthetic_demo_advisory_only'
    except Exception:ml='unavailable'
    failed=await col('agent_runs').count_documents({'kind':'workflow','status':'failed'}) if mongo=='healthy' else None
    return {'supervisor':'controlled_workflow_ready','rag':rag_status,'ml':ml,'mongodb':mongo,
            'openrouter':{'status':openrouter._provider_status.get('OpenRouter','unverified') if settings.openrouter_api_key else 'missing_credentials'},
            'activeProvider':await llm.health(),'workflow':{'status':'unavailable' if mongo!='healthy' else 'recovery_needed' if failed else 'ready','automatic':True}}

from .routers import profile_avatar
app.include_router(profile_avatar.router, prefix=settings.api_prefix + "/v1")

from .routers import resume_generator
app.include_router(resume_generator.router,prefix=settings.api_prefix + "/v1")

from .routers import coding
app.include_router(coding.router,prefix=settings.api_prefix + "/v1")

from .routers import intelligence
app.include_router(intelligence.router,prefix=settings.api_prefix + "/v1")
app.add_api_route('/health/intelligence',intelligence.intelligence_health,methods=['GET'])


from .routers import assistant
app.include_router(assistant.router, prefix=settings.api_prefix + "/v1")


@app.get('/api/v1/health/agentic')
async def agentic_health():
    from .routers.intelligence import intelligence_health
    from .integrations.agent_zero.health import health as agent_zero_health
    h = await intelligence_health()
    return {'supervisor': 'healthy', 'openDotsRuntime': 'adapted_gateway_enabled', 'openRouter': h['providers']['openrouter']['status'],
        'actionGateway': 'healthy', 'approvalBroker': h['mongodb'], 'audit': h['mongodb'],
        'rag': h['rag'], 'mongodb': h['mongodb'], 'worker': h['workers'], 'computer': 'disabled', 'meta': 'disabled',
        'centralBrain': h['centralBrain'], 'agentZero': await agent_zero_health(), 'vectorDb': h['vectorDb'],
        'jobQueue': h['jobQueue'], 'workers': h['workers'], 'eventStream': 'available', 'toolGateway': 'available'}


@app.get("/api/v1/health")
async def health_v1() -> dict[str, object]:
    from .services import rag
    from .ml.inference.ranker import model, predict
    db_status = "healthy"
    try:
        db_info = await server_info()
    except Exception:
        db_info = {}; db_status = "unavailable"
    try:
        rag_info = await rag.health()
    except Exception:
        rag_info = {"status":"unavailable"}
    try:
        from .ml.inference.advisory import predict as advisory_predict
        predict([.5]*5)
        advisory_predict('evidence-strength',[.5]*5)
        advisory_predict('learning-risk',[.5]*5)
        ml_status = 'healthy_synthetic_demo'
    except Exception:
        ml_status = "unavailable"
    return {"api":"healthy", "mongodb":db_status, "database":db_info, "llm":await llm_health(), "rag":rag_info, "ml":ml_status, "agents":"read_only_tools_available"}
