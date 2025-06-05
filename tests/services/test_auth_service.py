import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.auth_service import AuthService, User, Base

# Configuration de la base de données de test
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_service():
    return AuthService()

def test_verify_password(auth_service):
    # Test de vérification de mot de passe
    plain_password = "testpassword123"
    hashed_password = auth_service.get_password_hash(plain_password)
    
    assert auth_service.verify_password(plain_password, hashed_password) is True
    assert auth_service.verify_password("wrongpassword", hashed_password) is False

def test_create_access_token(auth_service):
    # Test de création de token
    data = {"sub": "test@example.com"}
    token = auth_service.create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)

def test_verify_token(auth_service):
    # Test de vérification de token
    data = {"sub": "test@example.com"}
    token = auth_service.create_access_token(data)
    
    payload = auth_service.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "test@example.com"
    
    # Test avec un token invalide
    assert auth_service.verify_token("invalid_token") is None

def test_create_user(auth_service, db_session):
    # Test de création d'utilisateur
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "role": "candidate"
    }
    
    user = auth_service.create_user(
        db=db_session,
        email=user_data["email"],
        password=user_data["password"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        role=user_data["role"]
    )
    
    assert user is not None
    assert user.email == user_data["email"]
    assert user.first_name == user_data["first_name"]
    assert user.last_name == user_data["last_name"]
    assert user.role == user_data["role"]
    
    # Test de création d'utilisateur avec email existant
    with pytest.raises(Exception):
        auth_service.create_user(
            db=db_session,
            email=user_data["email"],
            password=user_data["password"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            role=user_data["role"]
        )

def test_authenticate_user(auth_service, db_session):
    # Création d'un utilisateur de test
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "role": "candidate"
    }
    
    auth_service.create_user(
        db=db_session,
        email=user_data["email"],
        password=user_data["password"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        role=user_data["role"]
    )
    
    # Test d'authentification réussie
    authenticated_user = auth_service.authenticate_user(
        db=db_session,
        email=user_data["email"],
        password=user_data["password"]
    )
    assert authenticated_user is not False
    assert isinstance(authenticated_user, User)
    
    # Test d'authentification échouée
    failed_auth = auth_service.authenticate_user(
        db=db_session,
        email=user_data["email"],
        password="wrongpassword"
    )
    assert failed_auth is False 