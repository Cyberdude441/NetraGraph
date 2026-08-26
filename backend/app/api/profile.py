from fastapi import APIRouter, HTTPException, status
from ..models.profile import CriminalProfileResponse
from ..services.profile_service import profile_service

router = APIRouter(prefix="/profile", tags=["Criminal Profiles"])


@router.get(
    "/{entity_id}",
    response_model=CriminalProfileResponse,
    summary="Get complete criminal dossier & threat radar",
    description="Returns detailed subject dossier, threat radar vector breakdown (Violence, Finance, Mobility, Influence, Recidivism), offenses history, and surveillance timeline.",
)
async def get_subject_profile(entity_id: str) -> CriminalProfileResponse:
    profile = profile_service.get_criminal_profile(entity_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Criminal dossier for subject '{entity_id}' not found.",
        )
    return profile
