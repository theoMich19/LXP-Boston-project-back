from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.schemas.applications import ApplicationCreate, ApplicationStatus
from app.db.model import Application, JobOffer, User, Company, CV


class ApplicationService:
    """Service for application management - Integer IDs version"""

    def __init__(self):
        pass

    def _validate_job_offer_exists(self, db: Session, job_offer_id: int) -> JobOffer:
        """Validate that the job offer exists and is active"""
        job_offer = db.query(JobOffer).filter(JobOffer.id == job_offer_id).first()

        if not job_offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job offer not found"
            )

        if job_offer.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This job offer is no longer active"
            )

        return job_offer

    def _validate_user_is_candidate(self, db: Session, user_id: int) -> User:
        """Validate that the user is a candidate"""
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.role != "candidate":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only candidates can apply"
            )

        return user

    def _check_existing_application(self, db: Session, user_id: int, job_offer_id: int) -> None:
        """Check if the candidate has already applied to this offer"""
        existing_application = db.query(Application).filter(
            Application.user_id == user_id,
            Application.job_offer_id == job_offer_id
        ).first()

        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already applied to this offer"
            )

    def _validate_hr_access_to_job(self, db: Session, hr_user: User, job_offer_id: int) -> JobOffer:
        """Validate that an HR user has access to this job offer"""
        if hr_user.role != "hr":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access restricted to HR"
            )

        job_offer = db.query(JobOffer).filter(
            JobOffer.id == job_offer_id,
            JobOffer.company_id == hr_user.company_id
        ).first()

        if not job_offer:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to this offer"
            )

        return job_offer

    def _validate_hr_access_to_application(self, db: Session, hr_user: User, application_id: int) -> Application:
        """Validate that an HR user has access to this application"""
        if hr_user.role != "hr":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access restricted to HR"
            )

        application = db.query(Application).join(JobOffer).filter(
            Application.id == application_id,
            JobOffer.company_id == hr_user.company_id
        ).first()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to this application"
            )

        return application

    def _get_latest_cv_safely(self, db: Session, user_id: int) -> Optional[CV]:
        """Get the latest CV safely"""
        try:
            latest_cv = db.query(CV).filter(
                CV.user_id == user_id
            ).order_by(CV.upload_date.desc()).first()

            return latest_cv
        except Exception as e:
            print(f"Error retrieving CV for user {user_id}: {e}")
            return None

    async def create_application(self, db: Session, application_data: ApplicationCreate, user_id: int) -> Dict[
        str, Any]:
        """
        Créer une nouvelle candidature

        Args:
            db: Session de base de données
            application_data: Données de la candidature
            user_id: ID du candidat (integer)

        Returns:
            Dictionnaire avec les informations de la candidature créée
        """
        try:
            # Validations
            user = self._validate_user_is_candidate(db, user_id)
            job_offer = self._validate_job_offer_exists(db, application_data.job_offer_id)
            self._check_existing_application(db, user_id, application_data.job_offer_id)

            # Créer la candidature
            new_application = Application(
                user_id=user_id,
                job_offer_id=application_data.job_offer_id,
                status="pending"
            )

            db.add(new_application)
            db.commit()
            db.refresh(new_application)

            return {
                "id": new_application.id,
                "user_id": new_application.user_id,
                "job_offer_id": new_application.job_offer_id,
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

    async def get_candidate_applications(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Récupérer toutes les candidatures d'un candidat

        Args:
            db: Session de base de données
            user_id: ID du candidat (integer)

        Returns:
            Liste des candidatures avec informations des offres
        """
        try:
            # Récupérer les candidatures du candidat
            applications = db.query(Application).filter(
                Application.user_id == user_id
            ).order_by(Application.applied_at.desc()).all()

            result = []
            for app in applications:
                # Récupérer les informations de l'offre et de la compagnie
                job_offer = db.query(JobOffer).filter(JobOffer.id == app.job_offer_id).first()
                if job_offer:
                    company = db.query(Company).filter(Company.id == job_offer.company_id).first()

                    # Conversion sécurisée des salaires
                    salary_min = None
                    salary_max = None

                    if job_offer.salary_min:
                        try:
                            salary_min = float(job_offer.salary_min)
                        except (ValueError, TypeError):
                            salary_min = None

                    if job_offer.salary_max:
                        try:
                            salary_max = float(job_offer.salary_max)
                        except (ValueError, TypeError):
                            salary_max = None

                    result.append({
                        "id": app.id,
                        "user_id": app.user_id,
                        "job_offer_id": app.job_offer_id,
                        "status": app.status,
                        "applied_at": app.applied_at,
                        "job_title": job_offer.title,
                        "company_name": company.name if company else "N/A",
                        "job_salary_min": salary_min,
                        "job_salary_max": salary_max
                    })

            return result

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la récupération des candidatures: {str(e)}"
            )

    async def update_application_status(self, db: Session, application_id: int, new_status: ApplicationStatus,
                                        hr_user: User) -> Dict[str, Any]:
        """
        Update application status (HR only)

        Args:
            db: Database session
            application_id: Application ID (integer)
            new_status: New status
            hr_user: HR user

        Returns:
            Dictionary with updated application information
        """
        try:
            # Validate HR access to this application
            application = self._validate_hr_access_to_application(db, hr_user, application_id)

            # Update status
            application.status = new_status.value
            db.commit()
            db.refresh(application)

            return {
                "id": application.id,
                "user_id": application.user_id,
                "job_offer_id": application.job_offer_id,
                "status": application.status,
                "applied_at": application.applied_at,
                "message": "Application status updated successfully"
            }

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating application: {str(e)}"
            )

    async def get_job_applications(self, db: Session, job_offer_id: int, hr_user: User,
                                   status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all applications for a specific job offer (HR only)

        Args:
            db: Database session
            job_offer_id: Job offer ID (integer)
            hr_user: HR user
            status_filter: Status filter (optional)

        Returns:
            List of applications with candidate information
        """
        try:
            # Validate HR access to this job offer
            job_offer = self._validate_hr_access_to_job(db, hr_user, job_offer_id)

            # Get applications for this job offer
            query = db.query(Application).filter(Application.job_offer_id == job_offer_id)

            if status_filter:
                query = query.filter(Application.status == status_filter)

            applications = query.order_by(Application.applied_at.desc()).all()

            result = []
            for app in applications:
                # Get candidate information
                user = db.query(User).filter(User.id == app.user_id).first()
                if user:
                    # Get candidate's latest CV safely
                    latest_cv = self._get_latest_cv_safely(db, app.user_id)

                    # Get company information
                    company = db.query(Company).filter(Company.id == job_offer.company_id).first()

                    result.append({
                        "id": app.id,
                        "user_id": app.user_id,
                        "job_offer_id": app.job_offer_id,
                        "status": app.status,
                        "applied_at": app.applied_at,
                        "candidate_first_name": user.first_name,
                        "candidate_last_name": user.last_name,
                        "candidate_email": user.email,
                        "cv_id": latest_cv.id if latest_cv else None,
                        "cv_filename": latest_cv.original_filename if latest_cv else None,
                        "job_title": job_offer.title,
                        "company_name": company.name if company else "N/A"
                    })

            return result

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving job applications: {str(e)}"
            )


# Instance du service
application_service = ApplicationService()