# LXP-Boston Project Backend

## Description
Backend de l'application LXP-Boston, développé avec FastAPI et PostgreSQL.

## Installation

1. **Cloner le repository**
```bash
git clone https://github.com/theoMich19/LXP-Boston-project-back.git
cd LXP-Boston-project-back
```

2. **Créer et activer l'environnement virtuel**
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

## Installation avec Docker

1. **Setup complet avec Docker**
```bash
make docker-dev-setup
```

Cette commande va :
- Construire les images Docker
- Démarrer les services
- Configurer la base de données

Les services seront accessibles sur :
- API : `http://localhost:8000`
- Documentation : `http://localhost:8000/docs`
- Base de données : `localhost:5432`

2. **Autres commandes Docker utiles**
```bash
make docker-build    # Construire les images
make docker-up      # Démarrer les services
make docker-down    # Arrêter les services
make docker-logs    # Voir les logs
make docker-restart # Redémarrer les services
make docker-clean   # Nettoyer l'environnement Docker
```

## Lancer l'application

1. **Démarrer le serveur de développement**
```bash
uvicorn app.main:app --reload
```

L'application sera accessible à l'adresse : `http://localhost:8000`

2. **Documentation API**
- Swagger UI : `http://localhost:8000/docs`

## Tests Unitaires

### Lancer les tests

1. **Lancer tous les tests**
```bash
pytest tests/services/ -v
```

2. **Lancer les tests d'un service spécifique**
```bash
# Exemple pour les tests d'authentification
pytest tests/services/test_auth_service.py -v
```

3. **Lancer les tests avec couverture**
```bash
pytest --cov=app/services tests/services/
```

### Structure des tests
- Les tests sont organisés dans le dossier `tests/services/`
- Chaque service a son propre fichier de test (ex: `test_auth_service.py`)
- Les tests utilisent des mocks pour simuler la base de données