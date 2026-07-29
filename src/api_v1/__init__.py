from fastapi import APIRouter

from src.api_v1.auth.views import router as auth_router
from src.api_v1.users.views import router as users_router
from src.api_v1.vacancies.views import router as vacancies_router

router = APIRouter(prefix="/api")
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(vacancies_router)
