from fastapi import FastAPI
from .database import engine, Base
from .routers import leads as leads_router
from . import models
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI(title="Mini Lead CRM")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("uvicorn.error")

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.exception(f"Error while processing request: {e}")
        raise

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(leads_router.router)

@app.get("/")
def root():
    return {"message": "Mini Lead CRM backend running"}
