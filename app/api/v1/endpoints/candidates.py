from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.candidate import Candidate, CandidateCreate, CandidateUpdate
from app.services import candidate as candidate_service
from app.core.dependencies import get_current_user
from app.services.auth_service import User

router = APIRouter()

@router.get("/", response_model=List[Candidate])
def read_candidates(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer tous les candidats.
    """
    candidates = candidate_service.get_candidates(db, skip=skip, limit=limit)
    return candidates

@router.post("/", response_model=Candidate, status_code=status.HTTP_201_CREATED)
def create_candidate(
    *,
    db: Session = Depends(get_db),
    candidate_in: CandidateCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Créer un nouveau candidat.
    """
    candidate = candidate_service.get_candidate_by_email(db, email=candidate_in.email)
    if candidate:
        raise HTTPException(
            status_code=400,
            detail="Un candidat avec cet email existe déjà."
        )
    candidate = candidate_service.create_candidate(db, candidate_in, current_user.id)
    return candidate

@router.get("/{candidate_id}", response_model=Candidate)
def read_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer un candidat.
    """
    candidate = candidate_service.get_candidate(db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    return candidate

@router.put("/{candidate_id}", response_model=Candidate)
def update_candidate(
    *,
    db: Session = Depends(get_db),
    candidate_id: int,
    candidate_in: CandidateUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Mettre à jour un candidat.
    """
    candidate = candidate_service.update_candidate(db, candidate_id=candidate_id, candidate=candidate_in)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    return candidate

@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(
    *,
    db: Session = Depends(get_db),
    candidate_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Supprimer un candidat.
    """
    success = candidate_service.delete_candidate(db, candidate_id=candidate_id)
    if not success:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    return None 