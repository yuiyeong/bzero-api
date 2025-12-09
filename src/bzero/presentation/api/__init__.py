"""API router module.

All API endpoints are combined with /api/v1 prefix.
"""

from fastapi import APIRouter

from bzero.presentation.api.airship import router as airship_router
from bzero.presentation.api.city import router as city_router
from bzero.presentation.api.diary import router as diary_router
from bzero.presentation.api.questionnaire import router as questionnaire_router
from bzero.presentation.api.ticket import router as ticket_router
from bzero.presentation.api.user import router as user_router


router = APIRouter(prefix="/api/v1")

router.include_router(user_router)
router.include_router(city_router)
router.include_router(airship_router)
router.include_router(ticket_router)
router.include_router(diary_router)
router.include_router(questionnaire_router)
