from fastapi import APIRouter

from app.api import auth, fixtures, notifications, teams, users


router = APIRouter()
router.include_router(auth.router)
router.include_router(fixtures.router)
router.include_router(teams.router)
router.include_router(users.router)
router.include_router(notifications.router)
