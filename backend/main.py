import contextlib
from fastapi import FastAPI

from .config import settings
from .git import GitRepositoryManager

from .game import setup_database, APIRouter

@contextlib.asynccontextmanager
async def app_lifecycle(app: FastAPI):
    setup_database()
    repo_manager = GitRepositoryManager()
    yield
    repo_manager.cleanup()

app = FastAPI(lifespan=app_lifecycle)

app.include_router(APIRouter, prefix="/api")

@app.get("/")
def root():
    return {"message": "Hello, this is working!"}
