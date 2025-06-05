import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
from app.services.matching_service import MatchingService

@pytest.fixture
def matching_service():
    return MatchingService()

def test_fallback_analysis(matching_service):
    cv_text = "python java"
    job_title = "Développeur"
    job_description = "Nous recherchons un développeur python et java."
    result = matching_service._fallback_analysis(cv_text, job_title, job_description)
    assert "compatibility_score" in result
    assert isinstance(result["matched_skills"], list) 