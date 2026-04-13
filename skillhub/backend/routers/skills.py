from fastapi import APIRouter

from skillhub.backend.services.skill_manager import get_skills

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("")
def list_skills():
    return {"skills": get_skills()}
