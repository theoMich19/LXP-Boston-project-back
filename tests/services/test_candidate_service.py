import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
from unittest.mock import Mock, patch
from app.services import candidate

@pytest.fixture
def mock_db():
    return Mock()

def test_get_candidates_empty(mock_db):
    # Mock de la requête de base de données
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []
    
    result = candidate.get_candidates(mock_db)
    assert isinstance(result, list)
    assert len(result) == 0

def test_get_candidates_with_data(mock_db):
    # Création de données mockées
    mock_candidate = Mock()
    mock_candidate.id = 1
    mock_candidate.email = "test@example.com"
    mock_candidate.first_name = "John"
    mock_candidate.last_name = "Doe"
    mock_candidate.is_active = True
    
    # Mock de la requête de base de données
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [mock_candidate]
    
    result = candidate.get_candidates(mock_db)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].email == "test@example.com" 