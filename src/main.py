import logging
import time
import warnings

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from fastapi_pagination.utils import FastAPIPaginationWarning
from prometheus_client import Counter, Histogram
from starlette.middleware.sessions import SessionMiddleware
from starlette_exporter import PrometheusMiddleware, handle_metrics

from src.api_v1 import router as api_router
from src.core.config import configure_logging, setting

description = """
    API airport directory

    You will be able to:

    * **Read users**
    * **Create/Update/Remove users**
    * **Load file**
"""

warnings.simplefilter("ignore", FastAPIPaginationWarning)

app = FastAPI(
    title="API_AirportDirectory",
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
    # allow_origins=["*"],
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=setting.secret_key.get_secret_value())

# Добавляем middleware для сбора метрик по умолчанию
app.add_middleware(
    PrometheusMiddleware,
    app_name="my-fastapi-app",
    group_paths=True,  # Группирует параметризированные пути
    labels={"method": True, "path": True, "status": True},  # Включаем нужные лейблы
)

# Добавляем эндпоинт для метрик
app.add_route("/metrics", handle_metrics)

app.include_router(router=api_router)

add_pagination(app)

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)

# Создаем кастомные метрики
REQUEST_COUNT = Counter(
    "app_request_count",
    "Total number of requests",
    ["method", "path", "status_code"],
)

REQUEST_DURATION = Histogram(
    "app_request_duration_seconds",
    "Request processing time",
    ["method", "path"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
)


# Middleware для кастомных метрик
@app.middleware("http")
async def custom_metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    REQUEST_COUNT.labels(method=request.method, path=request.url.path, status_code=response.status_code).inc()

    REQUEST_DURATION.labels(method=request.method, path=request.url.path).observe(process_time)

    return response


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
