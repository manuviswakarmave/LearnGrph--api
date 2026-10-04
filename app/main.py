import uvicorn
from fastapi import FastAPI

from app.core.config import settings

from sqlalchemy import  text
from app.db.session import engine
from app.api.routes.documents import router as documents_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(
    documents_router,
    prefix="/api/v1"
)

@app.get("/health")
def healthcheck():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "database" : "Connected"
    }

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)