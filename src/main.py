from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.utils.log_util import LogFactory, logger_name
from src.apis import user_apis
from src.apis import balance_apis

import logging
import os


LogFactory.configure_logger(
    logger_name=logger_name, logging_level=os.environ.get("LOGGING_LEVEL", "WARNING")
)
logger = logging.getLogger(logger_name)

app = FastAPI(title="Splitwise App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_apis.user_router, tags=["Tag Version 1"])
app.include_router(balance_apis.balance_router, tags=["Tag Version 1"])

@app.get("/")
def read_root():
    return {"version": "0.1", "name": "starter-service-python event receiver REST API"}


@app.get("/health")
def health():
    return {"status": "ok"}
