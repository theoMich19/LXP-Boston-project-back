from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth import UserResponse
from app.services.auth_service import auth_service, User
from app.core.dependencies import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def read_candidates(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Récupérer tous les candidats.
    """
    return db.query(User).filter(User.role == "candidate").offset(skip).limit(limit).all()

@router.get("/{candidate_id}", response_model=UserResponse)
def read_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
):
    """
    Récupérer un candidat.
    """
    candidate = db.query(User).filter(User.id == candidate_id, User.role == "candidate").first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    return candidate

@router.put("/{candidate_id}", response_model=UserResponse)
def update_candidate(
    *,
    db: Session = Depends(get_db),
    candidate_id: int,
    candidate_in: dict,
    current_user: User = Depends(get_current_active_user)
):
    """
    Mettre à jour un candidat.
    """
    candidate = db.query(User).filter(User.id == candidate_id, User.role == "candidate").first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    
    # Mise à jour des champs autorisés
    for field, value in candidate_in.items():
        if field in ["first_name", "last_name", "phone"]:
            setattr(candidate, field, value)
    
    db.commit()
    db.refresh(candidate)
    return candidate

@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(
    *,
    db: Session = Depends(get_db),
    candidate_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprimer un candidat.
    """
    candidate = db.query(User).filter(User.id == candidate_id, User.role == "candidate").first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    
    db.delete(candidate)
    db.commit()
    return None 