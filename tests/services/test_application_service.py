import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
from app.services.application_service import ApplicationService

@pytest.fixture
def application_service():
    return ApplicationService()

def test_application_service_init(application_service):
    assert isinstance(application_service, ApplicationService) 