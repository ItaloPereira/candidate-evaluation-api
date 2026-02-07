from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FutureProofing - Candidate Evaluation API",
    description="API for managing candidates and their technical evaluations.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
