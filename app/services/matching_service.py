import json
import requests
from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging

from app.services.prompt.matching_prompts import MatchingPrompts

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for CV-Job matching using Gemini AI"""

    def __init__(self):
        self.gemini_api_key = "AIzaSyBlJYaJHITKvX-XGvIWXYe-htKlsVK9BH8"
        self.gemini_base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

        # Cache pour les résultats
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    def _call_gemini_api(self, prompt: str) -> str:
        """Call Gemini API for content generation"""
        try:
            headers = {
                "Content-Type": "application/json",
            }

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 1024,
                }
            }

            url = f"{self.gemini_base_url}?key={self.gemini_api_key}"
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                raise Exception(f"Gemini API error: {response.status_code}")

            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                raise Exception("No response from Gemini API")

        except requests.exceptions.Timeout:
            logger.error("Gemini API timeout")
            raise Exception("AI analysis timeout")
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise Exception(f"AI analysis failed: {str(e)}")

    def _analyze_cv_job_compatibility(self, cv_text: str, job_title: str, job_description: str) -> Dict[str, Any]:
        """Analyze CV-Job compatibility using Gemini AI"""

        # Generate prompt using the prompts module
        prompt = MatchingPrompts.get_cv_job_compatibility_prompt(cv_text, job_title, job_description)

        try:
            response_text = self._call_gemini_api(prompt)

            # Clean the response to extract JSON
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            # Parse JSON response
            analysis = json.loads(response_text)

            # Validate required fields and set defaults if missing
            return {
                "compatibility_score": max(0, min(100, analysis.get("compatibility_score", 0))),
                "matched_skills": analysis.get("matched_skills", [])[:10],  # Limit to 10
                "missing_skills": analysis.get("missing_skills", [])[:5],  # Limit to 5
                "analysis_summary": analysis.get("analysis_summary", "Analysis completed"),
                "strengths": analysis.get("strengths", [])[:5],
                "recommendations": analysis.get("recommendations", [])[:3]
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Response was: {response_text}")
            # Fallback to basic keyword matching
            return self._fallback_analysis(cv_text, job_title, job_description)
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            # Fallback to basic keyword matching
            return self._fallback_analysis(cv_text, job_title, job_description)

    def _fallback_analysis(self, cv_text: str, job_title: str, job_description: str) -> Dict[str, Any]:
        """Fallback analysis using basic keyword matching"""

        # Basic technical keywords
        tech_keywords = [
            'python', 'java', 'javascript', 'react', 'vue', 'angular', 'node.js',
            'docker', 'kubernetes', 'aws', 'azure', 'postgresql', 'mongodb',
            'machine learning', 'ai', 'data science', 'devops', 'agile', 'scrum'
        ]

        cv_lower = cv_text.lower()
        job_text_lower = f"{job_title} {job_description}".lower()

        matched_skills = []
        missing_skills = []

        for keyword in tech_keywords:
            if keyword in cv_lower and keyword in job_text_lower:
                matched_skills.append(keyword)
            elif keyword in job_text_lower and keyword not in cv_lower:
                missing_skills.append(keyword)

        # Basic score calculation
        if len(matched_skills) == 0:
            score = 0
        else:
            score = min(100, (len(matched_skills) * 15) + 10)

        return {
            "compatibility_score": score,
            "matched_skills": matched_skills[:10],
            "missing_skills": missing_skills[:5],
            "analysis_summary": "Basic keyword analysis completed",
            "strengths": matched_skills[:5],
            "recommendations": [f"Consider learning {skill}" for skill in missing_skills[:3]]
        }

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
        Get job matches for a user based on their CV using Gemini AI

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

            if not cv_text.strip():
                return {
                    "data": [],
                    "total": 0,
                    "user_skills": [],
                    "message": "No content found in your CV. Please ensure your CV contains readable text."
                }

            # Récupérer les offres d'emploi
            job_offers = self._get_job_offers(db)

            if not job_offers:
                return {
                    "data": [],
                    "total": 0,
                    "user_skills": [],
                    "message": "No active job offers available at the moment."
                }

            # Analyser chaque offre d'emploi avec Gemini AI
            matches = []
            all_user_skills = set()

            for job in job_offers:
                try:
                    # Utiliser Gemini AI pour analyser la compatibilité
                    analysis = self._analyze_cv_job_compatibility(
                        cv_text,
                        job['title'],
                        job['description']
                    )

                    score = analysis['compatibility_score']
                    matched_skills = analysis['matched_skills']
                    missing_skills = analysis['missing_skills']

                    # Ajouter les compétences détectées de l'utilisateur
                    all_user_skills.update(matched_skills)

                    # Ne garder que les matches avec un score minimum
                    if score >= 15:  # Score minimum de 15%
                        matches.append({
                            "id": job['id'],
                            "title": job['title'],
                            "company_name": job['company_name'],
                            "company_id": job['company_id'],
                            "compatibility_score": score,
                            "matched_skills": matched_skills,
                            "missing_skills": missing_skills,
                            "salary_min": job['salary_min'],
                            "salary_max": job['salary_max'],
                            "description": self._create_description_preview(job['description']),
                            "created_at": job['created_at']
                        })

                except Exception as e:
                    logger.error(f"Error analyzing job {job['id']}: {e}")
                    # Continue with next job if one fails
                    continue

            # Trier par score de compatibilité (décroissant)
            matches.sort(key=lambda x: x['compatibility_score'], reverse=True)

            # Limiter le nombre de résultats
            top_matches = matches[:limit]

            result = {
                "data": top_matches,
                "total": len(matches),
                "user_skills": list(all_user_skills),
                "message": f"Found {len(matches)} job matches using AI-powered analysis."
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
                detail="Error during AI-powered job matching analysis"
            )

    def get_match_stats(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get matching statistics for a user"""
        try:
            cv_data = self._get_user_cv_data(db, user_id)
            matches_result = self.get_job_matches(db, user_id, limit=100)  # Get all matches for stats

            matches = matches_result['data']

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