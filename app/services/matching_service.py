import re
from typing import List, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for CV-Job matching"""

    def __init__(self):
        # Mots-clés techniques avec leurs poids
        self.skill_keywords = {
            # Languages de programmation
            'python': 3.0, 'java': 3.0, 'javascript': 3.0, 'typescript': 2.5,
            'php': 2.5, 'c++': 3.0, 'c#': 2.5, 'go': 2.5, 'rust': 2.5,
            'ruby': 2.5, 'swift': 2.5, 'kotlin': 2.5, 'scala': 2.5,

            # Frameworks
            'react': 2.5, 'vue': 2.5, 'angular': 2.5, 'django': 2.5,
            'flask': 2.0, 'fastapi': 2.5, 'spring': 2.5, 'laravel': 2.0,
            'express': 2.0, 'nodejs': 2.5, 'node.js': 2.5,

            # Bases de données
            'postgresql': 2.0, 'mysql': 2.0, 'mongodb': 2.0, 'redis': 2.0,
            'elasticsearch': 2.0, 'sqlite': 1.5, 'oracle': 2.0,

            # DevOps & Cloud
            'docker': 2.5, 'kubernetes': 3.0, 'aws': 3.0, 'azure': 2.5,
            'gcp': 2.5, 'terraform': 2.5, 'jenkins': 2.0, 'gitlab': 1.5,
            'github': 1.5, 'ci/cd': 2.0,

            # Frontend
            'html': 1.5, 'css': 1.5, 'sass': 1.5, 'tailwind': 1.5,
            'bootstrap': 1.0, 'webpack': 2.0, 'vite': 1.5,

            # Outils
            'git': 1.5, 'jira': 1.0, 'agile': 1.5, 'scrum': 1.5,
            'rest': 1.5, 'api': 1.5, 'graphql': 2.0, 'microservices': 2.5,

            # Concepts
            'machine learning': 3.0, 'ai': 2.5, 'data science': 3.0,
            'blockchain': 2.5, 'iot': 2.0, 'mobile': 2.0,
        }

        # Cache simple pour les résultats
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    def _extract_skills_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract skills from text with weights"""
        if not text:
            return []

        text_lower = text.lower()
        found_skills = []

        for skill, weight in self.skill_keywords.items():
            # Recherche avec regex pour éviter les faux positifs
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            matches = re.findall(pattern, text_lower)

            if matches:
                # Compter les occurrences pour ajuster le poids
                occurrences = len(matches)
                adjusted_weight = weight * min(occurrences, 3)  # Max 3x le poids

                found_skills.append({
                    'skill': skill,
                    'weight': adjusted_weight,
                    'occurrences': occurrences
                })

        return found_skills

    def _get_user_cv_data(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get user's CV data"""
        try:
            # Récupérer le CV le plus récent de l'utilisateur
            result = db.execute(
                text("""
                     SELECT id, parsed_data, original_filename, upload_date
                     FROM cvs
                     WHERE user_id = :user_id
                     ORDER BY upload_date DESC LIMIT 1
                     """),
                {"user_id": user_id}
            ).fetchone()

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No CV found for user. Please upload a CV first."
                )

            cv_data = {
                'id': result[0],
                'parsed_data': result[1] or {},
                'filename': result[2],
                'upload_date': result[3]
            }

            # Extraire le texte du CV
            raw_text = cv_data['parsed_data'].get('raw_text', '')
            if not raw_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CV text could not be parsed. Please re-upload your CV."
                )

            return cv_data

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting CV data for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving CV data"
            )

    def _get_job_offers(self, db: Session) -> List[Dict[str, Any]]:
        """Get all active job offers with company names"""
        try:
            result = db.execute(
                text("""
                     SELECT jo.id,
                            jo.title,
                            jo.description,
                            jo.company_id,
                            jo.salary_min,
                            jo.salary_max,
                            jo.created_at,
                            c.name as company_name
                     FROM job_offers jo
                              JOIN companies c ON jo.company_id = c.id
                     WHERE jo.status = 'active'
                     ORDER BY jo.created_at DESC
                     """)
            ).fetchall()

            jobs = []
            for row in result:
                jobs.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2] or '',
                    'company_id': row[3],
                    'salary_min': row[4],
                    'salary_max': row[5],
                    'created_at': row[6],
                    'company_name': row[7]
                })

            return jobs

        except Exception as e:
            logger.error(f"Error getting job offers: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving job offers"
            )

    def _calculate_compatibility_score(self, cv_skills: List[Dict], job_skills: List[Dict]) -> Tuple[
        int, List[str], List[str]]:
        """Calculate compatibility score between CV and job"""

        # Convertir en dictionnaires pour faciliter les comparaisons
        cv_skill_dict = {skill['skill']: skill['weight'] for skill in cv_skills}
        job_skill_dict = {skill['skill']: skill['weight'] for skill in job_skills}

        matched_skills = []
        cv_skill_names = set(cv_skill_dict.keys())
        job_skill_names = set(job_skill_dict.keys())

        # Compétences correspondantes
        matched_skill_names = cv_skill_names.intersection(job_skill_names)

        total_score = 0
        max_possible_score = 0

        # Calculer le score basé sur les compétences correspondantes
        for skill in job_skill_names:
            job_weight = job_skill_dict[skill]
            max_possible_score += job_weight

            if skill in matched_skill_names:
                cv_weight = cv_skill_dict[skill]
                # Score = moyenne pondérée entre CV et job
                skill_score = (cv_weight + job_weight) / 2
                total_score += skill_score
                matched_skills.append(skill)

        # Compétences manquantes (dans le job mais pas dans le CV)
        missing_skills = list(job_skill_names - cv_skill_names)

        # Calculer le pourcentage de compatibilité
        if max_possible_score > 0:
            compatibility_percentage = min(100, int((total_score / max_possible_score) * 100))
        else:
            compatibility_percentage = 0

        return compatibility_percentage, matched_skills, missing_skills

    def _create_description_preview(self, description: str, max_length: int = 150) -> str:
        """Create a preview of the job description"""
        if not description:
            return "No description available"

        if len(description) <= max_length:
            return description

        # Couper à la phrase complète la plus proche
        preview = description[:max_length]
        last_sentence = preview.rfind('.')

        if last_sentence > max_length * 0.7:  # Si on trouve un point pas trop loin
            return preview[:last_sentence + 1]
        else:
            return preview + "..."

    def get_job_matches(self, db: Session, user_id: int, limit: int = 10) -> Dict[str, Any]:
        """
        Get job matches for a user based on their CV

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of matches to return

        Returns:
            Dictionary with matches and statistics
        """

        # Vérifier le cache
        cache_key = f"matches_{user_id}_{limit}"
        if cache_key in self._cache:
            cache_data = self._cache[cache_key]
            if (datetime.now() - cache_data['timestamp']).seconds < self._cache_ttl:
                return cache_data['data']

        try:
            # Récupérer les données du CV utilisateur
            cv_data = self._get_user_cv_data(db, user_id)
            cv_text = cv_data['parsed_data'].get('raw_text', '')

            # Extraire les compétences du CV
            cv_skills = self._extract_skills_from_text(cv_text)
            cv_skill_names = [skill['skill'] for skill in cv_skills]

            if not cv_skills:
                return {
                    "data": [],
                    "total": 0,
                    "user_skills": [],
                    "message": "No skills detected in your CV. Please ensure your CV contains technical skills and experience."
                }

            # Récupérer les offres d'emploi
            job_offers = self._get_job_offers(db)

            if not job_offers:
                return {
                    "data": [],
                    "total": 0,
                    "user_skills": cv_skill_names,
                    "message": "No active job offers available at the moment."
                }

            # Analyser chaque offre d'emploi
            matches = []

            for job in job_offers:
                # Combiner titre et description pour l'analyse
                job_text = f"{job['title']} {job['description']}"
                job_skills = self._extract_skills_from_text(job_text)

                # Calculer le score de compatibilité
                score, matched_skills, missing_skills = self._calculate_compatibility_score(
                    cv_skills, job_skills
                )

                # Ne garder que les matches avec un score minimum
                if score >= 10:  # Score minimum de 10%
                    matches.append({
                        "id": job['id'],  # Changé de job_id à id
                        "title": job['title'],
                        "company_name": job['company_name'],
                        "company_id": job['company_id'],
                        "compatibility_score": score,
                        "matched_skills": matched_skills,
                        "missing_skills": missing_skills[:5],  # Limiter à 5 compétences manquantes
                        "salary_min": job['salary_min'],
                        "salary_max": job['salary_max'],
                        "description": self._create_description_preview(job['description']),
                        # Changé de description_preview à description
                        "created_at": job['created_at']  # Ajouté created_at
                    })

            # Trier par score de compatibilité (décroissant)
            matches.sort(key=lambda x: x['compatibility_score'], reverse=True)

            # Limiter le nombre de résultats
            top_matches = matches[:limit]

            result = {
                "data": top_matches,
                "total": len(matches),
                "user_skills": cv_skill_names,
                "message": f"Found {len(matches)} job matches based on your CV analysis."
            }

            # Mettre en cache
            self._cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }

            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in job matching for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error during job matching analysis"
            )

    def get_match_stats(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get matching statistics for a user"""
        try:
            cv_data = self._get_user_cv_data(db, user_id)
            matches_result = self.get_job_matches(db, user_id, limit=100)  # Get all matches for stats

            matches = matches_result['matches']

            if not matches:
                return {
                    "total_jobs_analyzed": len(self._get_job_offers(db)),
                    "matches_found": 0,
                    "average_score": 0,
                    "top_score": 0,
                    "user_cv_id": cv_data['id'],
                    "analysis_date": datetime.now().isoformat()
                }

            scores = [match['compatibility_score'] for match in matches]

            return {
                "total_jobs_analyzed": len(self._get_job_offers(db)),
                "matches_found": len(matches),
                "average_score": round(sum(scores) / len(scores), 1),
                "top_score": max(scores),
                "user_cv_id": cv_data['id'],
                "analysis_date": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting match stats for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving match statistics"
            )


# Service instance
matching_service = MatchingService()