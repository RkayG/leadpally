import logging
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

# Internal imports
from database import init_db, get_db_session
from routes.leads import router as leads_router
from jobs.scheduler import get_scheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    logger.info("Initializing database...")
    init_db()

    logger.info("Starting routine scheduler...")
    try:
        scheduler = get_scheduler()
        scheduler.start()
    except Exception as e:
        logger.warning(f"Scheduler start notice: {e}")

    logger.info("Startup Client Acquisition Agent API is ready.")
    yield

    logger.info("Shutting down scheduler...")
    try:
        scheduler.shutdown()
    except Exception as e:
        logger.warning(f"Scheduler shutdown notice: {e}")

app = FastAPI(
    title="Startup Client Acquisition Agent",
    description="Backend API for discovering early-stage startups and monitoring for development opportunities.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads_router)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Startup Client Acquisition Agent"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)