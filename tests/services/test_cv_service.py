import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
from app.services.cv_service import CVService
from fastapi import UploadFile
from io import BytesIO

@pytest.fixture
def cv_service():
    return CVService()

def test_validate_file_extension_pdf(cv_service):
    class DummyUploadFile:
        def __init__(self, filename):
            self.filename = filename
    file = DummyUploadFile("cv.pdf")
    ext = cv_service._validate_file(file)
    assert ext == ".pdf"

def test_validate_file_extension_invalid(cv_service):
    class DummyUploadFile:
        def __init__(self, filename):
            self.filename = filename
    file = DummyUploadFile("cv.txt")
    with pytest.raises(Exception):
        cv_service._validate_file(file) 