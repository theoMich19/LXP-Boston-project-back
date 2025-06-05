from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.schemas.applications import ApplicationCreate, ApplicationStatus
from app.db.model import Application, JobOffer, User, Company, CV
import uuid


class ApplicationService:
    """Service pour la gestion des candidatures"""

    def __init__(self):
        pass

    def _validate_job_offer_exists(self, db: Session, job_offer_id: str) -> JobOffer:
        """Vérifier que l'offre d'emploi existe et est active"""
        try:
            # Convertir en UUID si nécessaire
            if isinstance(job_offer_id, str):
                job_offer_uuid = uuid.UUID(job_offer_id)
            else:
                job_offer_uuid = job_offer_id

            job_offer = db.query(JobOffer).filter(JobOffer.id == job_offer_uuid).first()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format d'ID d'offre invalide"
            )

        if not job_offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offre d'emploi non trouvée"
            )

        if job_offer.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cette offre d'emploi n'est plus active"
            )

        return job_offer

    def _validate_user_is_candidate(self, db: Session, user_id: str) -> User:
        """Vérifier que l'utilisateur est bien un candidat"""
        try:
            # Convertir en UUID si nécessaire
            if isinstance(user_id, str):
                user_uuid = uuid.UUID(user_id)
            else:
                user_uuid = user_id

            user = db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format d'ID utilisateur invalide"
            )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé"
            )

        if user.role != "candidate":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les candidats peuvent postuler"
            )

        return user

    def _check_existing_application(self, db: Session, user_id: str, job_offer_id: str) -> None:
        """Vérifier si le candidat a déjà postulé à cette offre"""
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            job_offer_uuid = uuid.UUID(job_offer_id) if isinstance(job_offer_id, str) else job_offer_id

            existing_application = db.query(Application).filter(
                Application.user_id == user_uuid,
                Application.job_offer_id == job_offer_uuid
            ).first()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format d'ID invalide"
            )

        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vous avez déjà postulé à cette offre"
            )

    def _validate_hr_access_to_job(self, db: Session, hr_user: User, job_offer_id: str) -> JobOffer:
        """Vérifier qu'un utilisateur RH a accès à cette offre d'emploi"""
        if hr_user.role != "hr":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès réservé aux RH"
            )

        try:
            job_offer_uuid = uuid.UUID(job_offer_id) if isinstance(job_offer_id, str) else job_offer_id

            job_offer = db.query(JobOffer).filter(
                JobOffer.id == job_offer_uuid,
                JobOffer.company_id == hr_user.company_id
            ).first()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format d'ID d'offre invalide"
            )

        if not job_offer:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé à cette offre"
            )

        return job_offer

    def _validate_hr_access_to_application(self, db: Session, hr_user: User, application_id: int) -> Application:
        """Vérifier qu'un utilisateur RH a accès à cette candidature"""
        if hr_user.role != "hr":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès réservé aux RH"
            )

        application = db.query(Application).join(JobOffer).filter(
            Application.id == application_id,
            JobOffer.company_id == hr_user.company_id
        ).first()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé à cette candidature"
            )

        return application

    def _get_latest_cv_safely(self, db: Session, user_id: str) -> Optional[CV]:
        """Récupérer le CV le plus récent de manière sécurisée"""
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

            latest_cv = db.query(CV).filter(
                CV.user_id == user_uuid
            ).order_by(CV.upload_date.desc()).first()

            return latest_cv
        except Exception as e:
            print(f"Erreur lors de la récupération du CV pour l'utilisateur {user_id}: {e}")
            return None

    async def create_application(self, db: Session, application_data: ApplicationCreate, user_id: str) -> Dict[
        str, Any]:
        """
        Créer une nouvelle candidature

        Args:
            db: Session de base de données
            application_data: Données de la candidature
            user_id: ID du candidat (UUID string)

        Returns:
            Dictionnaire avec les informations de la candidature créée
        """
        try:
            # Validations
            user = self._validate_user_is_candidate(db, user_id)
            job_offer = self._validate_job_offer_exists(db, application_data.job_offer_id)
            self._check_existing_application(db, user_id, application_data.job_offer_id)

            # Convertir les IDs en UUID
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            job_offer_uuid = uuid.UUID(application_data.job_offer_id) if isinstance(application_data.job_offer_id,
                                                                                    str) else application_data.job_offer_id

            # Créer la candidature
            new_application = Application(
                user_id=user_uuid,
                job_offer_id=job_offer_uuid,
                status="pending"
            )

            db.add(new_application)
            db.commit()
            db.refresh(new_application)

            return {
                "id": new_application.id,
                "user_id": str(new_application.user_id),
                "job_offer_id": str(new_application.job_offer_id),
                "status": new_application.status,
                "applied_at": new_application.applied_at,
                "message": "Candidature envoyée avec succès"
            }

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la création de la candidature: {str(e)}"
            )

    async def get_candidate_applications(self, db: Session, user_id: str) -> List[Dict[str, Any]]:
        """
        Récupérer toutes les candidatures d'un candidat

        Args:
            db: Session de base de données
            user_id: ID du candidat (UUID string)

        Returns:
            Liste des candidatures avec informations des offres
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

            # Récupérer les candidatures du candidat
            applications = db.query(Application).filter(
                Application.user_id == user_uuid
            ).order_by(Application.applied_at.desc()).all()

            result = []
            for app in applications:
                # Récupérer les informations de l'offre et de la compagnie
                job_offer = db.query(JobOffer).filter(JobOffer.id == app.job_offer_id).first()
                if job_offer:
                    company = db.query(Company).filter(Company.id == job_offer.company_id).first()

                    result.append({
                        "id": app.id,
                        "user_id": str(app.user_id),
                        "job_offer_id": str(app.job_offer_id),
                        "status": app.status,
                        "applied_at": app.applied_at,
                        "job_title": job_offer.title,
                        "company_name": company.name if company else "N/A",
                        "job_salary_min": float(
                            job_offer.salary_min) if job_offer.salary_min and job_offer.salary_min.replace('.',
                                                                                                           '').isdigit() else None,
                        "job_salary_max": float(
                            job_offer.salary_max) if job_offer.salary_max and job_offer.salary_max.replace('.',
                                                                                                           '').isdigit() else None
                    })

            return result

        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format d'ID utilisateur invalide"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la récupération des candidatures: {str(e)}"
            )

    async def update_application_status(self, db: Session, application_id: int, new_status: ApplicationStatus,
                                        hr_user: User) -> Dict[str, Any]:
        """
        Mettre à jour le statut d'une candidature (RH uniquement)

        Args:
            db: Session de base de données
            application_id: ID de la candidature (integer)
            new_status: Nouveau statut
            hr_user: Utilisateur RH

        Returns:
            Dictionnaire avec les informations de la candidature mise à jour
        """
        try:
            # Vérifier l'accès RH à cette candidature
            application = self._validate_hr_access_to_application(db, hr_user, application_id)

            # Mettre à jour le statut
            application.status = new_status.value
            db.commit()
            db.refresh(application)

            return {
                "id": application.id,
                "user_id": str(application.user_id),
                "job_offer_id": str(application.job_offer_id),
                "status": application.status,
                "applied_at": application.applied_at,
                "message": "Statut de la candidature mis à jour avec succès"
            }

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la mise à jour: {str(e)}"
            )

    async def get_job_applications(self, db: Session, job_offer_id: str, hr_user: User,
                                   status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupérer toutes les candidatures pour une offre spécifique (RH uniquement)

        Args:
            db: Session de base de données
            job_offer_id: ID de l'offre d'emploi (UUID string)
            hr_user: Utilisateur RH
            status_filter: Filtre par statut (optionnel)

        Returns:
            Liste des candidatures avec informations des candidats
        """
        try:
            # Vérifier l'accès RH à cette offre
            job_offer = self._validate_hr_access_to_job(db, hr_user, job_offer_id)

            job_offer_uuid = uuid.UUID(job_offer_id) if isinstance(job_offer_id, str) else job_offer_id

            # Récupérer les candidatures pour cette offre
            query = db.query(Application).filter(Application.job_offer_id == job_offer_uuid)

            if status_filter:
                query = query.filter(Application.status == status_filter)

            applications = query.order_by(Application.applied_at.desc()).all()

            result = []
            for app in applications:
                # Récupérer les informations du candidat
                user = db.query(User).filter(User.id == app.user_id).first()
                if user:
                    # Récupérer le CV le plus récent du candidat de manière sécurisée
                    latest_cv = self._get_latest_cv_safely(db, str(app.user_id))

                    # Récupérer les informations de la compagnie
                    company = db.query(Company).filter(Company.id == job_offer.company_id).first()

                    result.append({
                        "id": app.id,
                        "user_id": str(app.user_id),
                        "job_offer_id": str(app.job_offer_id),
                        "status": app.status,
                        "applied_at": app.applied_at,
                        "candidate_first_name": user.first_name,
                        "candidate_last_name": user.last_name,
                        "candidate_email": user.email,
                        "cv_id": str(latest_cv.id) if latest_cv else None,
                        "cv_filename": latest_cv.original_filename if latest_cv else None,
                        "job_title": job_offer.title,
                        "company_name": company.name if company else "N/A"
                    })

            return result

        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format d'ID d'offre invalide"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la récupération des candidatures: {str(e)}"
            )


# Instance du service
application_service = ApplicationService()