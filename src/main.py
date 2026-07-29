import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.api_v1 import router as api_router
from src.core.config import configure_logging, setting

description = """
    API resume review

    You will be able to:

    * **Read users**
    * **Create/Update/Remove users**
    * **Load file**
"""


app = FastAPI(
    title="API_ResumeReview",
    description=description,
    version="0.1.0",
    docs_url="/docs",
)

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1",
    "https://airportcards.ru",
    "https://www.airportcards.ru",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=setting.secret_key.get_secret_value())

app.include_router(router=api_router)

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
