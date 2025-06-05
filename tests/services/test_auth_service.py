import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from app.services.auth_service import AuthService
from app.db.model import User
import uuid


@pytest.fixture(scope="function")
def mock_db():
    return Mock()


@pytest.fixture(scope="function")
def auth_service():
    return AuthService()


def test_verify_password(auth_service):
    # Test de vérification de mot de passe
    password = "testpassword123"
    hashed_password = auth_service.get_password_hash(password)
    assert auth_service.verify_password(password, hashed_password) is True
    assert auth_service.verify_password("wrongpassword", hashed_password) is False


def test_create_access_token(auth_service):
    # Test de création de token
    data = {"sub": "test@example.com"}
    expires_delta = timedelta(minutes=15)
    token = auth_service.create_access_token(data, expires_delta)
    assert token is not None
    assert isinstance(token, str)


def test_create_user(auth_service, mock_db):
    # Test de création d'utilisateur
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "role": "candidate"
    }

    # Mock de la méthode get_user_by_email pour simuler qu'aucun utilisateur n'existe
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Mock de la méthode add et commit
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()

    # Création d'un utilisateur mock
    mock_user = User(
        id=uuid.uuid4(),
        email=user_data["email"],
        password_hash=auth_service.get_password_hash(user_data["password"]),
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        role=user_data["role"],
        is_active=True
    )

    # Mock de la méthode refresh pour retourner l'utilisateur mock
    mock_db.refresh.side_effect = lambda user: setattr(user, 'id', mock_user.id)

    user = auth_service.create_user(
        db=mock_db,
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
    assert user.is_active is True

    # Vérification que les méthodes mock ont été appelées
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

    # Test de création d'utilisateur avec email existant
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    with pytest.raises(Exception):
        auth_service.create_user(
            db=mock_db,
            email=user_data["email"],
            password=user_data["password"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            role=user_data["role"]
        )


def test_authenticate_user(auth_service, mock_db):
    # Création d'un utilisateur mock
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "role": "candidate"
    }

    mock_user = User(
        id=uuid.uuid4(),
        email=user_data["email"],
        password_hash=auth_service.get_password_hash(user_data["password"]),
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        role=user_data["role"],
        is_active=True
    )

    # Mock de la méthode query pour retourner l'utilisateur mock
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    # Test d'authentification réussie
    authenticated_user = auth_service.authenticate_user(
        db=mock_db,
        email=user_data["email"],
        password=user_data["password"]
    )
    assert authenticated_user is not None
    assert authenticated_user.email == user_data["email"]

    # Test d'authentification échouée
    assert auth_service.authenticate_user(
        db=mock_db,
        email=user_data["email"],
        password="wrongpassword"
    ) is False
