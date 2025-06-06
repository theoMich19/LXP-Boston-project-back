import json
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import google.generativeai as genai

from app.services.prompt.matching_prompts import MatchingPrompts

logger = logging.getLogger(__name__)


class GeminiMatchingService:
    """Service for CV-Job matching using Google Generative AI"""

    def __init__(self):
        self.api_key = "AIzaSyBlJYaJHITKvX-XGvIWXYe-htKlsVK9BH8"

        # Configure Gemini client
        self.client = genai.configure(api_key=self.api_key)

        # Cache optimisé
        self._cache = {}
        self._cache_ttl = 1800  # 30 minutes
        self._job_cache = {}
        self._job_cache_ttl = 600  # 10 minutes

        # Pool de threads pour traitement parallèle
        self.executor = ThreadPoolExecutor(max_workers=3)

    def _get_cache_key(self, *args) -> str:
        """Generate a cache key from arguments"""
        key_string = "_".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _is_cache_valid(self, cache_entry: Dict, ttl: int) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False
        return (datetime.now() - cache_entry['timestamp']).seconds < ttl

    def _call_gemini_api(self, prompt: str) -> str:
        """Call Gemini API using the official library"""
        try:
            # Generate content using the official library
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            return response.text

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise Exception(f"AI analysis failed: {str(e)}")

    def _analyze_single_job(self, cv_text: str, job: Dict) -> Dict[str, Any]:
        """Analyze a single job with caching"""

        # Vérifier le cache d'abord
        cache_key = self._get_cache_key(cv_text[:100], job['id'], job['title'])
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry, self._cache_ttl):
                return cache_entry['data']

        try:
            # Utiliser le prompt optimisé
            prompt = MatchingPrompts.get_optimized_cv_job_compatibility_prompt(
                cv_text, job['title'], job['description']
            )

            response_text = self._call_gemini_api(prompt)

            # Clean and parse response
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            analysis = json.loads(response_text)

            result = {
                "id": job['id'],
                "title": job['title'],
                "company_name": job['company_name'],
                "company_id": job['company_id'],
                "compatibility_score": max(0, min(100, analysis.get("compatibility_score", 0))),
                "matched_skills": analysis.get("matched_skills", [])[:8],
                "missing_skills": analysis.get("missing_skills", [])[:3],
                "salary_min": job['salary_min'],
                "salary_max": job['salary_max'],
                "description": self._create_description_preview(job['description']),
                "created_at": job['created_at'],
                "analysis_summary": analysis.get("analysis_summary", "Analysis completed")
            }

            # Mettre en cache
            self._cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }

            return result

        except Exception as e:
            logger.error(f"Analysis failed for job {job['id']}: {e}")
            # Fallback rapide
            return self._quick_fallback_analysis(cv_text, job)

    def _analyze_jobs_parallel(self, cv_text: str, jobs: List[Dict], max_workers: int = 3) -> List[Dict]:
        """Analyze multiple jobs in parallel using ThreadPoolExecutor"""

        valid_results = []

        # Limiter le nombre de jobs à analyser pour éviter la surcharge
        jobs_to_analyze = jobs[:20]  # Analyser max 20 jobs

        # Découper en batches pour éviter de surcharger l'API
        batch_size = 5

        for i in range(0, len(jobs_to_analyze), batch_size):
            batch = jobs_to_analyze[i:i + batch_size]

            # Analyser le batch en parallèle
            with ThreadPoolExecutor(max_workers=min(max_workers, len(batch))) as executor:
                # Soumettre les tâches
                future_to_job = {
                    executor.submit(self._analyze_single_job, cv_text, job): job
                    for job in batch
                }

                # Récupérer les résultats
                for future in as_completed(future_to_job):
                    job = future_to_job[future]
                    try:
                        result = future.result(timeout=20)  # Timeout par job
                        if result and result.get('compatibility_score', 0) >= 15:
                            valid_results.append(result)
                    except Exception as e:
                        logger.error(f"Error analyzing job {job['id']}: {e}")
                        continue

            # Pause entre les batches pour respecter les limites de l'API
            if i + batch_size < len(jobs_to_analyze):
                time.sleep(1)  # 1 seconde de pause

        return valid_results

    def _quick_fallback_analysis(self, cv_text: str, job: Dict) -> Dict[str, Any]:
        """Quick fallback analysis without AI"""
        tech_keywords = [
            'python', 'java', 'javascript', 'react', 'vue', 'angular', 'node.js',
            'docker', 'kubernetes', 'aws', 'azure', 'postgresql', 'mongodb',
            'django', 'flask', 'spring', 'laravel', 'git', 'linux'
        ]

        cv_lower = cv_text.lower()
        job_text_lower = f"{job['title']} {job['description']}".lower()

        matched_skills = [kw for kw in tech_keywords if kw in cv_lower and kw in job_text_lower]
        missing_skills = [kw for kw in tech_keywords if kw in job_text_lower and kw not in cv_lower]

        score = min(85, len(matched_skills) * 12 + 10) if matched_skills else 0

        return {
            "id": job['id'],
            "title": job['title'],
            "company_name": job['company_name'],
            "company_id": job['company_id'],
            "compatibility_score": score,
            "matched_skills": matched_skills[:8],
            "missing_skills": missing_skills[:3],
            "salary_min": job['salary_min'],
            "salary_max": job['salary_max'],
            "description": self._create_description_preview(job['description']),
            "created_at": job['created_at'],
            "analysis_summary": "Quick keyword analysis"
        }

    def _get_user_cv_data(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get user's CV data with caching using ORM"""
        cache_key = f"cv_{user_id}"
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry, self._cache_ttl):
                return cache_entry['data']

        try:
            from app.db.model import CV

            cv = db.query(CV).filter(
                CV.user_id == user_id
            ).order_by(CV.upload_date.desc()).first()

            if not cv:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No CV found for user. Please upload a CV first."
                )

            cv_data = {
                'id': cv.id,
                'parsed_data': cv.parsed_data or {},
                'filename': cv.original_filename,
                'upload_date': cv.upload_date
            }

            raw_text = cv_data['parsed_data'].get('raw_text', '')
            if not raw_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CV text could not be parsed. Please re-upload your CV."
                )

            # Cache the result
            self._cache[cache_key] = {
                'data': cv_data,
                'timestamp': datetime.now()
            }

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
        """Get all active job offers with enhanced caching using ORM"""
        cache_key = "active_jobs"
        if cache_key in self._job_cache:
            cache_entry = self._job_cache[cache_key]
            if self._is_cache_valid(cache_entry, self._job_cache_ttl):
                return cache_entry['data']

        try:
            from app.db.model import JobOffer, Company

            job_offers_query = db.query(
                JobOffer.id,
                JobOffer.title,
                JobOffer.description,
                JobOffer.company_id,
                JobOffer.salary_min,
                JobOffer.salary_max,
                JobOffer.created_at,
                Company.name.label('company_name')
            ).join(
                Company, JobOffer.company_id == Company.id
            ).filter(
                JobOffer.status == 'active'
            ).order_by(
                JobOffer.created_at.desc()
            ).limit(50)

            results = job_offers_query.all()

            jobs = []
            for row in results:
                jobs.append({
                    'id': row.id,
                    'title': row.title,
                    'description': row.description or '',
                    'company_id': row.company_id,
                    'salary_min': row.salary_min,
                    'salary_max': row.salary_max,
                    'created_at': row.created_at,
                    'company_name': row.company_name
                })

            # Cache the result
            self._job_cache[cache_key] = {
                'data': jobs,
                'timestamp': datetime.now()
            }

            return jobs

        except Exception as e:
            logger.error(f"Error getting job offers: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving job offers"
            )

    def _create_description_preview(self, description: str, max_length: int = 120) -> str:
        """Create a shorter preview of the job description"""
        if not description:
            return "No description available"

        if len(description) <= max_length:
            return description

        preview = description[:max_length]
        last_space = preview.rfind(' ')

        if last_space > max_length * 0.7:
            return preview[:last_space] + "..."
        else:
            return preview + "..."

    def get_job_matches(self, db: Session, user_id: int, limit: int = 10) -> Dict[str, Any]:
        """Get job matches for a user using optimized parallel processing with Gemini"""

        # Vérifier le cache
        cache_key = f"matches_{user_id}_{limit}"
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry, self._cache_ttl):
                return cache_entry['data']

        try:
            # Récupérer les données
            cv_data = self._get_user_cv_data(db, user_id)
            job_offers = self._get_job_offers(db)

            cv_text = cv_data['parsed_data'].get('raw_text', '')

            if not cv_text.strip():
                return {
                    "data": [],
                    "total": 0,
                    "user_skills": [],
                    "message": "No content found in your CV."
                }

            if not job_offers:
                return {
                    "data": [],
                    "total": 0,
                    "user_skills": [],
                    "message": "No active job offers available."
                }

            # Analyser en parallèle
            matches = self._analyze_jobs_parallel(cv_text, job_offers)

            # Trier et limiter
            matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
            top_matches = matches[:limit]

            # Extraire les compétences utilisateur
            all_user_skills = set()
            for match in top_matches:
                all_user_skills.update(match.get('matched_skills', []))

            result = {
                "data": top_matches,
                "total": len(matches),
                "user_skills": list(all_user_skills),
                "message": f"Found {len(matches)} job matches using Gemini AI analysis."
            }

            # Mettre en cache
            self._cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }

            return result

        except Exception as e:
            logger.error(f"Error in job matching for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error during AI-powered job matching analysis"
            )

    def get_match_stats(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get matching statistics for a user using ORM"""
        try:
            cv_data = self._get_user_cv_data(db, user_id)
            matches_result = self.get_job_matches(db, user_id, limit=100)

            matches = matches_result['data']

            from app.db.model import JobOffer
            total_jobs = db.query(JobOffer).filter(JobOffer.status == 'active').count()

            if not matches:
                return {
                    "total_jobs_analyzed": total_jobs,
                    "matches_found": 0,
                    "average_score": 0,
                    "top_score": 0,
                    "user_cv_id": cv_data['id'],
                    "analysis_date": datetime.now().isoformat()
                }

            scores = [match['compatibility_score'] for match in matches]

            return {
                "total_jobs_analyzed": total_jobs,
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

    def clear_cache(self):
        """Clear all caches"""
        self._cache.clear()
        self._job_cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        return {
            "main_cache_size": len(self._cache),
            "job_cache_size": len(self._job_cache),
            "cache_ttl": self._cache_ttl,
            "job_cache_ttl": self._job_cache_ttl
        }


# Service instance
matching_service = GeminiMatchingService()