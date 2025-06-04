from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.schemas.candidate import CandidateCreate, CandidateUpdate

def get_candidate(db: Session, candidate_id: int) -> Optional[Candidate]:
    return db.query(Candidate).filter(Candidate.id == candidate_id).first()

def get_candidate_by_email(db: Session, email: str) -> Optional[Candidate]:
    return db.query(Candidate).filter(Candidate.email == email).first()

def get_candidates(
    db: Session, skip: int = 0, limit: int = 100
) -> List[Candidate]:
    return db.query(Candidate).offset(skip).limit(limit).all()

def create_candidate(db: Session, candidate: CandidateCreate) -> Candidate:
    db_candidate = Candidate(
        **candidate.model_dump(),
        is_active=True
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

def update_candidate(
    db: Session, candidate_id: int, candidate: CandidateUpdate
) -> Optional[Candidate]:
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        return None
    
    update_data = candidate.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_candidate, field, value)
    
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

def delete_candidate(db: Session, candidate_id: int) -> bool:
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        return False
    
    db.delete(db_candidate)
    db.commit()
    return True 