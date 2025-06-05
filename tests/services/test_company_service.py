import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
from unittest.mock import Mock, patch
from app.services.company_service import CompanyService

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def company_service():
    return CompanyService()

def test_get_all_companies_empty(company_service, mock_db):
    # Mock de la requête de base de données
    mock_db.query.return_value.order_by.return_value.all.return_value = []
    
    result = company_service.get_all_companies(mock_db)
    assert result["total"] == 0
    assert isinstance(result["data"], list)
    assert result["message"] == "Found 0 companies"

def test_get_all_companies_with_data(company_service, mock_db):
    # Création de données mockées
    mock_company = Mock()
    mock_company.id = 1
    mock_company.name = "Test Company"
    mock_company.city = "Paris"
    mock_company.country = "France"
    mock_company.email = "test@company.com"
    mock_company.phone = "0123456789"
    mock_company.created_at = "2024-03-20T10:00:00"
    mock_company.updated_at = "2024-03-20T10:00:00"
    
    # Mock de la requête de base de données
    mock_db.query.return_value.order_by.return_value.all.return_value = [mock_company]
    
    result = company_service.get_all_companies(mock_db)
    assert result["total"] == 1
    assert len(result["data"]) == 1
    assert result["data"][0]["name"] == "Test Company"
    assert result["message"] == "Found 1 companies" 