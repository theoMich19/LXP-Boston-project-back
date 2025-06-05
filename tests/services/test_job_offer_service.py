import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
from unittest.mock import Mock, patch
from app.services.job_offer_service import JobOfferService

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def job_offer_service():
    return JobOfferService()

def test_get_all_job_offers_empty(job_offer_service, mock_db):
    # Mock de la requête de base de données
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    
    result = job_offer_service.get_all_job_offers(mock_db)
    assert result["total"] == 0
    assert isinstance(result["data"], list)
    assert result["message"] == "Found 0 active job offers"

def test_get_all_job_offers_with_data(job_offer_service, mock_db):
    # Création de données mockées
    mock_job = Mock()
    mock_job.id = 1
    mock_job.title = "Développeur Python"
    mock_job.description = "Description du poste"
    mock_job.company_id = 1
    mock_job.salary_min = 45000
    mock_job.salary_max = 65000
    mock_job.status = "active"
    mock_job.created_at = "2024-03-20T10:00:00"
    
    # Mock de la requête de base de données
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_job]
    
    result = job_offer_service.get_all_job_offers(mock_db)
    assert result["total"] == 1
    assert len(result["data"]) == 1
    assert result["data"][0]["title"] == "Développeur Python"
    assert result["message"] == "Found 1 active job offers" 